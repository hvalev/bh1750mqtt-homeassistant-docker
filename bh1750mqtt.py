#!/usr/bin/python3
from datetime import datetime
import time
import os
import csv
import paho.mqtt.client as mqtt
import smbus
import logging
from bh1750 import BH1750

# Begin
bh1750_start_ts = datetime.now()

###############
# MQTT Params
###############
mqtt_topic = os.getenv('topic', 'zigbee2mqtt/')
mqtt_device_id = os.getenv('device_id', 'bh1750')
mqtt_brokeraddr = os.getenv('broker', '192.168.1.10')
mqtt_username = os.getenv('username', None)
mqtt_password = os.getenv('password', None)
if not mqtt_topic.endswith('/'):
    mqtt_topic = mqtt_topic + "/"
mqtt_topic = mqtt_topic + mqtt_device_id + '/'

###############
# GPIO params
###############
# TODO check if we can use the GPIO test https://github.com/kgbplus/gpiotest to autodetect pin
# Problems with multiple sensors on the same device
bh1750_bus = int(os.getenv('bus', '1'))
bh1750_refresh = int(os.getenv('poll', '2'))
bh1750_addr = int(os.getenv('addr', '0x23'), 16)
bh1750_sens = int(os.getenv('sens', '254'))
bh1750_unit = os.getenv('unit', 'lx')
bh1750_mode = int(os.getenv('mode', '1'))

###############
# MQTT & Logging params
###############
bh1750_mqtt_chatter = str(os.getenv('mqtt_chatter', 'essential|ha|full')).lower()
bh1750_logging_mode = str(os.getenv('logging', 'None')).lower()
bh1750_sensor_tally = dict()


###############
# Logging functions
###############
def log2file(filename, params):
    if('log2file' in bh1750_logging_mode):
        ts_filename = bh1750_start_ts.strftime('%Y-%m-%dT%H-%M-%SZ')+'_'+filename+".csv"
        with open("/log/"+ts_filename, "a+") as file:
            w = csv.DictWriter(file, delimiter=',', lineterminator='\n', fieldnames=params.keys())
            if file.tell() == 0:
                w.writeheader()
            w.writerow(params)


def log2stdout(timestamp, msg, type):
    if('log2stdout' in bh1750_logging_mode):
        if type == 'info':
            logging.info(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')+' '+str(msg))
        if type == 'warning':
            logging.warning(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')+' '+str(msg))
        if type == 'error':
            logging.error(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')+' '+str(msg))


###############
# MQTT update functions
###############
def updateEssentialMqtt(illumination):
    if('essential' in bh1750_mqtt_chatter):
        payload = '{ "illuminance": '+str(illumination)+' }'
        client.publish(mqtt_topic + 'value', payload, qos=1, retain=True)
        client.publish(mqtt_topic + "updated", str(datetime.now()), qos=1, retain=True)


def registerWithHomeAssitant():
    if('ha' in bh1750_mqtt_chatter):
        ha_illuminance_config = '{"device_class": "illuminance",' + \
                                ' "name": "'+mqtt_device_id+'_illuminance",' + \
                                ' "state_topic": "'+mqtt_topic+'value",' + \
                                ' "unit_of_measurement": "'+bh1750_unit+'",' + \
                                ' "value_template": "{{ value_json.illuminance}}" }'
        client.publish('homeassistant/sensor/'+mqtt_device_id+'Illuminance/config', ha_illuminance_config, qos=1, retain=True)
        log2stdout(datetime.now().timestamp(), 'Registering sensor with home assistant success...', 'info')


###############
# Setup bh1750 sensor
###############
log2stdout(bh1750_start_ts.timestamp(), 'Starting bh1750mqtt...', 'info')
sensor = None
try:
    # bus = smbus.SMBus(0) # Rev 1 Pi uses 0
    bus = smbus.SMBus(bh1750_bus)  # Rev 2 Pi uses 1
    sensor = BH1750(bus, bh1750_addr)
    sensitivity = bh1750_sens % 255
    log2stdout(datetime.now().timestamp(), 'Setting sensor sensitivity to '+str(sensitivity)+' and address to '+str(bh1750_addr), 'info')
    sensor.set_sensitivity(sensitivity)
except Exception as error:
    log2stdout(datetime.now().timestamp(), 'Unsupported device...', 'error')
    log2stdout(datetime.now().timestamp(), 'Device supported by this container is the BH1750 sensor', 'error')
    raise error

log2stdout(datetime.now().timestamp(), 'Setup bh1750 sensor success...', 'info')

###############
# Setup mqtt client
###############
if('essential' in bh1750_mqtt_chatter):
    client = mqtt.Client(mqtt_device_id, clean_session=True, userdata=None)

    if mqtt_username:
        client.username_pw_set(username=mqtt_username, password=mqtt_password)

    # set last will for an ungraceful exit
    client.will_set(mqtt_topic + "state", "OFFLINE", qos=1, retain=True)

    # keep alive for 60 times the refresh rate
    client.connect(mqtt_brokeraddr, keepalive=bh1750_refresh*60)

    client.loop_start()

    client.publish(mqtt_topic + "type", "sensor", qos=1, retain=True)
    client.publish(mqtt_topic + "device", "bh1750", qos=1, retain=True)

    if('full' in bh1750_mqtt_chatter):
        client.publish(mqtt_topic + "env/brokeraddr", mqtt_brokeraddr, qos=1, retain=True)
        client.publish(mqtt_topic + "env/username", mqtt_username, qos=1, retain=True)
        client.publish(mqtt_topic + "env/refresh", bh1750_refresh, qos=1, retain=True)
        client.publish(mqtt_topic + "env/logging", bh1750_logging_mode, qos=1, retain=True)
        client.publish(mqtt_topic + "env/mqtt_chatter", bh1750_mqtt_chatter, qos=1, retain=True)

    client.publish(mqtt_topic + "updated", str(datetime.now()), qos=1, retain=True)

    log2stdout(datetime.now().timestamp(), 'Setup mqtt client success...', 'info')

    client.publish(mqtt_topic + "state", "ONLINE", qos=1, retain=True)

    registerWithHomeAssitant()

log2stdout(datetime.now().timestamp(), 'Begin capture...', 'info')


while True:
    try:
        bh1750_ts = datetime.now().timestamp()

        if(bh1750_mode == 0):
            lux = sensor.measure_low_res()
        if(bh1750_mode == 1):
            lux = sensor.measure_high_res()
        if(bh1750_mode == 2):
            lux = sensor.measure_high_res2()

        data = {'timestamp': bh1750_ts,
                'lux': lux}

        log2stdout(bh1750_ts, data, 'info')
        log2file('recording', data)
        updateEssentialMqtt(lux)
        time.sleep(bh1750_refresh)

    except RuntimeError as error:
        detected = 'error'

        data = {'timestamp': bh1750_ts, 'error_type': error.args[0]}
        log2stdout(bh1750_ts, data, 'warning')
        log2file('error', data)

        time.sleep(bh1750_refresh)
        continue

    except Exception as error:
        if('essential' in bh1750_mqtt_chatter):
            client.disconnect()
        raise error
