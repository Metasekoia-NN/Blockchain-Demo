from flask import Flask, request, make_response, redirect, url_for
import requests
import random
import json
import copy

from BC.transaction import Transaction, Transaction_REG, Transaction_REV, Transaction_UBF, Transaction_UACC
from BC.block import Block_with_REV
from BC.consensus import PoW_Consensus
import Utils.timetool as timetool
from Utils.accumulator import to_str
from Utils.bcdebug import *

app = Flask(__name__)


# 最顶上的x个区块有可能因为分叉会有变动，不返回给轻节点，x值未定
confirmed_block_offset = 3

# 公钥列表
# bc_file_path = 'blockchain.json'
bc_consensus = PoW_Consensus()
bc = bc_consensus.bc
network = bc_consensus.network
with open('conf/crypto_data/pk.txt', 'r') as fpk:
    public_key = fpk.read()
with open('conf/crypto_data/sk.txt', 'r') as fsk:
    private_key = fsk.read()

try:
    with open('conf/node_config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {
        'id_base': 1,
        'id_max': 10000000
    }
    with open('conf/node_config.json', 'w') as f:
        json.dump(config, f, indent=4)

id_base, id_max = config['id_base'], config['id_max']


bf = bc.bf
acc = bc.acc
# bf_data = {}
# acc_data = {}


# 验证：直接去BC里原文比对
def verify_post_tx_data(tx_data) -> bool:
    i, j = bc.get_transaction_index_by_id(tx_data['id'])
    if i > 0 and j >= 0 and tx_data == bc.chain[i].transactions[j].to_dict():
        return True
    else:
        return False

# 初始化区块链
@app.route('/', methods=['GET'])
def index():
    global bc
    return make_response(bc.to_dict())

# GET syncinfo -> P
# 返回区块高度
@app.route('/syncinfo', methods=['GET'])
def get_syncinfo():
    global bc
    debug_warning('syncinfo', request.remote_addr)
    num = request.args.get('num', default=10, type=int)
    return make_response({'syncinfo': bc.get_block_hashes(bc.height - num)})

# GET syncblocks -> P
# 返回最新num个区块的 index, bh_hash
@app.route('/syncblocks', methods=['GET'])
def get_syncblocks():
    global bc
    num = request.args.get('num', default=0, type=int)
    if num == 0:
        return make_response({'syncblocks': bc.get_blocks()})
    else:
        return make_response({'syncblocks': bc.get_blocks(bc.height - num)})

def verify_tx_content(tx) -> bool:
    return True

def random_txsign(new_transaction):
    for _ in range(10):
        base_url = network.peer_list[random.randint(0, len(network.peer_list) - 1)]
        res = requests.post('http://{}:{}'.format(base_url['host'], base_url['port']) + '/txsign', json=new_transaction.to_dict())
        if res.status_code == 200:
            break
    
    if res.status_code == 200:
        debug_info('random_txsign', res.text)
    else:
        debug_error('random_txsign', res.status_code + 'ERROR')
    return res


# 交易签名请求
# 签够数了直接广播
@app.route('/txsign', methods=['POST'])
def post_txsign():
    global public_key, private_key
    req = request.get_json()
    try:
        if req['txtype'] == Transaction.REGISTER:
            transaction = Transaction_REG(req)
        elif req['txtype'] == Transaction.REVOKE:
            transaction = Transaction_REV(req)
        elif req['txtype'] == Transaction.UPDATEBF:
            transaction = Transaction_UBF(req)
        elif req['txtype'] == Transaction.UPDATEACC:
            transaction = Transaction_UACC(req)
        else:
            return make_response({'msg': 'Bad request'}, 400)

        if verify_tx_content(transaction) == True:
            transaction.sign_transaction(private_key, public_key)
            if transaction.verify_transaction() == True:
                network.broadcast('/newtx', transaction.to_dict())
                return make_response({'msg': 'Add tx and broadcast'})
            elif len(transaction.sign) < Transaction.threshold:
                res = random_txsign(transaction)
                return make_response({'msg': 'Send to sign successfully'})
            else:
                return make_response({'msg': 'Bad tx request'}, 400)
    except KeyError:
        return make_response({'msg': 'Bad request'}, 400)


