#!/usr/bin/python
#-*- coding:utf-8 -*-
 
import RPi.GPIO as GPIO
import time
 
channel = 7         #引脚号Pin7
data = []           #温湿度值
j = 0               #计数器
 
GPIO.setmode(GPIO.BOARD)    #以BOARD编码格式
time.sleep(1)               #时延一秒
 
# 1、MCU发送开始起始信号
# 总线空闲状态为高电平，主机把总线拉低等待DHT11响应；
# 与MCU相连的SDA数据引脚置为输出模式；
# 主机把总线拉低至少18毫秒，然后拉高20-40us等待DHT返回响应信号；
GPIO.setup(channel, GPIO.OUT)
GPIO.output(channel, GPIO.LOW)
time.sleep(0.02)
GPIO.output(channel, GPIO.HIGH)

# 2、读取DHT11响应
# SDA数据引脚设为输入模式；
# DHT11检测到起始信号后，会将总线拉低80us，然后拉高80us作为响应；
GPIO.setup(channel, GPIO.IN)
while GPIO.input(channel) == GPIO.LOW:
    continue
while GPIO.input(channel) == GPIO.HIGH:
    continue

# 3、DHT11送出40bit数据
# DHT11数据格式: 40bit数据=8位湿度整数+8位湿度小数+8位温度整数+8位温度小数+8位校验.
# 例如：0000 0010+1000 1100+0000 0001+0101 1111=1110 1110
# 二进制的湿度数据 0000 0010 1000 1100 ==>转为十进制：652，除以10即为湿度值；
# 湿度=65.2％RH
# 二进制的温度数据 0000 0001 0101 1111 ==>转为十进制：351，除以10即为温度值；
# 温度=35.1℃

# 当温度低于0℃时温度数据的最高位置1。
while j < 40:   # 40bit数据
    # 数据'0'还是'1'判定规则:
    #     位数据“0”的格式为：50 微秒的低电平和 26-28 微秒的高电平，
    #     位数据“1”的格式为：50 微秒的低电平加 70微秒的高电平。
    #     1、等待50us低电平结束
    #         因为接收数据时，低电平的时间都是50us，该位数据到底是0还是1，取决于低电平后面的高电平的时间多少；
    #         如果不考虑低电平的时间，我们可以简化程序，可以先等待低电平过去；
    #     2、数据拉高后，判断30us后数据总线电平的高低
    #         等待数据线拉高后，再延时30us，因为30us大于28us且小于70us，再检测此时数据线是否为高，如果为高，则数据判定为1，否则为0。
    k = 0
    while GPIO.input(channel) == GPIO.LOW:
        continue
 
    while GPIO.input(channel) == GPIO.HIGH:
        k += 1
        if k > 100:
            break
    
    # 8 意味高电平>30微秒。通过计数的方式判断是数据位高电平长短，以置0或1。
    if k < 8:
        data.append(0)
    else:
        data.append(1)
 
    j += 1
 
print ("sensor is working.")
print (data)              #输出初始数据高低电平

# DHT11数据格式: 40bit数据=8位湿度整数+8位湿度小数+8位温度整数+8位温度小数+8位校验.
humidity_bit = data[0:8]
humidity_point_bit = data[8:16]
temperature_bit = data[16:24]
temperature_point_bit = data[24:32]
check_bit = data[32:40]
 
humidity = 0
humidity_point = 0
temperature = 0
temperature_point = 0
check = 0
 
for i in range(8):
    humidity += humidity_bit[i] * 2 ** (7 - i)              #转换成十进制数据
    humidity_point += humidity_point_bit[i] * 2 ** (7 - i)
    temperature += temperature_bit[i] * 2 ** (7 - i)
    temperature_point += temperature_point_bit[i] * 2 ** (7 - i)
    check += check_bit[i] * 2 ** (7 - i)
 
tmp = humidity + humidity_point + temperature + temperature_point       #十进制的数据相加
 
if check == tmp:    #数据校验，相等则输出
    print ("temperature : ", temperature, ", humidity : " , humidity)
else:               #错误输出错误信息，和校验数据
    print ("wrong")
    print ("temperature : ", temperature, ", humidity : " , humidity, " check : ", check, " tmp : ", tmp)

# 重置针脚
GPIO.cleanup()                                  