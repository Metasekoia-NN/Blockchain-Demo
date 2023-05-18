#!/usr/bin/python
#Author: Jianan Hong
#Created Time: 2023-03-15 18:40:14
#Name: accumulator.py
from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair
from charm.core.engine.util import objectToBytes, bytesToObject


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
