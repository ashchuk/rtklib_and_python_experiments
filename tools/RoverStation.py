import requests
import serial
import logging
import sys, os

from time import sleep, time
from requests.exceptions import Timeout, ConnectionError

logging.basicConfig(filename='gpsserver.log', filemode='w', format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)
# open serial
ser = serial.Serial('/dev/ttyACM0', 115200, parity=serial.PARITY_ODD)

BAD_REQUEST = False
count = 0

import serial
from time import sleep
#ser = serial.Serial('/dev/ttyACM0', 115200, parity=serial.PARITY_NONE)
ser = serial.Serial('/dev/ttyACM0', 115200, parity=serial.PARITY_NONE)
ser.write(b'$PORZB*55\r\n') #- to stop
sleep(0.5)
ser.write(b'$PORZB*55\r\n') #- to stop
sleep(0.5)
ser.write(b'$PORZB*55\r\n') #- to stop
sleep(0.5)
ser.write(b'$PORZB*55\r\n') #- to stop
sleep(0.5)
ser.write(b'$PORZB*55\r\n') #- to stop

ser.write(b'$PORZA,1,115200,3*7F\r\n') #- to start BINR
sleep(0.5)
ser.write(b'$PORZA,1,115200,3*7F\r\n') #- to start BINR
sleep(0.5)
ser.write(b'$PORZA,1,115200,3*7F\r\n') #- to start BINR
sleep(0.5)
ser.write(b'$PORZA,1,115200,3*7F\r\n') #- to start BINR
sleep(0.5)
ser.write(b'$PORZA,1,115200,3*7F\r\n') #- to start BINR

ser.close()
#ser = serial.Serial('/dev/ttyUSB0', 115200, parity=serial.PARITY_ODD) #- change ser to read BINR format
ser = serial.Serial('/dev/ttyACM0', 115200, parity=serial.PARITY_ODD, timeout=1) #- change ser to read BINR format

ser.flushInput()

ser.write('\x10\xF4\x0A\x10\x03\\r\\n') #- to start BINR transfering
sleep(0.5)
ser.write('\x10\xF4\x0A\x10\x03\\r\\n') #- to start BINR transfering
sleep(0.5)
ser.write('\x10\xF4\x0A\x10\x03\\r\\n') #- to start BINR transfering
sleep(0.5)
ser.write('\x10\xF4\x0A\x10\x03\\r\\n') #- to start BINR transfering
sleep(0.5)
ser.write('\x10\xF4\x0A\x10\x03\\r\\n') #- to start BINR transfering


print('Begin transfering')
while True:
	sleep(0.5)	
	bytesToRead = ser.inWaiting()
	data = ser.read(bytesToRead)
	logging.debug('~~~~~~~~ data begin ~~~~~~~~~~~')
	logging.debug('Received data: %s ' % str(len(data)))
	logging.debug('~~~~~~~~~ data end ~~~~~~~~~~~~')
	if data:
		logging.debug('Data is not null')
		with open("base.dat", "ab") as dataStorage:
			logging.debug('Base size: %s' % str(os.stat("base.dat").st_size))
			dataStorage.write(data)
		try:
			if BAD_REQUEST:
				with open("temp_storage.dat", "rb+") as tempStorage:
					logging.debug('~~~~~~~~ BAD_REQUEST ~~~~~~~~~~~')
					tempStorage.seek(0)
					dataToSend = tempStorage.read()+data
					message = {"length": str(len(dataToSend)), "time":str(time()).ljust(13, '0')}
					binaryData = {'data': dataToSend}
					logging.debug('tempStorage data: %s ' % str(len(dataToSend)))
					tempStorage.seek(0)
					tempStorage.truncate()
					BAD_REQUEST = False
			else:
				dataToSend = data
				message = {"length": str(len(dataToSend)), "time":str(time()).ljust(13, '0')}
				binaryData = {'data': dataToSend}
			r = requests.post('http://gps-ashchuk.rhcloud.com/secondwrite', stream=True, timeout=None, files=binaryData, data = message)
			if r.status_code == 200:
				count += 1
				#logging.debug('Success! Data: %s' % r.text) # for Debugging
			else:
				BAD_REQUEST = True
				with open("temp_storage.dat", "ab") as tempStorage:
					tempStorage.write(dataToSend)
		except (Timeout, ConnectionError) as e:
			logging.info(u'~~~~~~~~~~~~~~~~~Got Timeout or ConnectionError~~~~~~~~~~~~~')
			logging.info(e)
			logging.info(u'\n~~~~~~~~~~~~~~~~~~~~~~###############~~~~~~~~~~~~~~~~~~~~~~~~~')
			BAD_REQUEST = True
			with open("temp_storage.dat", "ab") as tempStorage:
				tempStorage.write(dataToSend)
			continue