@app.route('/newtx', methods=['POST'])
def post_newtx():
    global bc
    req = request.get_json()
    try:
        if req['txtype'] == Transaction.REGISTER:
            new_transaction = Transaction_REG(req)
        elif req['txtype'] == Transaction.REVOKE:
            new_transaction = Transaction_REV(req)
        elif req['txtype'] == Transaction.UPDATEBF:
            new_transaction = Transaction_UBF(req)
        elif req['txtype'] == Transaction.UPDATEACC:
            new_transaction = Transaction_UACC(req)
        res = bc_consensus.add_transaction(new_transaction)
        response_msg = 'Add transaction successfully' if res else 'Add transaction ERROR'
        return make_response({'msg': response_msg})
    except KeyError:
        return make_response({'msg': 'Bad request'}, 400)


@app.route('/newblock', methods=['POST'])
def post_newblock():
    global bc
    req = request.get_json()
    try:
        block = Block_with_REV(req)
        if bc.append_block(block) == True:
            bc_consensus.update_transactions_pool()
            return make_response({'msg': 'Accept the new block'})
        else:
            bc_consensus.sync_block()
            return make_response({'msg': 'Need to sync and then verify this block'})
    except KeyError:
        # debug_info('post_newblock', str(req))
        return make_response({'msg': 'Bad request'}, 400)


@app.route('/blockheaders', methods=['GET'])
def get_block_headers():
    global bc
    begin_height = request.args.get('begin_height', default=0, type=int)

    return make_response({'block_headers': bc.get_block_headers(begin_height, bc.height - confirmed_block_offset)})


@app.route('/merkleproof', methods=['GET'])
def get_merkle_proof():
    global bc
    user_id = request.args.get('id', default=0, type=int)
    if user_id <= 0:
        return make_response({'msg': 'Bad request'}, 400)
    else:
        i, j = bc.get_transaction_index_by_id(user_id)
        block = bc.chain[i]
        merkle_proof = block.get_merkle_proof(j)
        # tx = block.transactions[j]
        # user_pk = tx.publickey
        return make_response({'block_index': i, 'tx_index': j, 'data': block.transactions[j].to_dict(), 'merkle_proof': merkle_proof})


@app.route('/bf', methods=['GET'])
def get_bf():
    global bc
    block_index = request.args.get('index', default=-1, type=int)
    if block_index == -1:
        pass
    else:
        return make_response({'bf_data': bc.get_transaction_by_itype(block_index, Transaction.REVOKE)})


@app.route('/acc', methods=['GET'])
def get_acc():
    global bc
    block_index = request.args.get('index', default=-1, type=int)
    if block_index == -1:
        pass
    else:
        return make_response({'acc_data': bc.get_transaction_by_itype(block_index, Transaction.UPDATEACC)})


@app.route('/register', methods=['POST'])
def post_register():
    global public_key, private_key, id_base
    req = request.get_json()
    try:
        user_pk = req['pk']
        user_msg = req['message'] if req['message'] != '' else 'Add a user'
        user_id = id_base
        id_base = id_base + 1
        config['id_base'] = id_base
        with open('conf/node_config.json', 'w') as f:
            json.dump(config, f, indent=4)
        new_transaction = Transaction_REG({'id': user_id, 'message': user_msg,
                    'publickey': '{}'.format(user_pk), 'timestamp': timetool.time2strtime(timetool.get_current_time()),
                    'starttime': timetool.date2strdate(timetool.next_day(timetool.get_current_date())),
                    'endtime': timetool.date2strdate(timetool.next_year(timetool.get_current_date()))})
        if verify_tx_content(new_transaction) == True:
            new_transaction.sign_transaction(private_key, public_key)
            random_txsign(new_transaction)
            return make_response({'msg': 'Successfully processing... Your ID is {}. Please wait consensus...'.format(user_id), 'user_id': user_id})
        else:
            return make_response({'msg': 'Bad register request'}, 400)
    except KeyError:
        return make_response({'msg': 'Bad request'}, 400)


