# OGC.Engineering
### mqtt-host-client - demo applications to develop and test OGC mqtt interface
developer contact - dustin ( at ) ogc.engineering

---

## Install requirements and run demo
* acquire sources
```
git clone git@github.com:kz5ee/mqtt-host-client.git
git submodule update --init
```
* install and start a MQTT broker
```
sudo apt install mosquitto
```
* install python and required packages ( incomplete, untested list )
```
sudo apt install python3, python3-paho
```
* In one terminal, run the host application to start generating host/server side heartbeats
```
cd host
./ogc-network-host-application.py
```
* In a second terminal, run the client application to start generating client/device side heartbeats
```
cd client
./ogc-network-client-application.py
```
* run multipl clients to see broadcasts across the network but responses only to individual clients

## Expected operation
* host side application broadcasts heartbeats on /network/broadcasts topic for clients to track server health
* client side application broadcasts heartbeats on /network/broadcasts topic for host to find and respond to on client specific topic
