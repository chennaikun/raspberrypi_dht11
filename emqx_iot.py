from mqtt_iot import MQTTIOTBase

class EmqxIOT(MQTTIOTBase):
    '''
    emqx.cloud mqtt client
    '''
    def __init__(self):
        broker = 'pab800a0.cn.emqx.cloud'
        port = 12870
        client_id = 'huayi_pi_dht11'
        # username = '{username}'   # your username
        # password = '{password}'   # your password
        username = 'user_huayi_pi_dht11'
        password = 'poiu,0987'

        super().__init__(broker, port, username, password, client_id, clean_session=True)