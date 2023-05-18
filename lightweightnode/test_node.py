import requests
import random
import time
import ast

import Utils.timetool as timetool
import Utils.cryptotool as cryptotool
from Utils.bloomfilter import BF
from Utils.accumulator import *


block_headers = []
user_id_list = []
merkle_proof_list = []
bf = BF(1000, 0.3)
acc_delta = 0


fullnode_list = [
    {
        "host": "172.28.0.2",
        "port": 8080
    },
    {
        "host": "172.28.0.3",
        "port": 8080
    },
    {
        "host": "172.28.0.4",
        "port": 8080
    },
    {
        "host": "172.28.0.5",
        "port": 8080
    },
    {
        "host": "172.28.0.6",
        "port": 8080
    }
]


def random_fullnode_baseurl(num=0):
    if num <= 0:
        i = random.randint(0, len(fullnode_list) - 1)
        return 'http://{}:{}'.format(fullnode_list[i]['host'], fullnode_list[i]['port'])
    else:
        i = random.sample(range(0, len(fullnode_list)), num)
        return ['http://{}:{}'.format(fullnode_list[j]['host'], fullnode_list[j]['port']) for j in i]


def encode_block_header(block_header):
    return str(block_header['index']) + str(block_header['previous_hash']) + str(block_header['nonce']) + str(block_header['merkle_root']) + str(block_header['merkle_height']) + str(block_header['revo_flag'])


def hash_block_header(block_header):
    return cryptotool.compute_hash(encode_block_header(block_header))


def get_block_headers(begin_height):
    url = random_fullnode_baseurl()

    res = requests.get(url + '/blockheaders', params={'begin_height': begin_height})
    if res.status_code == 200:
        return ast.literal_eval(res.text)['block_headers']
    else:
        raise ValueError


def verify_block_headers(prev_hash, new_block_headers):
    temp_hash = prev_hash
    for i in new_block_headers:
        if i['previous_hash'] == temp_hash:
            temp_hash = hash_block_header(i)
        else:
            return False
    return True


def encode_transaction_with_sign(tx):
    return str(tx['id']) + str(tx['txtype']) + str(tx['message']) + str(tx['publickey']) + str(tx['timestamp']) + str(tx['starttime']) + str(tx['endtime']) + str(sorted(tx['sign']))


# 身份验证相关
def get_merkle_root_height(i):
    global block_headers
    return (block_headers[i]['merkle_root'], block_headers[i]['merkle_height'])


def verify_merkle_proof(data, merkle_proof, merkle_root, merkle_height, j):
    return cryptotool.verify_merkle_proof(encode_transaction_with_sign(data), merkle_proof, merkle_root, merkle_height, j)


def verify_date(begin_date, end_date):
    now = timetool.get_current_date()
    if now >= timetool.strdate2date(begin_date) and now <= timetool.strdate2date(end_date):
        return True
    else:
        return False


def verify_revo(IDx, bf: BF):
    if IDx in bf:
        return False
    else:
        return True


# 区块头信息维护
def check_revo_flag(block_header):
    try:
        f = block_header['revo_flag']
        if f == 0:
            return (0, 0)
        if f == 1:
            return (0, 1)
        if f == 2:
            return (1, 0)
        if f == 3:
            return (1, 1)
        else:
            return (-1, -1)
    except:
        return (-1, -1)


def update_bf(block_index):
    global bf
    url = random_fullnode_baseurl()
    res = requests.get(url + '/bf', params={'index': block_index})
    if res.status_code == 200:
        tx = ast.literal_eval(res.text)
        print(tx)
        # bf = BF.frombase64(tx['message'])
        # save_lwn_data()
    else:
        print(res.status_code, 'ERROR')


def update_acc(block_index):
    global acc_delta
    # self_acc_witness, global self_id, need_to_update_acc
    url = random_fullnode_baseurl()
    res = requests.get(url + '/acc', params={'index': block_index})
    if res.status_code == 200:
        print(ast.literal_eval(res.text))
        acc_data = ast.literal_eval(res.text)
        if len(acc_data) > 0:
            acc_delta = from_str(acc_data[-1]['message'])
        # if need_to_update_acc:
        #     for tx in acc_data:
        #         self_acc_witness = del_update_witness(tx['message'], self_id, tx['id'], self_acc_witness)
        # save_lwn_data()
    else:
        print(res.status_code, 'ERROR')


