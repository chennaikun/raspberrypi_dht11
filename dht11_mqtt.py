import os
import logging.config
import yaml
import time
import datetime

import pigpio

import DHT
from emqx_iot import EmqxIOT

topic = '/raspberry/temp'

def setup_logging(default_path = "logging.yaml", default_level = logging.INFO, env_key = "LOG_CFG"):
    '''
    配置日志模块logging
    '''
    path = default_path
    value = os.getenv(env_key,None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path,"r") as f:
            config = yaml.load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)        

def publish_temp_humi(timestamp, temperature, humidity):
    '''
    通过mqtt发布温湿度
    '''
    # Sample output Date: 2019-11-17T10:55:08, Temperature: 25°C, Humidity: 72%
    date = datetime.datetime.fromtimestamp(timestamp).replace(microsecond=0).isoformat()
    message = {
        "reported": {
            "TimeStamp": f"{date}",
            "Temperature": f"{temperature}",
            "Humidity": f"{humidity}"
        }
    }

    # publish to mqtt broker
    mqtt_client.publish(topic, message)

if __name__ == '__main__':
    setup_logging()

    global mqtt_client
    mqtt_client = EmqxIOT()

    time.sleep(1)

    # 初始化pigpio
    pi = pigpio.pi()
    if not pi.connected:
        exit()

    # 初始化DHT11传感器
    pin = 4     # Data - Pin 7 (BCM 4)
    s = DHT.sensor(pi, pin, model=DHT.DHT11)

    while True:
        try:
            timestamp, gpio, status, temperature, humidity = s.read()   #read DHT device
            if (status == DHT.DHT_GOOD):
                publish_temp_humi(timestamp, temperature, humidity)
            elif (status == DHT.DHT_TIMEOUT):  # no response from sensor
                print("DHT_TIMEOUT ERROR! Try again...")
            elif (status == DHT.DHT_BAD_CHECKSUM):  # no response from sensor
                print("DHT_BAD_CHECKSUM ERROR! Try again...")
            elif (status == DHT.DHT_BAD_DATA):  # no response from sensor
                print("DHT.DHT_BAD_DATA ERROR! Try again...")

            time.sleep(2)
        except KeyboardInterrupt:
            break
    
    s.cancell()
    pi.stop()