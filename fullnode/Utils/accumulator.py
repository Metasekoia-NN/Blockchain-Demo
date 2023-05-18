#!/usr/bin/python
#Author: Jianan Hong
#Created Time: 2023-03-15 18:40:14
#Name: accumulator.py
from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair
from charm.core.engine.util import objectToBytes, bytesToObject


class Accumulator():
    def __init__(self, groupObj, delta, sk, g2, pk, userset):
        self.group = groupObj
        # self.delta = self.group.random(G1)
        # self.__sk = self.group.random(ZR)
        # self.g2 = self.group.random(G2)
        # self.pk = self.g2 ** self.__sk
        self.delta = delta
        self.__sk = sk
        self.g2 = g2
        self.pk = pk
        self.userset = userset

    # 通过区块链共识保证x（身份的唯一标识符）无重复
    def useradd(self, x):
        witness = self.delta ** ((x + self.__sk) ** (-1))
        self.userset.add(x)
        return witness

    def userdel(self, x):
        self.delta = self.delta ** ((x + self.__sk) ** (-1))

    # def to_dict_bytes(self):
    #     return {'delta': objectToBytes(self.delta, self.group), 'g2': objectToBytes(self.g2, self.group), 'pk': objectToBytes(self.pk, self.group)}
    
    # def to_dict(self):
    #     return {'delta': objectToBytes(self.delta, self.group), 'g2': objectToBytes(self.g2, self.group), 'pk': objectToBytes(self.pk, self.group), 'userset': str(self.userset)}

# def to_bytes(element, group=PairingGroup('MNT224')):
#     return objectToBytes(element, group)

# def from_bytes(element, group=PairingGroup('MNT224')):
#     return bytesToObject(element, group)

def to_str(element, group=PairingGroup('MNT224')):
    return objectToBytes(element, group).decode()

def from_str(element, group=PairingGroup('MNT224')):
    return bytesToObject(element.encode(), group)

# a plaintext verification
def witness_verify(delta, g2, pk, x, witness):
    return pair(witness, g2 ** x * pk) == pair(delta, g2)


# i删掉了j
def del_update_witness(delta_new, i, j, witness):
    witness_new = (witness / delta_new) ** ((j - i) ** (-1))
    return witness_new


# def main():
#     group = PairingGroup('MNT224')
#     acc = Accumulator(group)

#     secret1 = group.init(ZR, 5)
#     secret2 = group.init(ZR, 10)

#     print(secret1, secret2)
#     print(type(secret1), type(secret2))

#     witness1 = acc.useradd(secret1)
#     witness2 = acc.useradd(secret2)

#     print(secret1, witness1, witness_verify(acc, secret1, witness1))
#     print(secret2, witness2, witness_verify(acc, secret2, witness2))

#     acc.userdel(secret1)
#     print(secret1, witness1, witness_verify(acc, secret1, witness1))
#     print(secret2, witness2, witness_verify(acc, secret2, witness2))


#     witness2 = del_update_witness(acc.delta, secret2, secret1, witness2)
#     print(secret2, witness2, witness_verify(acc, secret2, witness2))

#     print(acc.delta, type(acc.delta))
#     print(acc.g2, type(acc.g2))
#     print(acc.pk, type(acc.pk))

#     delta_bytes = objectToBytes(acc.delta, PairingGroup('MNT224'))
#     delta_new = bytesToObject(delta_bytes, PairingGroup('MNT224'))

#     g2_bytes = objectToBytes(acc.g2, PairingGroup('MNT224'))
#     pk_bytes = objectToBytes(acc.pk, PairingGroup('MNT224'))

#     print(delta_new, type(delta_new))


# if __name__ == '__main__':
#     main()
