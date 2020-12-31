import random
import datetime
import json
import logging

import paho.mqtt.client as mqtt
import shortuuid

class MQTTIOTBase(object):
    '''
    mqtt客户端
    '''
    def __init__(self, broker, port, username, password, client_id, clean_session=True):
        self.__logger = logging.getLogger()

        self.__borker = broker
        self.__port = port
        self.__client_id = client_id
        self.__username = username
        self.__password = password

        self.__clean_session = clean_session

        self.connect()
        self.__client.loop_start()

    def connect(self):
        '''
        连接mqtt broker
        '''
        if not self.__client_id:
            self.__client_id = f'mqtt_{shortuuid.uuid()}'

        self.__client = mqtt.Client(
            self.__client_id, 
            clean_session=self.__clean_session
        )
        self.__client.username_pw_set(
            username=self.__username, 
            password=self.__password)
        self.__client.on_connect = self.on_connect
        self.__client.on_message = self.on_message

        self.__logger.debug(f'connecting to {self.__borker}:{self.__port}')
        self.__client.connect(self.__borker, self.__port)

    def on_connect(self, client, userdata, flags, rc):
        '''
        连接borker的回调
        '''
        if rc == 0:
            self.__logger.info("Connected to MQTT Broker!")
        else:
            self.__logger.info("Failed to connect, return code %d\n", rc)

    def on_message(self, client, userdata, msg):
        self.__logger.info(msg.topic+" "+str(msg.payload))

    def publish(self, topic, message):
        '''
        发布到mqtt broker
        '''
        result = self.__client.publish(topic, json.dumps(message))
        # result: [0, 1]
        status = result[0]
        if status == 0:
            self.__logger.info(f"publish `{message}` to topic `{topic}`")
        else:
            self.__logger.warning(f"Failed to send message to topic {topic}")
