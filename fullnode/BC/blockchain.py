from __future__ import annotations

import json
import ast

import Utils.cryptotool as cryptotool

from BC.transaction import Transaction
from BC.block import Block_with_REV
from Utils.bloomfilter import BF
from Utils.accumulator import Accumulator, from_str, to_str
from Utils.bcdebug import *

from charm.toolbox.pairinggroup import PairingGroup


default_bcfile = 'conf/blockchain.json'

try:
    with open('conf/acc_const.json', 'r') as facc:
        acc_const = json.load(facc)

except FileNotFoundError:
    debug_error('conf/acc_const.json FileNotFoundError')
    debug_error('- - - exit(1) - - -')
    exit(1)

# bcfile -> {
#     'chain': [],
#     'acc_delta': '',
#     'acc_userset': set(),
#     'bf': '',
#     'bf_revo_map': []
# }
try:
    with open(default_bcfile, 'r') as f:
        bcfile = default_bcfile
except FileNotFoundError:
    bcfile = ''

Blocktype = Block_with_REV

class Blockchain:
    difficulty = 3
    max_transactions = 8

    def __init__(self, network, bcfile=bcfile, acc_const=acc_const):
        self.height = 0
        self.network = network
        if bcfile != '':
            bc_dict = json.load(open(bcfile, 'r'))
            self.chain = [Blocktype(block) for block in bc_dict['chain']]
            self.height = len(self.chain)

            self.bf = BF.frombase64(bc_dict['bf'])
            self.bf.revo_map = ast.literal_eval(bc_dict['bf_revo_map'])
            # debug_info('init bitarray', self.bf.bitarray)
            # debug_info('init revo_map', self.bf.revo_map)
            acc_delta = from_str(bc_dict['acc_delta'])
            acc_userset = ast.literal_eval(bc_dict['acc_userset'])

            self.acc = Accumulator(PairingGroup('MNT224'), acc_delta, acc_const['sk'], acc_const['g2'], acc_const['pk'], acc_userset)
            # debug_info('init acc_delta', acc_delta)
            # debug_info('init userset', acc_userset)
            self.bcfile = bcfile
            self.save_chain()

        else:
            self.chain = []
            self.create_genesis_block()
            self.height = 1
            self.bf = BF(1000, 0.1)
            self.acc = Accumulator(PairingGroup('MNT224'), from_str(acc_const['delta']), from_str(acc_const['sk']), from_str(acc_const['g2']), from_str(acc_const['pk']), str(acc_const['userset']))
            self.bcfile = default_bcfile
            self.save_chain()

    def create_genesis_block(self):
        genesis_block = Blocktype({'previous_hash': cryptotool.compute_hash('genesis_block')})
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]
    
    @property
    def last_three_blocks(self):
        if self.height >= 3:
            return self.chain[-3:]
        else:
            return self.chain

    def check_chain_validity(self):
        for i in range(len(self.chain)):
            if i == 0 and self.chain[i].previous_hash != cryptotool.compute_hash('genesis_block'):
                return False
            if self.chain[i].verify_block(self.chain[i - 1].hash_block_header()) == False or self.chain[i].is_valid_proof(Blockchain.difficulty) == False:
                return False
        return True
    
    def check_repetition(self, block: Blocktype):
        for tx in block.transactions:
            if self.tx_in_blockchain(tx.id, tx.txtype):
                return True
        return False

    def update_BF_Acc(self, begin_height):
        for i in range(begin_height, self.height):
            block = self.chain[i]
            for j, v in enumerate(block.transactions):
                if v.txtype == Transaction.REVOKE:
                    self.bf.add(v.id, i, j)
                elif v.txtype == Transaction.UPDATEACC:
                    self.acc.delta = from_str(v.message)
                    self.acc.userset.add(v.id)

    def append_block(self, block: Blocktype) -> bool:
        if block.index == self.last_block.index + 1 and block.verify_block(self.last_block.hash_block_header()) == True and block.is_valid_proof(Blockchain.difficulty) == True and self.check_repetition(block) == False:
                self.chain.append(block)
                self.height = self.height + 1
                self.update_BF_Acc(self.last_block.index)
                self.save_chain()
                return True
        else:
            return False

    def update_block(self, blocks: list[Blocktype], begin_height):
        if begin_height < 0 or (begin_height > 0 and begin_height != self.chain[begin_height - 1].index + 1):
            raise IndexError
        else:
            if begin_height == 0:
                current_block = Blocktype({'previous_hash': cryptotool.compute_hash('genesis_block')})
                begin_height = 1
            else:
                current_block = self.chain[begin_height - 1]
            for block in blocks:
                debug_warning('update_block', str(current_block.index))
                if block.verify_block(current_block.hash_block_header()) == True and block.is_valid_proof(
                        Blockchain.difficulty) == True:
                    current_block = block
                else:
                    debug_warning('update_block', 'ValueError')
                    raise ValueError
            self.chain = self.chain[0:begin_height] + blocks
            self.height = len(self.chain)
            self.update_BF_Acc(begin_height)
            self.save_chain()

    def get_blocks(self, begin_height=0, end_height=0):
        if begin_height < 0 or begin_height >= self.height:
            begin_height = 0
        if end_height < 0:
            return []
        if end_height == 0:
            return [block.to_dict() for block in self.chain[begin_height:]]
        elif begin_height <= end_height:
            return [block.to_dict() for block in self.chain[begin_height:end_height]]
        else:
            return []

    def get_block_headers(self, begin_height=0, end_height=0):
        if begin_height < 0 or begin_height >= self.height:
            begin_height = 0
        if end_height < 0:
            return []
        elif end_height == 0:
            return [block.to_dict_header() for block in self.chain[begin_height:]]
        elif begin_height <= end_height:
            return [block.to_dict_header() for block in self.chain[begin_height:end_height]]
        else:
            return []

    def get_block_hashes(self, begin_height=0, end_height=0):
        if begin_height < 0 or begin_height >= self.height:
            begin_height = 0
        if end_height < 0:
            return []
        if end_height == 0:
            return [(block.index, block.hash_block_header()) for block in self.chain[begin_height:]]
        elif begin_height <= end_height:
            return [(block.index, block.hash_block_header()) for block in self.chain[begin_height:end_height]]
        else:
            return []
 
    def to_dict(self):
        return {'chain': [block.to_dict() for block in self.chain]}

    def save_chain(self):
        chain = self.to_dict()
        bf_acc = {
            'acc_delta': to_str(self.acc.delta),
            'acc_userset': str(self.acc.userset),
            'bf': self.bf.tobase64(),
            'bf_revo_map': str(self.bf.revo_map)
        }
        all_bc_info = {**chain, **bf_acc}
        with open(self.bcfile, 'w') as fbc:
            json.dump(all_bc_info, fbc, indent=4)

    def get_transaction_index_by_id(self, txid):
        for i in reversed(self.chain):
            for j, value in enumerate(i.transactions):
                if value.id == txid:
                    return i.index, j
        return (-1, -1)

    def get_transaction_by_itype(self, block_index, txtype):
        txs = []
        try:
            for i, tx in enumerate(self.chain[block_index].transactions):
                if tx.txtype == txtype:
                    txs.append({'block_index': block_index, 'data': tx.to_dict(), 'merkle_proof': self.chain[block_index].get_merkle_proof(i)})
            return txs
        except IndexError:
            return []


    def tx_in_blockchain(self, tx_id, tx_type) -> bool:
        for i in reversed(self.chain):
            for j in i.transactions:
                if j.id == tx_id and j.txtype == tx_type:
                    return True
        return False
