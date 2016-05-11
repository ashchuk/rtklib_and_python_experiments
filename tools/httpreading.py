import requests
import serial
import logging
import sys, errno
import multiprocessing
import logging
import socket
from requests.exceptions import Timeout, ConnectionError, RequestException
from bson.json_util import loads
from time import sleep


def httpRequestProcess(stream, logfile, q):
	logging.basicConfig(filename=logfile, filemode='w', format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)
	FIRST_REQUEST = 'first_request'
	DEFAULT_REQUEST = 'default'

	FIRST_CONNECTION = True
	index = 0
	while True:
		sleep(1)
		try:
			if FIRST_CONNECTION:
				logging.debug('FIRST_CONNECTION')
				r = requests.post(stream, stream=True, timeout=None, data={"request": FIRST_REQUEST})
				if r.status_code == 200:

					index+=1
					FIRST_CONNECTION = False
					logging.debug('FIRST_REQUEST. status_code: ' + str(r.status_code))
					resp = loads(r.content)
					current_time = resp['time']
					logging.debug('current_time %s' % current_time)
					logging.debug("Index: " + str(index) + " Length received: " + str(len(resp['data'])) + " Length from response: " + str(resp['length']) + '\n')
					received_data = bytes(resp['data'])
				else:
					logging.debug(str(r.status_code) + '   ' + str(r.text))
					continue
			else:
				logging.debug('DEFAULT_CONNECTION')
				r = requests.post(stream, stream=True, timeout=5, data={"request": DEFAULT_REQUEST, 'time': current_time})
				if r.status_code == 200:
					index+=1
					logging.debug('status_code: ' + str(r.status_code))
					resp = loads(r.content)
					current_time = resp['time']
					logging.debug('current_time %s' % current_time)
					logging.debug("Index: " + str(index) +" Length received: " + str(len(resp['data'])) + " Length from response: " + str(resp['length']) + '\n')
					received_data = bytes(resp['data'])
				else:
					logging.debug(str(r.status_code) +  str(r.text))
					continue
			logging.debug('Received message size. q.put == ' + str(len(received_data)))
			if len(received_data) > 0:
				q.put(received_data)
		except requests.exceptions.Timeout as te:
			sleep(10) # Wait 10 sec and try again
			logging.error('~~~~~~~~~~Timeout exception~~~~~~`')
			logging.error(te)
			continue
		except ConnectionError as ce:
			logging.error('~~~~~~~~~~ConnectionError exception~~~~~~`')
			logging.error(ce)
			continue
		except RequestException as re:
			logging.error('~~~~~~~~~~Other request exception~~~~~~`')
			logging.error(re)
			continue


def serialProcess(device, q):
	logging.basicConfig(filename="serialProcess.txt", filemode='w', format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)
	logging.debug('serialProcess started')
	try:
		ser = serial.Serial(device, 115200, timeout=1, parity=serial.PARITY_ODD)
		while True:
			try:
				bytesToRead = ser.inWaiting()
				data = ser.read(bytesToRead)
			except serial.SerialTimeoutException as tout:
				logging.error('~~~~~~~~~~SerialTimeoutException~~~~~~~~~~`')
				logging.error(tout)
				sleep(10)
				continue
	except serial.SerialException as e:
		logging.error('~~~~~~~~~~SerialException~~~~~~~~~~`')
		logging.error(e)
	

def socketProcess(q, host, port, filename):
	sended = True
	logging.basicConfig(filename="socketProcess.txt", filemode='w', format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)
	logging.debug('socketProcess started')
	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# Bind the socket to the port
	server_address = (host, port)
	logging.debug('starting up on %s port %s' % server_address)
	sock.bind(server_address)
	sock.listen(1)

	while True:
		# Wait for a connection
		logging.debug('Waiting for a connection...')
		connection, client_address = sock.accept()
		try:
			print >>sys.stderr, 'Connection from: ', client_address
			# Receive the data in small chunks and retransmit it
			while True:
				if sended:
					sended = False
					data = q.get()
				while True:
					if data:
						print('Try to send %s bytes to socket...' % str(len(data)))
						connection.send(data)
						print('Success! Sended data: ' + str(len(data)))
						with open(filename, 'wb') as f:
							f.write(data)
						sended = True
						break
					break
		except IOError as e:
			if e.errno == errno.EPIPE:
				print('~~~~~~~~~~~ Broken Pipe error ~~~~~~~~~~~')
				logging.error('~~~~~~~~~~~ Broken Pipe error ~~~~~~~~~~~')
				logging.error(e)
			# Handle error: reopen socket
				connection.close()
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				server_address = (host, port)
				logging.debug('starting up on %s port %s' % server_address)
				sock.bind(server_address)
				sock.listen(1)
				continue
		finally:
			# Clean up the connection
			logging.debug('Connection closed in FINALLY')
			connection.close()

def start_process():

	baseQueue = multiprocessing.Queue()
	roverQueue = multiprocessing.Queue()
	corrQueue = multiprocessing.Queue()
	baseProcess = multiprocessing.Process(target=httpRequestProcess, args=('http://gps-ashchuk.rhcloud.com/firstread', "baseProcess.txt", baseQueue,))	
	#roverProcess = multiprocessing.Process(target=serialProcess, args=('/dev/ttyACM0', roverQueue,))
	corrProcess = multiprocessing.Process(target=httpRequestProcess, args=('http://gps-ashchuk.rhcloud.com/secondread', "corrProcess.txt", corrQueue,))

	baseSocket = multiprocessing.Process(target=socketProcess, args=(baseQueue, 'localhost', 1010, 'base.dat'))
	corrSocket = multiprocessing.Process(target=socketProcess, args=(corrQueue, 'localhost', 2020, 'rover.dat'))

	baseProcess.start()
	#roverProcess.start()
	corrProcess.start()
	baseSocket.start()
	corrSocket.start()
if __name__ == "__main__":
	start_process()
