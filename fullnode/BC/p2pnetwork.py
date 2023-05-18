import json
import requests
import ast

from Utils.bcdebug import *

class P2PNetwork():
    def __init__(self):
        self.peer_list = []
        try:
            with open('conf/network_config.json') as f:
                self.peer_list = json.load(f)
        except FileNotFoundError:
            pass

    def add_node(self, host, port):
        self.peer_list.append({'host': host, 'port': port})

    # # 收到之后继续发 / 不继续发 在HTTP响应中判断
    # def gossip(self, url_path, content):
    #     # 实际上就是收到之后再broadcast
    #     self.broadcast(url_path, content, True)

    @staticmethod
    def get_request(url: str, params: dict=None):
        res = requests.get(url, params=params)
        return res

    @staticmethod
    def post_request(url: str, message: dict):
        res = requests.post(url, json=message)
        return res

    # 交易签名请求
    # 交易公开
    # 区块公开
    def broadcast(self, url_path, content):
        for peer in self.peer_list:
            url = 'http://{}:{}{}'.format(peer['host'], peer['port'], url_path)
            try:
                res = requests.post(url, json=content)
                debug_info('broadcast {}'.format(url_path), res.status_code)
            except requests.exceptions.ConnectionError:
                debug_error('broadcast', url + ' requests.exceptions.ConnectionError')

    def get_broadcast(self, url_path, params) -> dict:
        peer_res_dict = {}
        for peer in self.peer_list:
            url = 'http://{}:{}{}'.format(peer['host'], peer['port'], url_path)
            try:
                res = requests.get(url, params=params)
                debug_info('get_broadcast {}'.format(url_path), res.status_code)
                if res.status_code == 200:
                    peer_res_dict['http://{}:{}'.format(peer['host'], peer['port'])] = ast.literal_eval(res.text)
            except requests.exceptions.ConnectionError:
                debug_error('get_broadcast', url + ' requests.exceptions.ConnectionError')
        return peer_res_dict
