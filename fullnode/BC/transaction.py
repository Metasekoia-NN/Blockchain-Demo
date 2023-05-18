from __future__ import annotations

import Utils.cryptotool as cryptotool
from abc import ABC, abstractmethod


class Transaction(ABC):
    REGISTER = 0
    REVOKE = 1
    UPDATEBF = 2
    UPDATEACC = 3

    threshold = 2

    @abstractmethod
    def __init__(self):
        self.sign: dict(str, str) = {}  # Key: 公钥  Value: 签名

    @abstractmethod
    def encode_transaction(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    def hash_transaction(self) -> str:
        return cryptotool.compute_hash(self.encode_transaction())

    def sign_transaction(self, sk, pk) -> None:
        self.sign[pk] = cryptotool.sign(sk, self.hash_transaction())

    def encode_transaction_with_sign(self) -> str:
        return self.encode_transaction() + str(sorted(self.sign))

    # 1. 所有签名都有效
    # 2. 签名数超过阈值
    def verify_transaction(self) -> bool:
        try:
            tx_hash = self.hash_transaction()
            cnt = 0
            for t_pk, t_sign in self.sign.items():
                if cryptotool.verify_signature(t_pk, t_sign, tx_hash) == True:
                    cnt = cnt + 1
                else:
                    return False
            if cnt >= Transaction.threshold:
                return True
            else:
                return False
        except (KeyError, AttributeError):
            return False


class Transaction_REG(Transaction):
    # attributes: ('id', 'txtype', 'message', 'publickey', 'timestamp', 'starttime', 'endtime', 'sign')

    def __init__(self, tx_dict: dict):
        self.id = 0
        self.txtype = Transaction.REGISTER
        self.message = ''
        self.publickey = ''
        self.timestamp: str = ''
        self.starttime: str = ''
        self.endtime: str = ''
        self.sign: dict(str, str) = {}  # Key: 公钥  Value: 签名

        self.__dict__.update(tx_dict)

    def encode_transaction(self) -> str:
        return str(self.id) + str(self.txtype) + str(self.message) + str(self.publickey) + str(self.timestamp) + str(
            self.starttime) + str(self.endtime)

    def to_dict(self) -> dict:
        return {'id': self.id, 'txtype': self.txtype, 'message': self.message, 'publickey': self.publickey,
                'timestamp': self.timestamp, 'starttime': self.starttime, 'endtime': self.endtime,
                'sign': self.sign}


class Transaction_REV(Transaction):
    # attributes: ('id', 'txtype', 'message', 'publickey', 'timestamp', 'sign')

    def __init__(self, tx_dict: dict):
        self.id = 0
        self.txtype = Transaction.REVOKE
        self.message = ''
        self.publickey = ''
        self.timestamp: str = ''
        self.sign: dict(str, str) = {}  # Key: 公钥  Value: 签名

        self.__dict__.update(tx_dict)

    def encode_transaction(self) -> str:
        return str(self.id) + str(self.txtype) + str(self.message) + str(self.publickey) + str(self.timestamp)

    def to_dict(self) -> dict:
        return {'id': self.id, 'txtype': self.txtype, 'message': self.message, 'publickey': self.publickey,
                'timestamp': self.timestamp, 'sign': self.sign}


class Transaction_UBF(Transaction):
    # attributes: ('id', 'txtype', 'message', 'timestamp', 'sign')

    def __init__(self, tx_dict: dict):
        self.id = 0  # 将id加入BF
        self.txtype = Transaction.UPDATEBF
        self.message = ''  # 存放base64编码后的BF
        self.timestamp: str = ''
        self.sign: dict(str, str) = {}  # Key: 公钥  Value: 签名

        self.__dict__.update(tx_dict)

    def encode_transaction(self) -> str:
        return str(self.id) + str(self.txtype) + str(self.message) + str(self.timestamp)

    def to_dict(self) -> dict:
        return {'id': self.id, 'txtype': self.txtype, 'message': self.message,
                'timestamp': self.timestamp, 'sign': self.sign}


class Transaction_UACC(Transaction):
    # attributes: ('id', 'txtype', 'message', 'timestamp', 'sign')

    def __init__(self, tx_dict: dict):
        self.id = 0  # id需要从acc中删除，加入时不需要全局更新acc
        self.txtype = Transaction.UPDATEACC
        self.message = ''  # 存放Acc
        self.publickey = ''
        self.timestamp: str = ''
        self.sign: dict(str, str) = {}  # Key: 公钥  Value: 签名

        self.__dict__.update(tx_dict)

    def encode_transaction(self) -> str:
        return str(self.id) + str(self.txtype) + str(self.message) + str(self.publickey) + str(self.timestamp)

    def to_dict(self) -> dict:
        return {'id': self.id, 'txtype': self.txtype, 'message': self.message, 'publickey': self.publickey,
                'timestamp': self.timestamp, 'sign': self.sign}
