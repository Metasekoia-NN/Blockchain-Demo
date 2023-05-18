from __future__ import annotations

from abc import ABC, abstractmethod

import Utils.cryptotool as cryptotool
from BC.transaction import Transaction, Transaction_REG, Transaction_REV, Transaction_UBF, Transaction_UACC


class Block(ABC):
    # attributes: ('index', 'previous_hash', 'nonce', 'merkle_root', 'merkle_height', 'transactions')

    @abstractmethod
    def __init__(self):
        self.index = 0
        self.previous_hash = ''
        self.nonce = 0
        self.merkle_root = ''
        self.merkle_height = 0
        self.transactions = []  # list[dict[Transaction]]

    @abstractmethod
    def encode_block_header(self) -> str:
        pass

    @abstractmethod
    def to_dict_header(self):
        pass

    def to_dict(self):
        dict_temp = self.to_dict_header()
        dict_temp['transactions'] = [tx.to_dict() for tx in self.transactions]
        return dict_temp

    def hash_block_header(self):
        return cryptotool.compute_hash(self.encode_block_header())

    def verify_prev_hash(self, prev_hash):
        try:
            if self.previous_hash == prev_hash:
                return True
            else:
                return False
        except AttributeError:
            return False

    def verify_body(self):
        for tx in self.transactions:
            if tx.verify_transaction() == False:
                return False
        return True

    def compute_merkle_root_height(self):
        data = []
        for tx in self.transactions:
            data.append(tx.encode_transaction_with_sign())
        return cryptotool.compute_merkle_root_height(data)

    def verify_merkle_root_height(self):
        try:
            if (self.merkle_root, self.merkle_height) == self.compute_merkle_root_height():
                return True
            else:
                return False
        except AttributeError:
            return False

    def get_merkle_proof(self, i):
        data = []
        for tx in self.transactions:
            data.append(tx.encode_transaction_with_sign())
        return cryptotool.get_merkle_proof(data, i)

    def verify_block(self, prev_hash):
        if self.verify_prev_hash(prev_hash) == True \
                and self.verify_body() == True \
                and self.verify_merkle_root_height() == True:
            return True
        else:
            return False

    def encode_block(self) -> str:
        header = self.encode_block_header()
        body = ''
        for tx in self.transactions:
            body += tx.encode_transaction_with_sign()
        return header + body

    def hash_block(self):
        if self.index == 0 or self.previous_hash == '' or self.merkle_root == '':
            raise AttributeError
        else:
            return cryptotool.compute_hash(self.encode_block())

    def is_valid_proof(self, difficulty):
        return self.hash_block().startswith('0' * difficulty)


class Block_with_REV(Block):
    # attributes: ('index', 'previous_hash', 'nonce', 'merkle_root', 'merkle_height', 'revo_flag', 'transactions')

    def __init__(self, b_dict: dict):
        self.index = 0
        self.previous_hash = ''
        self.nonce = 0
        self.merkle_root = ''
        self.merkle_height = 0
        self.revo_flag = 0  # (BF, Acc)
        self.transactions = []  # list[dict[Transaction]]

        self.__dict__.update(b_dict)

        if len(self.transactions) != 0:
            temp = []
            for t in self.transactions:
                if t['txtype'] == Transaction.REGISTER:
                    tx = Transaction_REG(t)
                elif t['txtype'] == Transaction.REVOKE:
                    tx = Transaction_REV(t)
                elif t['txtype'] == Transaction.UPDATEBF:
                    tx = Transaction_UBF(t)
                elif t['txtype'] == Transaction.UPDATEACC:
                    tx = Transaction_UACC(t)
                else:
                    break
                if tx.verify_transaction() == True:
                    temp.append(tx)
            self.transactions = temp

    def encode_block_header(self) -> str:
        return str(self.index) + str(self.previous_hash) + str(self.nonce) + str(self.merkle_root) + str(self.merkle_height) + str(self.revo_flag)

    def to_dict_header(self) -> dict:
        return {'index': self.index, 'previous_hash': self.previous_hash, 'nonce': self.nonce,
                'merkle_root': self.merkle_root, 'merkle_height': self.merkle_height, 'revo_flag': self.revo_flag}

