#!/usr/bin/env python
import tornado.web
import os
import pymongo

from bson import Binary
from bson import json_util
from time import sleep, time
from pymongo import MongoClient

import logging
import subprocess
import multiprocessing
__UPLOADS__ = str(os.environ.get('OPENSHIFT_DATA_DIR'))
__STATIC__ = str(os.environ.get('OPENSHIFT_DATA_DIR'))+"../repo/wsgi/"

logging.basicConfig(filename=__UPLOADS__+'postprocessing.log', filemode='w', format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.ERROR)


def filemaker():
    with open(__UPLOADS__ + '/somefile.txt', 'w') as f:
        f.write(str(time()).ljust(13, '0'))

FIRST_REQUEST = 'first_request'
DEFAULT_REQUEST = 'default'

class BaseHandler(tornado.web.RequestHandler):
    MONGODB_DB_URL = os.environ.get('OPENSHIFT_MONGODB_DB_URL') if os.environ.get('OPENSHIFT_MONGODB_DB_URL') else 'mongodb://localhost:27017/'
    MONGODB_DB_NAME = os.environ.get('OPENSHIFT_APP_NAME') if os.environ.get('OPENSHIFT_APP_NAME') else 'gps'
    client = MongoClient(MONGODB_DB_URL)
    db = client[MONGODB_DB_NAME]

    def clearTemp(self, stream):
        stream.drop()

def postprocessing():
    MONGODB_DB_URL = os.environ.get('OPENSHIFT_MONGODB_DB_URL') if os.environ.get('OPENSHIFT_MONGODB_DB_URL') else 'mongodb://localhost:27017/'
    MONGODB_DB_NAME = os.environ.get('OPENSHIFT_APP_NAME') if os.environ.get('OPENSHIFT_APP_NAME') else 'gps'
    client = MongoClient(MONGODB_DB_URL)
    db = client[MONGODB_DB_NAME]
    base_station = b''
    rover_station =b''
    try:
        with open(__STATIC__+'tools/tbase.dat', 'wb') as tbase:
            cursor = db.FirstStream.find()
            if cursor.count() == 0:
                print('FirstStreamTemp cursor.count() == 0!')
                #sleep(5)
                return
                #continue
            else:
                for item in cursor:
                    base_station += item['data']
            tbase.write(base_station)
        with open(__STATIC__+'tools/trover.dat', 'wb') as trover:
            cursor = db.SecondStreamTemp.find()
            if cursor.count() == 0:
                print('SecondStreamTemp cursor.count() == 0!')
                #sleep(5)
                return
                #continue
            else:
                for item in cursor:
                    rover_station += item['data']
            trover.write(rover_station)
        process = subprocess.call([__UPLOADS__+'/RTKLIB/app/convbin/gcc/convbin', __STATIC__+'tools/tbase.dat', '-r', 'nvs'])#, stdout=subprocess.PIPE)
        process = subprocess.call([__UPLOADS__+'/RTKLIB/app/convbin/gcc/convbin', __STATIC__+'tools/trover.dat', '-r', 'nvs'])#, stdout=subprocess.PIPE)
        process = subprocess.call([__UPLOADS__+'/RTKLIB/app/rnx2rtkp/gcc/rnx2rtkp', '-k',__UPLOADS__+'/RTKLIB/app/rnx2rtkp/gcc/opts2.txt', '-o', __UPLOADS__+'tpos.pos', __STATIC__+'tools/trover.obs',__STATIC__+'tools/tbase.nav',__STATIC__+'tools/tbase.obs'])#, stdout=subprocess.PIPE)
        with open(__UPLOADS__+'tpos.pos', 'r') as f:
            datalist = [list(filter(None, line.split(' '))) for line in f if line[0].rstrip() != '%']
            for item in datalist:
                coords = {'date': item[0],
                              'time': item[1],
                              'lat': item[2],
                              'lng': item[3],
                              'height': item[4],
                              'quality': item[5],
                              'satellites': item[6]
                              }
                db.Coords.insert(coords)
        with open(__UPLOADS__+'tpos.pos', 'r') as f:
            with open(__UPLOADS__+'sol.pos', 'a+') as t:
                t.write('New appending!\nCalculation time: %s \n' % str(time()).ljust(13, '0'))
                for line in f:
                    t.write(line)
            #Clear temp files
        with open(__UPLOADS__+'tpos.pos', 'rb+') as f:
            f.seek(0)
            f.truncate()
        with open(__STATIC__+'tools/tbase.dat', 'rb+') as f:
            f.seek(0)
            f.truncate()
        with open(__STATIC__+'tools/trover.dat', 'rb+') as f:
            f.seek(0)
            f.truncate()
        #db.FirstStreamTemp.drop()
        db.SecondStreamTemp.drop()
        #break
    except Exception as e:
        logging.debug('Exception')
        logging.debug(str(e))
        return


