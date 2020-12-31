#!/usr/bin/env python

# DHT.py
# 2019-11-07
# Public Domain

import time
import pigpio

DHTAUTO=0
DHT11=1
DHTXX=2

DHT_GOOD=0
DHT_BAD_CHECKSUM=1
DHT_BAD_DATA=2
DHT_TIMEOUT=3

class sensor:
   """
   A class to read the DHTXX temperature/humidity sensors.
   """
   def __init__(self, pi, gpio, model=DHTAUTO, callback=None):
      """
      Instantiate with the Pi and the GPIO connected to the
      DHT temperature and humidity sensor.

      Optionally the model of DHT may be specified.  It may be one
      of DHT11, DHTXX, or DHTAUTO.  It defaults to DHTAUTO in which
      case the model of DHT is automtically determined.

      Optionally a callback may be specified.  If specified the
      callback will be called whenever a new reading is available.

      The callback receives a tuple of timestamp, GPIO, status,
      temperature, and humidity.

      The timestamp will be the number of seconds since the epoch
      (start of 1970).

      The status will be one of:
      0 DHT_GOOD (a good reading)
      1 DHT_BAD_CHECKSUM (receieved data failed checksum check)
      2 DHT_BAD_DATA (data receieved had one or more invalid values)
      3 DHT_TIMEOUT (no response from sensor)
      """
      self._pi = pi                 # pigpio
      self._gpio = gpio             # gpio接口，BCM编号
      self._model = model           # DHT型号，如DHT11, DHTXX...
      self._callback = callback     # 回调函数

      self._new_data = False        # 是否收到新数据
      self._in_code = False         # 是否在接受有效数据
      self._bits = 0                # 总位数指针
      self._code = 0                # 读取的5字节编码

      self._status = DHT_TIMEOUT    # 状态
      self._timestamp = time.time() # 时间戳
      self._temperature = 0.0       # 温度
      self._humidity = 0.0          # 湿度

      pi.set_mode(gpio, pigpio.INPUT)                          # 设置输入模式
      self._last_edge_tick = pi.get_current_tick() - 10000     # ？
      self._cb_id = pi.callback(gpio, pigpio.RISING_EDGE,      # pigpio回调，中断检测到上升沿时callback
         self._rising_edge)

   def _datum(self):
      return ((self._timestamp, self._gpio, self._status,
              self._temperature, self._humidity))

   def _validate_DHT11(self, b1, b2, b3, b4):
      '''
      验证DHT11数据
      '''
      t = b2 + b1 / 10.0   # 温度 
      h = b4 + b3 / 10.0  # 湿度
      # 温度范围：0-50 湿度范围：20-80
      # if (b1 == 0) and (b3 == 0) and (t <= 60) and (h >= 9) and (h <= 90): 
      if (t <= 60) and (h >= 9) and (h <= 90): 
         valid = True
      else:
         valid = False
      return (valid, t, h)

   def _validate_DHTXX(self, b1, b2, b3, b4):
      '''
      验证DHTXX数据
      '''

      # 检查正负符号（最高位为1为负数）和小数因子
      if b2 & 128:
         div = -10.0
      else:
         div = 10.0
      t = float(((b2&127)<<8) + b1) / div # 温度（包含小数）。
      h = float((b4<<8) + b3) / 10.0      # 湿度（包含小数）
      # 验证取值范围
      if (h <= 110.0) and (t >= -50.0) and (t <= 135.0):
         valid = True
      else:
         valid = False
      return (valid, t, h)

   def _decode_dhtxx(self, code):
      """
            +-------+-------+
            | DHT11 | DHTXX |
            +-------+-------+
      Temp C| 0-50  |-40-125|
            +-------+-------+
      RH%   | 20-80 | 0-100 |
            +-------+-------+

               0      1      2      3      4
            +------+------+------+------+------+
      DHT11 |check-| 0    | temp |  0   | RH%  |
            |sum   |      |      |      |      |
            +------+------+------+------+------+
      DHT21 |check-| temp | temp | RH%  | RH%  |
      DHT22 |sum   | LSB  | MSB  | LSB  | MSB  |
      DHT33 |      |      |      |      |      |
      DHT44 |      |      |      |      |      |
            +------+------+------+------+------+
      """
      b0 =  code        & 0xff   # 校验和
      b1 = (code >>  8) & 0xff   # 温度小数
      b2 = (code >> 16) & 0xff   # 温度整数
      b3 = (code >> 24) & 0xff   # 湿度小数
      b4 = (code >> 32) & 0xff   # 温度整数
      # print(f'code: {code:b}')
      # print(f'b1:{b1}, b2: {b2}, b3: {b3}, b4: {b4}')

      chksum = (b1 + b2 + b3 + b4) & 0xFF # 校验和

      if chksum == b0:  # 校验和正确
         if self._model == DHT11:
            valid, t, h = self._validate_DHT11(b1, b2, b3, b4)
         elif self._model == DHTXX:
            valid, t, h = self._validate_DHTXX(b1, b2, b3, b4)
         else: # AUTO
            # Try DHTXX first.
            valid, t, h = self._validate_DHTXX(b1, b2, b3, b4)
            if not valid:
               # try DHT11.
               valid, t, h = self._validate_DHT11(b1, b2, b3, b4)
         if valid:
            self._temperature = t
            self._humidity = h
            self._status = DHT_GOOD
         else:
            self._status = DHT_BAD_DATA
      else:
         self._status = DHT_BAD_CHECKSUM

      self._new_data = True

   def _rising_edge(self, gpio, level, tick):
      '''
      callback(user_gpio, edge, func)
      Calls a user supplied function (a callback) whenever the specified 
      GPIO edge is detected. 

      Parameters

      user_gpio:= 0-31.
         edge:= EITHER_EDGE, RISING_EDGE (default), or FALLING_EDGE.
         func:= user supplied callback function.


      The user supplied callback receives three parameters, the GPIO, the
      level, and the tick. 

      Parameter   Value    Meaning

      GPIO        0-31     The GPIO which has changed state

      level       0-2      0 = change to low (a falling edge)
                           1 = change to high (a rising edge)
                           2 = no level change (a watchdog timeout)

      tick        32 bit   The number of microseconds since boot
                           WARNING: this wraps around from
                           4294967295 to 0 roughly every 72 minutes
      2、读取DHT11响应
      SDA数据引脚设为输入模式；
      DHT11检测到起始信号后，会将总线拉低80us，然后拉高80us作为响应；
      3、DHT11送出40bit数据
      位数据“0”的格式为：50 微秒的低电平和 26-28 微秒的高电平，
      位数据“1”的格式为：50 微秒的低电平加 70微秒的高电平。
      '''
      edge_len = pigpio.tickDiff(self._last_edge_tick, tick)   # 电平时长
      self._last_edge_tick = tick
      if edge_len > 10000:             # 10000 why?
         self._in_code = True          # 开始传输数据
         self._bits = -2               # why?
         self._code = 0
      elif self._in_code:
         self._bits += 1               # 增加1位
         if self._bits >= 1:
            self._code <<= 1           # 左移1位
            if (edge_len >= 60) and (edge_len <= 150):   # 有效的电平
               if edge_len > 100:
                  # 1 bit
                  self._code += 1
            else:
               # invalid bit
               self._in_code = False   # 错误时复位
         if self._in_code:
            if self._bits == 40:       # 总40位
               self._decode_dhtxx(self._code)
               self._in_code = False   # 复位

   def _trigger(self):
      '''
      MCU发送开始起始信号，触发数据传输。
      1、MCU发送开始起始信号
      总线空闲状态为高电平，主机把总线拉低等待DHT11响应；
      与MCU相连的SDA数据引脚置为输出模式；
      主机把总线拉低至少18毫秒，然后拉高20-40us等待DHT返回响应信号；
      '''
      self._new_data = False
      self._timestamp = time.time()
      self._status = DHT_TIMEOUT
      self._pi.write(self._gpio, 0) # 低电位，拉低至少18ms
      if self._model != DHTXX:
         time.sleep(0.018)
      else:
         time.sleep(0.001)
      
      # 为何没有拉高20-40us？

      self._pi.set_mode(self._gpio, pigpio.INPUT)  # 等待输入


   def cancel(self):
      """
      取消回调
      """
      if self._cb_id is not None:
         self._cb_id.cancel()
         self._cb_id = None

   def read(self):
      """
      This triggers a read of the sensor.

      The returned data is a tuple of timestamp, GPIO, status,
      temperature, and humidity.

      The timestamp will be the number of seconds since the epoch
      (start of 1970).

      The status will be one of:
      0 DHT_GOOD (a good reading)
      1 DHT_BAD_CHECKSUM (receieved data failed checksum check)
      2 DHT_BAD_DATA (data receieved had one or more invalid values)
      3 DHT_TIMEOUT (no response from sensor)
      """

      # MCU发送开始起始信号
      self._trigger()
      for i in range(5): # timeout after 0.25 seconds.
         time.sleep(0.05)
         if self._new_data:   # 0.25秒内有数据
            break
      datum = self._datum()
      if self._callback is not None:
          self._callback(datum)
      return datum

