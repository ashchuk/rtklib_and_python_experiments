# RTKLib and Python experiments

There is pilot project what uses RTKLib postprocessing, Google Maps JS API and Python. Tested on Ubuntu 14.04.
Used NV08C-CSM receiver and NVS BINR raw data format.

### What used?

Server:
  - OpenShift Tornado (Python 3.3)
  - MongoDB 2.4
  - RockMongo 1.1 (used for debug)

Client:
  - Python Requests
  - PySerial (NVS BINR setup and data reading)
  - Python Socket (to connect with rtkrcv)
  - Python Multiprocessing

### Tools 

  - BaseStation.py/RoverStation.py - script used to read raw navdata from NVS receiver (NVS BINR out format), save received data to local storage and send data chunks to server.
  - httpreading.py - the bridge between Server and started rtkrcv process. It open sockets and send raw data from server to appropriate rtkrcv stream (base/rover/correction)

### Server functions

Server has two modes: 
  - Used clearly as storage+receiver. Just get data from base/rover, save it in DB and send it to httpreading.py process.
  - Postprocessing mode. Using working only with available base and rover stations. To use this mode just go to https://your_url/map, it will return Google Map page with 10 markers plased in last calculated rover positions.
 