class MainHandler(BaseHandler):
    def get(self): 
        #self.clearTemp(self.db.FirstStream)
        #self.clearTemp(self.db.SecondStream)
        #self.clearTemp(self.db.ThirdStream)
        '''temp = ''
        process = subprocess.call([__UPLOADS__+'/RTKLIB/app/convbin/gcc/convbin', __STATIC__+'tools/base.dat', '-r', 'nvs'])#, stdout=subprocess.PIPE)
        process = subprocess.call([__UPLOADS__+'/RTKLIB/app/convbin/gcc/convbin', __STATIC__+'tools/rover.dat', '-r', 'nvs'])#, stdout=subprocess.PIPE)
        filename = str(time()).ljust(13, '0')+'.pos'
        process = subprocess.call(['touch', __UPLOADS__+filename])
        #process = subprocess.Popen(['sh', __UPLOADS__+'rnx.sh'])#, '-o', __UPLOADS__+'sol.pos', __STATIC__+'tools/rover.obs',__STATIC__+'tools/base.nav',__STATIC__+'tools/base.obs'])#, stdout=subprocess.PIPE)
        process = subprocess.call([__UPLOADS__+'/RTKLIB/app/rnx2rtkp/gcc/rnx2rtkp', '-k',__UPLOADS__+'/RTKLIB/app/rnx2rtkp/gcc/opts2.txt', '-o', __UPLOADS__+filename, __STATIC__+'tools/rover.obs',__STATIC__+'tools/base.nav',__STATIC__+'tools/base.obs'], stdout=subprocess.PIPE)
        #process = subprocess.Popen('~/app-root/data/RTKLIB/app/rnx2rtkp/gcc/rnx2rtkp -k ~/app-root/data/RTKLIB/app/rnx2rtkp/gcc/opts2.conf -o ~/app-root/data/RTKLIB/app/rnx2rtkp/gcc/sol.pos ~/app-root/repo/wsgi/tools/rover.obs ~/app-root/repo/wsgi/tools/base.nav ~/app-root/repo/wsgi/tools/base.obs')
        #sleep(20)
        testp = multiprocessing.Process(target=filemaker)
        testp.start()
        with open(__UPLOADS__+filename, 'r') as f:
            datalist = [list(filter(None, line.split(' '))) for line in f if line[0].rstrip() != '%']
            temp += '<h1>' + filename + '</h1> </br>'
            #temp += '<p> Date: ' + s[0] + ' Time: ' + s[1] + ' Coords: lat/long/h ' + s[2]+' '+s[3]+ ' '+ s[4] + ' Quality: ' + s[5] + '</p>'
            size = len(datalist)
            temp += 'Data len == ' + str(size)
            for item in datalist:
                temp += '<p> Date: ' + item[0] + ' Time: ' + item[1] + ' Coords: lat/long/h ' + item[2]+' '+item[3]+ ' '+ item[4] + ' Quality: ' + item[5] + '</p>'
        self.write(temp)
        '''
        #testp = multiprocessing.Process(target=postprocessing)
        #testp.start()
        postprocessing()
        self.write(b'Maked postprocessing in GPS project')

    def post(self): 
        self.write(b'MainHandler in GPS project')

