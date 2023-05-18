import ast
import traceback

from BC.transaction import Transaction
from BC.block import Block_with_REV
from BC.blockchain import Blockchain
from BC.p2pnetwork import P2PNetwork
from Utils.bcdebug import *
import Utils.cryptotool as cryptotool

Blocktype = Block_with_REV


class PoW_Consensus:
    def __init__(self):
        self.network = P2PNetwork()
        self.bc = Blockchain(self.network)
        self.unconfirmed_transactions = []
        # self.sync_block()

    def sync_block(self):
        syncinfos = self.network.get_broadcast('/syncinfo', params={'num': 10})

        legal_urls = {}  # 哈希表

        for k, v in syncinfos.items():
            if v['syncinfo'][-1][0] >= self.bc.height:
                if (v['syncinfo'][-1][0], cryptotool.compute_hash(str(v))) in legal_urls:
                    legal_urls[(v['syncinfo'][-1][0], cryptotool.compute_hash(str(v)))].append(k)
                else:
                    legal_urls[(v['syncinfo'][-1][0], cryptotool.compute_hash(str(v)))] = [k]
        
        legal_url_list_t = [i[1] for i in sorted(legal_urls.items(), key=lambda x: (x[0][0], len(x[1])), reverse=True)]
        legal_url_list = []
        for i in legal_url_list_t:
            for j in i:
                legal_url_list.append(j)
        debug_warning('sync_block legal_url_list', str(legal_url_list))

        for i in legal_url_list:
            res = self.network.get_request(i + '/syncblocks', params={'num': 10})
            if res.status_code == 200:
                syncinfo = ast.literal_eval(res.text)['syncblocks']
                debug_warning('sync_block syncinfo {}'.format(i), syncinfo[0])

                blocks = [Blocktype(b) for b in syncinfo]
                begin_height = syncinfo[0]['index']
                debug_warning('sync_block begin_height', begin_height)

                try:
                    self.bc.update_block(blocks, begin_height)
                    debug_warning('sync_block syncinfo {}'.format(i), 'success')
                    self.bc.save_chain()
                    self.update_transactions_pool(empty=True)
                    return
                except (IndexError, ValueError):
                    res_all = self.network.get_request(i + '/syncblocks', params={'num': -1})
                    debug_warning('sync_block syncinfo {}'.format(i), 'all blocks')
                    if res_all.status_code == 200:
                        all_syncinfo = ast.literal_eval(res_all.text)['syncblocks']
                        debug_warning('sync_block syncinfo {}'.format(i), 'all_syncinfo')
                        all_blocks = [Blocktype(b) for b in all_syncinfo]
                        debug_warning('sync_block', all_blocks[1].to_dict())
                        try:
                            self.bc.update_block(all_blocks[1:], 0)
                            self.bc.save_chain()
                            self.update_transactions_pool(empty=True)
                            return
                        except (IndexError, ValueError):
                            pass

    def check_tx_in_chain(self, tx) -> bool:
        try:
            tx_id = tx.id
            tx_type = tx.txtype
            return self.bc.tx_in_blockchain(tx_id, tx_type)
        except KeyError:
            return False

    def add_transaction(self, transaction):
        if transaction.verify_transaction() == True and self.check_tx_in_chain(transaction) == False:
            self.unconfirmed_transactions.append(transaction.to_dict())

            if len(self.unconfirmed_transactions) >= Blockchain.max_transactions:
                try:
                    new_block = self.mine()
                    self.broadcast_block(new_block)
                except ValueError:
                    debug_error('add_transaction', 'ValueError')
                    return False
            return True

        else:
            return False

    def update_transactions_pool(self, empty=False):
        if empty == False:
            # debug_info('update_transactions_pool', 'empty = False')
            last_three_blocks = self.bc.last_three_blocks
            for block in last_three_blocks:
                for tx in block.transactions:
                    # debug_info('update_transactions_pool', tx.id)
                    i = 0
                    while i < len(self.unconfirmed_transactions):
                        if self.unconfirmed_transactions[i]['id'] == tx.id:
                            # debug_info('update_transactions_pool', 'delete ' + str(tx.id))
                            self.unconfirmed_transactions.pop(i)
                            break
                        else:
                            i = i + 1
        else:
            debug_info('update_transactions_pool', 'empty = True')
            self.unconfirmed_transactions = []

    def proof_of_work(self, block: Blocktype):
        block.nonce = 0
        current_height = self.bc.height

        computed_hash = block.hash_block()
        while not computed_hash.startswith('0' * Blockchain.difficulty) and current_height == self.bc.height:
            block.nonce += 1
            computed_hash = block.hash_block()

        if current_height < self.bc.height:
            debug_error('proof_of_work', 'current_height < self.bc.height ERROR')
            raise ValueError

    def check_revo(self):
        temp1 = 0  # BF
        temp2 = 0  # Acc
        for tx in self.unconfirmed_transactions:
            if tx['txtype'] == Transaction.REVOKE:
                temp1 = 2
            elif tx['txtype'] == Transaction.UPDATEACC:
                temp2 = 1
        debug_warning('check_revo', 'BF: {}, Acc: {}'.format(temp1, temp2))
        return temp1 + temp2

    def mine(self):
        if len(self.unconfirmed_transactions) == 0:
            raise ValueError

        last_block = self.bc.last_block

        self.update_transactions_pool()

        new_block = Blocktype({'index': last_block.index + 1, 'previous_hash': last_block.hash_block_header(),
                               'revo_flag': self.check_revo(), 'transactions': self.unconfirmed_transactions})

        try:
            new_block.merkle_root, new_block.merkle_height = new_block.compute_merkle_root_height()
            self.proof_of_work(new_block)
            if self.bc.append_block(new_block) != True:
                self.sync_block()
                raise ValueError
            else:
                self.update_transactions_pool()
                return new_block

        except (ValueError, AttributeError):
            self.unconfirmed_transactions = []
            raise ValueError

    def broadcast_block(self, block: Blocktype):
        self.network.broadcast('/newblock', block.to_dict())

    def broadcast_transaction(self, transaction):
        self.network.broadcast('/newtx', transaction.to_dict())