@app.route('/revoke', methods=['POST'])
def post_revoke():
    global public_key, private_key, bf, acc
    req = request.get_json()
    try:
        user_tx = req['data']
        if verify_post_tx_data(user_tx) == False:
            return make_response({'msg': 'Bad request -> verify id failed'}, 400)

        tx_i, tx_j = bc.get_transaction_index_by_id(user_tx['id'])
        bf_temp = copy.deepcopy(bf)
        bf_temp.add(user_tx['id'], tx_i, tx_j)

        new_transaction_rev = Transaction_REV({'id': user_tx['id'], 'message': bf_temp.tobase64(),
                    'publickey': '{}'.format(user_tx['publickey']), 'timestamp': timetool.time2strtime(timetool.get_current_time())})
        
        if verify_tx_content(new_transaction_rev) == True:
            new_transaction_rev.sign_transaction(private_key, public_key)
            random_txsign(new_transaction_rev)
        else:
            return make_response({'msg': 'Bad register request -> verify revo tx failed'}, 400)

        if user_tx['id'] in acc.userset:
            acc_temp = copy.deepcopy(acc)
            acc_temp.userdel(user_tx['id'])

            new_transaction_updateacc = Transaction_UACC({'id': user_tx['id'], 'message': to_str(acc_temp.delta),
                    'publickey': '{}'.format(user_tx['publickey']), 'timestamp': timetool.time2strtime(timetool.get_current_time())})
            new_transaction_updateacc.sign_transaction(private_key, public_key)
            random_txsign(new_transaction_updateacc)
        return make_response({'msg': 'Revoke {} successfully'.format(user_tx['id'])}, 200)

    except KeyError:
        return make_response({'msg': 'Bad request -> KeyError'}, 400)


@app.route('/update', methods=['POST'])
def post_update():
    global public_key, private_key, bf
    req = request.get_json()
    try:
        user_tx = req['data']
        if verify_post_tx_data(user_tx) == False:
            return make_response({'msg': 'Bad request'}, 400)
        user_update_type = req['type']
        # 修改内容
        if user_update_type == 'modify':
            user_pk_new = req['pk_new']
            user_msg = req['message'] if req['message'] != '' else 'modify a user'
            user_id = id_base
            id_base = id_base + 1
            config['id_base'] = id_base
            with open('conf/node_config.json', 'w') as f:
                json.dump(config, f, indent=4)
            new_transaction_reg = Transaction_REG({'id': user_id, 'message': user_msg,
                        'publickey': '{}'.format(user_pk_new), 'timestamp': timetool.time2strtime(timetool.get_current_time()),
                        'starttime': timetool.date2strdate(timetool.next_day(timetool.get_current_date())),
                        'endtime': timetool.date2strdate(timetool.next_year(timetool.get_current_date()))})
            
            tx_i, tx_j = bc.get_transaction_index_by_id(user_tx['id'])
            bf_temp = bf.copy()
            bf_temp.add(user_tx['id'], tx_i, tx_j)

            new_transaction_rev = Transaction_REV({'id': user_tx['id'], 'message': bf_temp.tobase64(),
                    'publickey': '{}'.format(user_tx['publickey']), 'timestamp': timetool.time2strtime(timetool.get_current_time())})
            if verify_tx_content(new_transaction_rev) == True:
                new_transaction_reg.sign_transaction(private_key, public_key)
                new_transaction_rev.sign_transaction(private_key, public_key)
                random_txsign(new_transaction_reg)
                random_txsign(new_transaction_rev)
                return make_response({'msg': 'Successfully processing... Your new ID is {}. Please wait consensus...'.format(user_id), 'user_id': user_id})

        # 延长时间
        elif user_update_type == 'extend':
            user_id = id_base
            id_base = id_base + 1
            config['id_base'] = id_base
            with open('conf/node_config.json', 'w') as f:
                json.dump(config, f, indent=4)
            new_transaction = Transaction_REG({'id': user_id, 'message': 'extend valid time',
                        'publickey': '{}'.format(user_tx['publickey']), 'timestamp': timetool.time2strtime(timetool.get_current_time()),
                        'starttime': timetool.date2strdate(timetool.next_day(timetool.strdate2date(user_tx['endtime']))),
                        'endtime': timetool.date2strdate(timetool.next_year(timetool.strdate2date(user_tx['endtime'])))})
            if verify_tx_content(new_transaction) == True:
                new_transaction.sign_transaction(private_key, public_key)
                random_txsign(new_transaction)
                return make_response({'msg': 'Successfully processing... Your next ID is {}. Please wait consensus...'.format(user_id), 'user_id': user_id})
        else:
            return make_response({'msg': 'Bad request'}, 400)
    except KeyError:
        return make_response({'msg': 'Bad request'}, 400)


def id_is_revoked(user_id) -> bool:
    return bf.element_in_bf(user_id)


@app.route('/addtoacc', methods=['POST'])
def post_add_to_acc():
    global bf
    req = request.get_json()
    try:
        user_tx = req['data']
        if user_tx['id'] in bf and id_is_revoked(user_tx['id']) == False:
            witness = acc.useradd(user_tx['id'])
            return make_response({'acc_witness': to_str(witness)})
        else:
            return make_response({'msg': 'You do not need to add to acc'}, 201)
    except KeyError:
        return make_response({'msg': 'Bad request'}, 400)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