class MapHandler(BaseHandler):
    def get(self):
        self.render('maptest.html')

    def post(self):
        coords = {}
        index = 0
        postprocessing()
        cursor = self.db.Coords.find().sort([('quality', pymongo.DESCENDING)])[0:9]
        if cursor.count() == 0:
            coords.update({'message': 'Coordinates are not available yet'})
        else:
            #coords.update({'message': 'Coordinates are available'})
            for item in cursor:
                coords.update({index: item})
                index += 1
        self.write(json_util.dumps(coords, default=json_util.default)) 
        #self.db.Coords.drop() # Clear temp storage

class FirstStreamWriteHandler(BaseHandler):
    def get(self):
        self.write("FirstStreamWriteHandler page")
        
    def post(self):
        data_length = self.get_argument("length")
        get_time = self.get_argument("time")
        #print('time and length: ', get_time, data_length)
        files = self.request.files
        binaryData = files['data'][0]['body']
        #print('binaryData: ', binaryData)
        data = {"time":str(get_time), "data": binaryData, 'length': data_length}
        self.db.FirstStream.insert(data)
        #self.db.FirstStreamTemp.insert(data)
        status = ""
        status +=  "Received time: " + str(data["time"]) + '\n'
        status +=  "Received data: " + str(data["data"]) + '\n'
        status +=  "Received data length: " + str(data["length"]) + '\n'
        self.write(status)

class SecondStreamWriteHandler(BaseHandler):
    def get(self):
        self.write("SecondStreamWriteHandler page")
        
    def post(self):
        data_length = self.get_argument("length")
        get_time = self.get_argument("time")
        files = self.request.files
        binaryData = files['data'][0]['body']
        
        data = {"time":str(get_time), "data": binaryData, 'length': data_length}
        self.db.SecondStream.insert(data)
        self.db.SecondStreamTemp.insert(data)
        status = ""
        status +=  "Received time: " + str(data["time"]) + '\n'
        status +=  "Received data: " + str(data["data"]) + '\n'
        status +=  "Received data length: " + str(data["length"]) + '\n'
        self.write(status)

class ThirdStreamWriteHandler(BaseHandler):
    def get(self):
        self.write("ThirdStreamWriteHandler page")
        
    def post(self):
        data_length = self.get_argument("length")
        get_time = self.get_argument("time")
        files = self.request.files
        binaryData = files['data'][0]['body']
        
        data = {"time":str(get_time), "data": binaryData, 'length': data_length}
        self.db.ThirdStream.insert(data)
        status = ""
        status +=  "Received time: " + str(data["time"]) + '\n'
        status +=  "Received data: " + str(data["data"]) + '\n'
        status +=  "Received data length: " + str(data["length"]) + '\n'
        self.write(status)


class FirstStreamReadHandler(BaseHandler):
    def get(self):
        self.write("FirstStreamReadHandler page")

    def post(self):
        request_status = self.get_argument("request")
        base_station = b''
        if request_status == FIRST_REQUEST:
            cursor = self.db.FirstStream.find()
            if cursor.count() == 0:
                print('FirstStream cursor.count() == 0!')
                time = get_time
            for item in cursor:
                base_station += item['data']
                time = item['time']
            dataToSend = base_station
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            print('BASE STATION SIZE: %s' % len(dataToSend))
            response = {"data": Binary(dataToSend), "length": len(dataToSend), 'time': time}
            self.write(json_util.dumps(response, default=json_util.default))
        elif request_status == DEFAULT_REQUEST:
            get_time = self.get_argument("time")
            cursor = self.db.FirstStream.find({'time': { '$gt': get_time }}).sort([('time', pymongo.ASCENDING)])
            if cursor.count() == 0:
                print('FirstStream cursor.count() == 0!')
                time = get_time
            for item in cursor: 
                base_station += item['data']
                time = item['time']
            dataToSend = base_station
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            response = {"data": Binary(dataToSend), "length": len(dataToSend), 'time': time}
            self.write(json_util.dumps(response, default=json_util.default))