if __name__== "__main__":
   import sys
   import pigpio
   import DHT

   def callback(data):
      print("{:.3f} {:2.1f} {} {:3.1f} {:3.1f} *".
         format(data[0], data[1], data[2], data[3], data[4]))

   argc = len(sys.argv) # get number of command line arguments

   if argc < 2:
      print("Need to specify at least one GPIO")
      exit()

   pi = pigpio.pi()
   if not pi.connected:
      exit()

   # Instantiate a class for each GPIO
   # for testing use a GPIO+100 to mean use the callback
   S = []
   for i in range(1, argc): # ignore first argument which is command name
      g = int(sys.argv[i])
      if (g >= 100):
         s = DHT.sensor(pi, g-100, callback=callback)
      else:
         s = DHT.sensor(pi, g)
      S.append((g,s)) # store GPIO and class

   while True:
      try:
         for s in S:
            if s[0] >= 100:
               s[1].read() # values displayed by callback
            else:
               d = s[1].read()
               print("{:.3f} {:2d} {} {:3.1f} {:3.1f}".
                  format(d[0], d[1], d[2], d[3], d[4]))
         time.sleep(2)
      except KeyboardInterrupt:
         break

   for s in S:
      s[1].cancel()
      print("cancelling {}".format(s[0]))
   pi.stop()
