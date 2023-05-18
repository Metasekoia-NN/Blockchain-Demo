from __future__ import annotations

from hashlib import sha256
import ecdsa
import base64


def compute_hash(message) -> str:
    # The string equivalent also considers the previous_hash field now
    if type(message) == bytes:
        return sha256(message).hexdigest()
    elif type(message) == str:
        return sha256(message.encode()).hexdigest()
    else:
        raise TypeError('bytes or str')


# return merkle_root, merkle_tree_height
def compute_merkle_root_height(data: list[str]) -> tuple[str, int]:
    temp = []
    for i in range(len(data)):
        temp.append(compute_hash(data[i]))
    # print(temp)
    data = temp
    height = 1
    while len(data) != 1:
        height = height + 1
        temp = []
        for i in range(0, len(data), 2):
            if i + 1 == len(data):
                data.append(data[i])
            new_hash = compute_hash(bytes.fromhex(data[i]) + bytes.fromhex(data[i + 1]))
            # print(data[i], data[i + 1], '->', new_hash)
            temp.append(new_hash)
        data = temp
    return data[0], height


def get_merkle_proof(data: list[str], index: int) -> list[str]:
    if index < 0 or index >= len(data):
        raise IndexError
    merkle_proof = []
    temp = []
    for i in range(len(data)):
        temp.append(compute_hash(data[i]))
    data = temp
    while len(data) != 1:
        if index == len(data) - 1 and len(data) % 2 == 1:
            merkle_proof.append(data[-1])
        else:
            merkle_proof.append(data[index + 1] if index % 2 == 0 else data[index - 1])
        temp = []
        for i in range(0, len(data), 2):
            if i + 1 == len(data):
                data.append(data[i])
            new_hash = compute_hash(bytes.fromhex(data[i]) + bytes.fromhex(data[i + 1]))
            # print(data[i], data[i + 1], '->', new_hash)
            temp.append(new_hash)
        data = temp
        index = index // 2
    return merkle_proof


# TODO: add merkle_height fin
def verify_merkle_proof(data: str, merkle_proof: list[str], merkle_root: str, merkle_height: int, index: int) -> bool:
    if len(merkle_proof) != merkle_height - 1 or len(merkle_proof) >= 10 or index < 0 or index >= 2 ** len(merkle_proof) :
        return False
    data_hash = compute_hash(data)
    for i in range(len(merkle_proof)):
        if index % 2 == 0:
            data_hash = compute_hash(bytes.fromhex(data_hash) + bytes.fromhex(merkle_proof[i]))
        else:
            data_hash = compute_hash(bytes.fromhex(merkle_proof[i]) + bytes.fromhex(data_hash))
        index = index // 2
    if data_hash == merkle_root:
        return True
    else:
        return False


# 密钥生成
# 生成并返回一对公私钥
def generate_ECDSA_keys():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)  # this is your sign (private key)
    private_key = sk.to_string().hex()  # convert your private key to hex
    vk = sk.get_verifying_key()  # this is your verification key (public key)
    public_key = vk.to_string().hex()
    return public_key, private_key


# 签名
# private_key: hex string 格式的私钥
# data: bytes 类型的消息数据
# 返回 base64 编码的签名
def sign(private_key, data) -> str:
    if type(data) == str:
        data = data.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    return base64.b64encode(sk.sign(data)).decode()


# 验证签名
# public_key: hex string 格式的公钥
# signature: base64 编码的签名
# message: bytes 类型的消息数据
# 返回 True（验证成功）或 False（验证失败）
def verify_signature(public_key, signature, digest) -> bool:
    signature = base64.b64decode(signature)
    if type(digest) == str:
        digest = digest.encode()
    try:
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
        return vk.verify(signature, digest)
    except:
        return False
