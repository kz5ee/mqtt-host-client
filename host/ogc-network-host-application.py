#!/bin/python3

# OGC.Engineering
# MQTT device server
# tracking and management of OGC devices over a private network

import os
import platform
import time
import json
import paho.mqtt.client as paho
import sys
import ogc_python_tools.ogc_python_logging as l

broker = "localhost"  # change to target if another broker server is being used
hostname = os.uname()[ 1 ]  # this is one of many ways to get the devices hostname


# ------------------------------------------------------------------------------
# Table driven message logic
# TODO: move into a dedicated shared header so host and client can use the same logic
# ------------------------------------------------------------------------------
# Commonly placed elements, zero-indexing starting at zero
MSG_TYPE = 0       # first element is message type to determine how to process
MSG_ID = 1         # second element is message ID to track data through requests and responses
MSG_DATA_TYPE = 2  # third element if data type to be passed to processing callback

# Discovery message intended to be used to query the network for information
#
# Expected response is a series of get/set messages with data associated with discovery query
#
#    msg_type      - common first element for ease of processing, holds "disco" string
#    msg_id        - positive random 32 bit tracking ID in case it is needed, 0 otherwise
#    source        - source device name so data can be returned appropriately since this is a broadcast
#    data_type     - data type being requested ( think category that sets how data is processed )
#    value         - ( optional ) value ( think subcategory value or structure )
#
msg_elements__disco = [ "msg_type", "msg_id", "data_type", "source", "value" ]

# Status message intended to be a heartbeat and update the network about individual device status
#
# Expected response is an acknowledgement that may contain additional configuration information
#     this ACK message can probably use the SET message with a ack data_type, config register, and value sub structure
#
#    msg_type      - common first element for eas of processing, holds "stat" string
#    msg_id        - positive random 32 bit tracking ID in case it is needed, 0 otherwise
#    data_type     - server, device, router, ... etc.
#    device_name   - unique name for tracking and direct messaging
#    device_group  - group the device belongs to for group broadcasts
#    device_uptime - seconds of operation
#    device_status - value or substructure that could be a simple "good", a percentage, or a sub structure with battery, temperature, etc
#
msg_elements__stat  = [ "msg_type", "msg_id", "data_type", "device_name", "device_group", "device_uptime", "device_status" ]

# Get message
#
# Expected response is likely a SET message with the associated data being requested
#
#    msg_type      - common first element for eas of processing, holds "get" string
#    msg_id        - positive random 32 bit tracking ID in case it is needed, 0 otherwise
#    data_type     - data type being requested ( think category that sets how data is processed )
#    value         - ( optional ) value ( think subcategory value or structure )
#
msg_elements__get   = [ "msg_type", "msg_id", "data_type", "value" ]

# Set message
#
# Expected response is likely a set message with an ACK data_type
#
#    msg_type      - common first element for eas of processing, holds "set" string
#    msg_id        - positive random 32 bit tracking ID in case it is needed, 0 otherwise
#    data_type     - data type being set ( think category that sets how the data is processed )
#    value         - ( optional ) value ( think subcategory value or structure )
#
msg_elements__set   = [ "msg_type", "msg_id", "data_type", "value" ]
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# message_table is the structure that holds all messages and associated processing elements
# ------------------------------------------------------------------------------
# callbacks for processing
def callback_disco( type, id, obj ):
    l.log( l.DEBUG, "DISCO(%s)(%s)(%s)" % ( type, id, obj ) )

def callback_stat( type, id, obj ):
    if ( ( type == "client" ) and ( obj[ "device_name" ] != hostname ) ):
        rbuffer = "{\"msg_type\":\"set\",\"msg_id\":%u,\"data_type\":\"response\",\"value\":\"ack\"}" % ( obj[ "msg_id" ] ) # generate message
        topic = "/device/%s" % ( obj[ "device_name" ] )  # generate topic
        client.publish( topic, rbuffer )  # response message
        # TODO: further processing ofststus heartbeats
    elif ( ( type == "server" ) and ( obj[ "device_name" ] != hostname ) ):
        rbuffer = "{\"msg_type\":\"set\",\"msg_id\":%u,\"data_type\":\"response\",\"value\":\"ack\"}" % ( obj[ "msg_id" ] ) # generate message
        topic = "/device/%s" % ( obj[ "device_name" ] )  # generate topic
        client.publish( topic, rbuffer )  # response message
        # TODO: further processing ofststus heartbeats
    elif ( ( type == "server" ) and ( obj[ "device_name" ] == hostname ) ):
        l.log( l.DEBUG, "Self status verified" )
    else:
        l.log( l.DEBUG, "STAT(%s)(%s)(%s)" % ( type, id, obj ) )

def callback_get( type, id, obj ):
    l.log( l.DEBUG, "GET(%s)(%s)(%s)" % ( type, id, obj ) )

def callback_set( type, id, obj ):
    l.log( l.DEBUG, "SET(%s)(%s)(%s)" % ( type, id, obj ) )


TABLE_MSG_TYPE = 0
TABLE_CALLBACK = 1

msg_table = [
    { "msg_type":"disco", "callback":callback_disco },
    { "msg_type":"stat", "callback":callback_stat },
    { "msg_type":"get", "callback":callback_get },
    { "msg_type":"set", "callback":callback_set }
]

def on_message( client, userdata, message ):
#    print( "received message = (%s)" % ( str( message.payload.decode( "utf-8" ) ) ) )
    try:
        msg = json.loads( str( message.payload.decode( "utf-8" ) ) )  # extract json into object
#        l.log( l.DEBUG, str( msg ) )
        for entry in msg_table:
            if( entry[ "msg_type" ] == msg[ "msg_type" ] ):
                entry[ "callback" ]( msg[ "data_type" ], msg[ "msg_id" ], msg )
                break  # finish processing this message
    except Exception as e:
        l.log( l.ERROR, "ERROR: message rcv (%s)" % ( e ) )


if __name__ == "__main__":
    # TODO: add command line arguments

    # ogc_python_logging
    l.verbosity_override_set( True )
    l.log_file_set( "test.log" )
    l.storage_use_set( False ) # set to true or give option to when the TUI is in operation

    l.log( l.INFO, "--------------------------------------------------------------------------------" )
    l.log( l.INFO, "OGC.Engineering - ogc-network-mqtt-host-application.py" )
    l.log( l.INFO, "--------------------------------------------------------------------------------" )

    # TODO: create a unique name for this client for use in client creation
    client = paho.Client( "client-server" )

    # bind function to callback
    client.on_message = on_message

    l.log( l.DEBUG, "connecting to broker (%s)" % ( broker ) )
    client.connect( broker )  # connect
    client.loop_start()  # start loop to process received messages

    l.log( l.DEBUG, "subscribing" )
    # network level subscriptions
    client.subscribe( "/network/broadcasts/#" )
    # group level subscriptions
    #client.subscribe( "/group/servers/#" )
    # system level subscriptions
    # device level descriptions
    client.subscribe( "/device/%s/#" % ( hostname ) )

    time.sleep( 2 )

    l.log( l.DEBUG, "publishing " )

    while True:
        # Periodic TICK/Heartbeat
        buffer = "{\"msg_type\":\"stat\",\"msg_id\":0,\"data_type\":\"server\",\"device_name\":\"%s\",\"device_group\":\"demo\",\"device_uptime\":\"%s\",\"device_status\":\"OK\"}" % ( hostname, time.monotonic() )
        client.publish( "/network/broadcasts", buffer )
        time.sleep( 60 )  # repeat every minute
    client.disconnect()  # disconnect
    client.loop_stop()  # stop loop

