import Utils.cryptotool as cryptotool
import os

pk, sk = cryptotool.generate_ECDSA_keys()

if not os.path.exists('conf/crypto_data'):
    os.makedirs('conf/crypto_data', exist_ok=True)

with open('conf/crypto_data/pk.txt', 'w') as fpk:
    fpk.write(pk)
with open('conf/crypto_data/sk.txt', 'w') as fsk:
    fsk.write(sk)