class FirstStreamRawReadHandler(BaseHandler):
    def get(self):
        one = self.db.FirstStream.find().sort([('time', pymongo.DESCENDING)])[0]
        self.write(one['time'])

    def post(self):
        request_status = self.get_argument("request")
        base_station = b''

        if request_status == FIRST_REQUEST:
            cursor = self.db.FirstStream.find()
            if cursor.count() == 0:
                print('FirstStreamRawReadHandler cursor.count() == 0!')
                time = get_time
            for item in cursor:
                base_station += item['data']
                time = item['time']
            dataToSend = base_station
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            print('BASE STATION SIZE: %s' % len(dataToSend))
            self.write(dataToSend)

        elif request_status == DEFAULT_REQUEST:
            get_time = self.get_argument("time")
            cursor = self.db.FirstStream.find({'time': { '$gt': get_time }}).sort([('time', pymongo.ASCENDING)])
            print('FirstStreamRawReadHandler cursor.count() == %s' % cursor.count())
            if cursor.count() == 0:
                print('cursor.count() == 0!')
                time = get_time
            for item in cursor:
                base_station += item['data']
                time = item['time']
            dataToSend = base_station
            print('Data len == %s' % len(dataToSend))
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            self.write(dataToSend)

class SecondStreamReadHandler(BaseHandler):
    def get(self):
        self.write("SecondStreamReadHandler page")

    def post(self):
        request_status = self.get_argument("request")
        rover_station = b''
        if request_status == FIRST_REQUEST:
            cursor = self.db.SecondStream.find()
            if cursor.count() == 0:
                print('SecondStream cursor.count() == 0!')
                time = get_time
            for item in cursor:
                rover_station += item['data']
                time = item['time']
            dataToSend = rover_station
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            print('ROVER STATION SIZE: %s' % len(dataToSend))
            response = {"data": Binary(dataToSend), "length": len(dataToSend), 'time': time}
            self.write(json_util.dumps(response, default=json_util.default))

        elif request_status == DEFAULT_REQUEST:
            get_time = self.get_argument("time")
            cursor = self.db.SecondStream.find({'time': { '$gt': get_time }}).sort([('time', pymongo.ASCENDING)])
            if cursor.count() == 0:
                print('SecondStream cursor.count() == 0!')
                time = get_time
            for item in cursor:
                rover_station += item['data']
                time = item['time']
            dataToSend = rover_station
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            response = {"data": Binary(dataToSend), "length": len(dataToSend), 'time': time}
            self.write(json_util.dumps(response, default=json_util.default))

class ThirdStreamReadHandler(BaseHandler):
    def get(self):
        self.write("ThirdStreamReadHandler page")

    def post(self):
        request_status = self.get_argument("request")
        corr_station = b''
        if request_status == FIRST_REQUEST:
            cursor = self.db.ThirdStream.find()
            if cursor.count() == 0:
                print('ThirdStream cursor.count() == 0!')
                time = get_time
            for item in cursor:
                rocc_station += item['data']
                time = item['time']
            dataToSend = corr_station
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            print('CORR STATION SIZE: %s' % len(dataToSend))
            response = {"data": Binary(dataToSend), "length": len(dataToSend), 'time': time}
            self.write(json_util.dumps(response, default=json_util.default))

        elif request_status == DEFAULT_REQUEST:
            get_time = self.get_argument("time")
            cursor = self.db.ThirdStream.find({'time': { '$gt': get_time }}).sort([('time', pymongo.ASCENDING)])
            if cursor.count() == 0:
                print('ThirdStream cursor.count() == 0!')
                time = get_time
            for item in cursor:
                corr_station += item['data']
                time = item['time']
            dataToSend = corr_station
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('content-encoding', 'none')
            response = {"data": Binary(dataToSend), "length": len(dataToSend), 'time': time}
            self.write(json_util.dumps(response, default=json_util.default))

handlers = [(r'/', MainHandler),
            (r'/firstraw', FirstStreamRawReadHandler), (r'/map', MapHandler),
            (r'/firstwrite', FirstStreamWriteHandler), (r'/secondwrite',SecondStreamWriteHandler), (r'/thirdwrite',ThirdStreamWriteHandler),
            (r'/firstread', FirstStreamReadHandler), (r'/secondread',SecondStreamReadHandler), (r'/thirdread',ThirdStreamReadHandler),]
