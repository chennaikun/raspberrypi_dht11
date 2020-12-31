import base64
import hashlib
import hmac
import random
import string
import time
import sys

class TencentIOT():
    '''
    腾讯物联网通信平台Iot Hub MQTT客户端

    device_secret = u/nAbSmZKbCW7lugludvLg==
    device_name = 'pi_dht11'
    product_id = 'J5M4D6INI9'

    MQTT 服务器连接地址，
    广州域设备填入：PRODUCT_ID.iotcloud.tencentdevices.com，
    这里 PRODUCT_ID 为变量参数，用户需填入创建产品时自动生成的产品 ID，
    例如 9****ZW2EZ.iotcloud.tencentdevices.com
    broker = 'J5M4D6INI9.iotcloud.tencentdevices.com'

    MQTT 服务器连接端口，证书认证型端口：8883；密钥认证型：1883
    port = 1883

    MQTT 协议字段，按照物联网通信约束填入：产品 ID + 设备名，
    例如："9****ZW2EZgate_dev01 "，9****ZW2EZ 是产品 ID，gate_dev01 是设备名。
    client_id = 'J5M4D6INI9pi_dht11'

    User Name ：MQTT 协议字段，按照物联网通信约束填入：产品 ID + 设备名 + SDKAppID + connid。
    （创建完产品即可在产品列表页和产品详情页查看 ProductID）如：
    "9****ZW2EZgate_dev01;12010126;12345"，仅替换示例中的产品 ID + 设备名即可，
    后面的两个参数本身由物联网通信接入 SDK 自动生成，所以这里填写固定测试值。
    mqtt_username = 'J5M4D6INI9pi_dht11;12010126;13GB9;1645079520'

    证书认证：由于 mqtt.fx 默认将密码标志位设为 true，
    所以需要填写一个任意的非空字符串作为密码，否则无法连接到物联云通信后台。
    而实际接入物联云后台时，鉴权是根据证书认证，此处随机填写的密码不会作为接入凭证。
    密钥认证：用户可进入 Hub 相应设备列表查看获取（具体页面见下方密钥认证步骤），也可以按照文档 手动生成Password。
    mqtt_password = '995566e2241a06391c30d9ac23de2706a0e9e59247830c556eb55ccfdee5f127;hmacsha256'
    '''

    def __init__(self, product_id, device_name, device_secret):
        broker = f'{product_id}.iotcloud.tencentdevices.com'
        port = 1883
        username, password, client_id = self.__IotHmac(product_id, device_name, device_secret)

        supper.__init__(broker, port, username, password, client_id, clean_session=True)

    # 生成指定长度的随机字符串
    def __random_conn_id(self, length):
        return  ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

    # 生成接入物联网通信平台需要的各参数
    def __IotHmac(self, productID, devicename, devicePsk):
        # 1. 生成 connid 为一个随机字符串，方便后台定位问题
        connid   = self.__random_conn_id(5)
        # 2. 生成过期时间，表示签名的过期时间,从纪元1970年1月1日 00:00:00 UTC 时间至今秒数的 UTF8 字符串
        expiry   = int(time.time()) + 60 * 60
        # 3. 生成 MQTT 的 clientid 部分, 格式为 ${productid}${devicename}
        clientid = "{}{}".format(productID, devicename)
        # 4. 生成 MQTT 的 username 部分, 格式为 ${clientid};${sdkappid};${connid};${expiry}
        username = "{};12010126;{};{}".format(clientid, connid, expiry)
        # 5. 对 username 进行签名，生成token
        token = hmac.new(devicePsk.decode("base64"), username, digestmod=hashlib.sha256).hexdigest()
        # 6. 根据物联网通信平台规则生成 password 字段
        password = "{};{}".format(token, "hmacsha256")
        return {
            "username" : username,
            "password" : password,
            "clientid" : clientid
        }

