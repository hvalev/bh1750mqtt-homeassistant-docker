# bh1750 illuminance sensor in a docker container
[![build](https://github.com/hvalev/bh1750mqtt-homeassistant-docker/actions/workflows/main.yml/badge.svg)](https://github.com/hvalev/bh1750mqtt-homeassistant-docker/actions/workflows/main.yml)
![Docker Pulls](https://img.shields.io/docker/pulls/hvalev/bh1750mqtt-homeassistant)
![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/hvalev/bh1750mqtt-homeassistant)

This docker container enables you to use the BH1750 illuminance sensor on a GPIO enabled device such as raspberry pi. This container can communicate with an MQTT broker and relay the sensors' values in addition to integrating with home assistants' [discovery](https://www.home-assistant.io/docs/mqtt/discovery/) protocol. Discovery will automatically detect the sensor and make it available for visualizations, automations, etc within your home assistant instance.

## How to run it
The following docker run command or docker-compose service will get you up and running with the minimal configuration.
```docker run --device=/dev/i2c-1:/dev/i2c-1 -e topic=zigbee2mqtt -e device_id=bh1750 -e broker=192.168.X.X hvalev/bh1750mqtt-homeassistant```
```
version: "3.8"
services:
  bh1750mqtt:
    image: hvalev/bh1750mqtt-homeassistant
    container_name: bh1750mqtt
    devices:
      - /dev/i2c-1:/dev/i2c-1
    environment:
      - topic=zigbee2mqtt
      - device_id=bh1750
      - broker=192.168.X.X
```
```/dev/i2c-1:/dev/i2c-1``` is required to access the Inter-Integrated Circuit bus and communicate with your BH1750 sensor. If it doesn't work, you can try to run the container in privileged mode ```privileged:true```.

## Parameters
The container offers the following configurable environment variables:</br>
| Parameter | Possible values | Description | Default |
| --------- | --------------- | ----------- | ------- |
| ```topic``` |  | MQTT topic to submit to. | ```zigbee2mqtt```  |
| ```device_id``` |  | Unique identifier for the device. \*If you have multiple, you could use something like ```bedroom_dht22```. | ```bh1750``` |
| ```broker``` |  | MQTT broker ip address. | ```192.168.1.10``` |
| ```username``` |  | MQTT username. | `None` |
| ```password``` |  | MQTT password. | `None` |
| ```bus``` |  | Variable passed to the i2c bus. Rev 1 Pi uses 0, Rev 2 Pi uses 1. | ```1``` |
| ```addr``` |  | Pin address. | ```0x23``` |
| ```sens``` |  | Sensor sensitivity. Possible values are 31-254. | ```254``` |
| ```unit``` |  | Measurement unit. | ```lx``` |
| ```mode``` |  | Measurement mode. Supported methods are *measure_low_res*, *measure_high_res* and *measure_high_res2* coded as 0, 1 and 2. Recommended is to set at ```1```.  | ```1``` |
| ```poll``` |  | Sampling rate in seconds. Depending on the measurement mode (see ```mode``` variable) different sampling rates are possible ([Specs Datasheet](https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf)). Recommended value is at least 2 seconds. | ```2``` |
| ```mqtt_chatter``` | ```essential\|ha\|full``` | Controls how much information is relayed over to the MQTT broker. Possible ***non-mutually exclusive*** values are: ```essential``` - enables basic MQTT communications required to connect and transmit data to the zigbee broker; ```ha``` enables home assistant discovery protocol; ```full``` enables sending information about container internals over to the MQTT broker. | ```essential\|ha``` |
| ```logging``` | ```log2stdout\|log2file``` | Logging strategy. Possible ***non-mutually exclusive*** values are: ```log2stdout``` - forwards logs to stdout, inspectable through ```docker logs dht22mqtt``` and ```log2file``` which logs temperature and humidity readings to files timestamped at containers' start. | ```none``` |
----------------------------------

*If you end up using ```log2file```, make sure to add this volume in your docker run or docker-compose commands ```- ~/yourfolderpath:/log``` to be able to access the logs from your host os.* </br> 

*If you want to run this container to simply record values to files with no MQTT integration, you need to explicitly set ```mqtt_chatter``` to a blank string. In that case, you can also omit all MQTT related parameters from your docker run or compose configurations.* </br>

*If you're using this container for multiple sensors on the same or different devices which, however, connect to the same mqtt network, you need to explicitly pick a unique ```device_id``` for each. Otherwise, identically named devices will boot each other off the network each time they transmit a reading.* </br>

*I have noticed that using ```measure_high_res2``` for sensor measurement ```mode``` sometimes produces 0 lux measurements. Some sort of filtering may be required if you opt for it.*

## Connecting your sensor 
There are multiple online resources on how to hook up your sensor. Be mindful that the pins your sensor is connected to influences the ```addr``` pin parameter above.

## Acknowledgements
The bh1750.py class has been shamelessly copied from the following [gist](https://gist.github.com/oskar456/95c66d564c58361ecf9f).