def update_block_headers(new_block_headers, begin_height):
    global block_headers
    # global self_id, need_to_update_acc
    block_headers = block_headers[:begin_height] + new_block_headers
    for bh in new_block_headers:
        BF_update, Acc_update = check_revo_flag(bh)
        if BF_update == 1:
            update_bf(bh['index'])
            # if self_id in bf:
            #     ID_add_acc()
        if Acc_update == 1:
            update_acc(bh['index'])
        if BF_update == Acc_update == -1:
            print('block_header_maintain -> check_revo_flag WRONG!')


def block_header_maintain():
    global block_headers
    print('block_header_maintain -> ', timetool.time2strtime(timetool.get_current_time()))
    i = 0
    if len(block_headers) > 0:
        while block_headers[-1]['index'] >= i * 10:
            new_block_headers = get_block_headers(block_headers[-1]['index'] - i * 10)
            if block_headers[-1]['index'] == i * 10:
                prev_hash = cryptotool.compute_hash('genesis_block')
            else:
                prev_hash = hash_block_header(block_headers[-1]['index'] - i * 10 - 1)
            if verify_block_headers(prev_hash, new_block_headers) == True:
                update_block_headers(new_block_headers, block_headers[-1]['index'] - i * 10)
                break
            i += 1
    else:
        new_block_headers = get_block_headers(0)
        if len(new_block_headers) > 0:
            prev_hash = hash_block_header(new_block_headers[0])
            if verify_block_headers(prev_hash, new_block_headers[1:]) == True:
                update_block_headers(new_block_headers[1:], 1)
            block_headers = new_block_headers


def main():
    global block_headers, user_id_list, merkle_proof_list
    for i in range(100):
        baseurl = random_fullnode_baseurl()
        postdata = {'pk': 'test_reg_{}'.format(i), 'message': 'test_reg_{}'.format(i)}
        res = requests.post(baseurl + '/register', json=postdata)
        print(res.status_code, res.text)
        if res.status_code == 200:
            user_id_list.append(ast.literal_eval(res.text)['user_id'])
        else:
            print(res.status_code, '???')
        time.sleep(0.2 * random.randint(2, 15))

    print(user_id_list)

    time.sleep(5)

    for i in user_id_list[:90]:
        baseurl = random_fullnode_baseurl()
        param = {'id': i}
        res = requests.get(baseurl + '/merkleproof', params=param)
        print(res.status_code, res.text)
        if res.status_code == 200:
            # {'block_index': i, 'tx_index': j, 'data': block.transactions[j].to_dict(), 'merkle_proof': merkle_proof}    
            merkle_proof_list.append(ast.literal_eval(res.text))

    time.sleep(2)

    block_header_maintain()
    print(len(block_headers))

    for i in range(20):
        baseurl = random_fullnode_baseurl()
        postdata = merkle_proof_list[i]
        m_blockindex = postdata['block_index']
        mr, mh = get_merkle_root_height(m_blockindex)
        m_txindex = postdata['tx_index']
        m_data = postdata['data']
        mp = postdata['merkle_proof']
        print('verify', m_data['id'], '->', verify_merkle_proof(m_data, mp, mr, mh, m_txindex))

        res = requests.post(baseurl + '/revoke', json=postdata)
        print(res.status_code, res.text)

    for j in range(20, 30):
        baseurl = random_fullnode_baseurl()
        postdata = merkle_proof_list[j]
        m_blockindex = postdata['block_index']
        mr, mh = get_merkle_root_height(m_blockindex)
        m_txindex = postdata['tx_index']
        m_data = postdata['data']
        mp = postdata['merkle_proof']
        print('verify', m_data['id'], '->', verify_merkle_proof(m_data, mp, mr, mh, m_txindex))

        res = requests.post(baseurl + '/addtoacc', json=postdata)
        print(res.status_code, res.text)


if __name__ == '__main__':
    main()
