import json
from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair
from charm.core.engine.util import objectToBytes


def to_str(element, group=PairingGroup('MNT224')):
    return objectToBytes(element, group).decode()

Group = PairingGroup('MNT224')

delta = Group.random(G1)
sk = Group.random(ZR)
g2 = Group.random(G2)
pk = g2 ** sk
userset = {-1}

acc_const = {
    'delta': to_str(delta),
    'sk': to_str(sk),
    'g2': to_str(g2),
    'pk': to_str(pk),
    'userset': str(userset),
}

with open('conf/acc_const.json', 'w') as facc:
    json.dump(acc_const, facc, indent=4)
