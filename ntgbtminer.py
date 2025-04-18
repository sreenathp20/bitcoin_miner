# ntgbtminer - vsergeev - https://github.com/vsergeev/ntgbtminer
#
# No Thrils GetBlockTemplate Bitcoin Miner
#
# This is mostly a demonstration of the GBT protocol.
# It mines at a measly 550 KH/s on my computer, but
# with a whole lot of spirit ;)
#

import subprocess
import sys


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install('pymongo')

from utils import rpc, rpc_getmininginfo, getblocktemplate, submitblock

import urllib.request
import urllib.error
import urllib.parse
import base64
import json
import hashlib
import struct
import random
import time
import os
import sys
from db import MongoDb
import random



# JSON-HTTP RPC Configuration
# This will be particular to your local ~/.bitcoin/bitcoin.conf

RPC_URL = os.environ.get("RPC_URL", "http://127.0.0.1:8332")
RPC_USER = os.environ.get("RPC_USER", "admin")
RPC_PASS = os.environ.get("RPC_PASS", "admin")

################################################################################
# Bitcoin Daemon RPC Call Wrappers
################################################################################

# def rpc_getblocktemplate():
#     out = os.popen("bitcoin-cli getblocktemplate '{\"rules\": [\"segwit\"]}'").read()
#     #print("out:", out)
#     json_out = json.loads(out)
#     #print("height:", json_out['height'])
#     return json_out






# def rpc_submitblock(block_submission, block_hash):
#     print("bitcoin-cli submitblock \""+block_hash+"\"")
#     out = os.popen("bitcoin-cli submitblock \""+block_hash+"\"").read()
#     print("out:", out)
#     json_out = json.loads(out)
    #return rpc("submitblock", [block_submission])




################################################################################
# Representation Conversion Utility Functions
################################################################################


def int2lehex(value, width):
    """
    Convert an unsigned integer to a little endian ASCII hex string.

    Args:
        value (int): value
        width (int): byte width

    Returns:
        string: ASCII hex string
    """

    return value.to_bytes(width, byteorder='little').hex()


def int2varinthex(value):
    """
    Convert an unsigned integer to little endian varint ASCII hex string.

    Args:
        value (int): value

    Returns:
        string: ASCII hex string
    """

    if value < 0xfd:
        return int2lehex(value, 1)
    elif value <= 0xffff:
        return "fd" + int2lehex(value, 2)
    elif value <= 0xffffffff:
        return "fe" + int2lehex(value, 4)
    else:
        return "ff" + int2lehex(value, 8)


def bitcoinaddress2hash160(addr):
    """
    Convert a Base58 Bitcoin address to its Hash-160 ASCII hex string.

    Args:
        addr (string): Base58 Bitcoin address

    Returns:
        string: Hash-160 ASCII hex string
    """

    table = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    hash160 = 0
    addr = addr[::-1]
    for i, c in enumerate(addr):
        hash160 += (58 ** i) * table.find(c)

    # Convert number to 50-byte ASCII Hex string
    hash160 = "{:050x}".format(hash160)

    # Discard 1-byte network byte at beginning and 4-byte checksum at the end
    return hash160[2:50 - 8]


################################################################################
# Transaction Coinbase and Hashing Functions
################################################################################


def tx_encode_coinbase_height(height):
    """
    Encode the coinbase height, as per BIP 34:
    https://github.com/bitcoin/bips/blob/master/bip-0034.mediawiki

    Arguments:
        height (int): height of the mined block

    Returns:
        string: encoded height as an ASCII hex string
    """

    width = (height.bit_length() + 7) // 8

    return bytes([width]).hex() + int2lehex(height, width)


def tx_make_coinbase(coinbase_script, address, value, height):
    """
    Create a coinbase transaction.

    Arguments:
        coinbase_script (string): arbitrary script as an ASCII hex string
        address (string): Base58 Bitcoin address
        value (int): coinbase value
        height (int): mined block height

    Returns:
        string: coinbase transaction as an ASCII hex string
    """

    # See https://en.bitcoin.it/wiki/Transaction

    coinbase_script = tx_encode_coinbase_height(height) + coinbase_script

    # Create a pubkey script
    # OP_DUP OP_HASH160 <len to push> <pubkey> OP_EQUALVERIFY OP_CHECKSIG
    pubkey_script = "76" + "a9" + "14" + bitcoinaddress2hash160(address) + "88" + "ac"

    tx = ""
    # version
    tx += "01000000"
    # in-counter
    tx += "01"
    # input[0] prev hash
    tx += "0" * 64
    # input[0] prev seqnum
    tx += "ffffffff"
    # input[0] script len
    tx += int2varinthex(len(coinbase_script) // 2)
    # input[0] script
    tx += coinbase_script
    # input[0] seqnum
    tx += "ffffffff"
    # out-counter
    tx += "01"
    # output[0] value
    tx += int2lehex(value, 8)
    # output[0] script len
    tx += int2varinthex(len(pubkey_script) // 2)
    # output[0] script
    tx += pubkey_script
    # lock-time
    tx += "00000000"

    return tx


def tx_compute_hash(tx):
    """
    Compute the SHA256 double hash of a transaction.

    Arguments:
        tx (string): transaction data as an ASCII hex string

    Return:
        string: transaction hash as an ASCII hex string
    """

    return hashlib.sha256(hashlib.sha256(bytes.fromhex(tx)).digest()).digest()[::-1].hex()


def tx_compute_merkle_root(tx_hashes):
    """
    Compute the Merkle Root of a list of transaction hashes.

    Arguments:
        tx_hashes (list): list of transaction hashes as ASCII hex strings

    Returns:
        string: merkle root as a big endian ASCII hex string
    """

    # Convert list of ASCII hex transaction hashes into bytes
    tx_hashes = [bytes.fromhex(tx_hash)[::-1] for tx_hash in tx_hashes]

    # Iteratively compute the merkle root hash
    while len(tx_hashes) > 1:
        # Duplicate last hash if the list is odd
        if len(tx_hashes) % 2 != 0:
            tx_hashes.append(tx_hashes[-1])

        tx_hashes_new = []

        for i in range(len(tx_hashes) // 2):
            # Concatenate the next two
            concat = tx_hashes.pop(0) + tx_hashes.pop(0)
            # Hash them
            concat_hash = hashlib.sha256(hashlib.sha256(concat).digest()).digest()
            # Add them to our working list
            tx_hashes_new.append(concat_hash)

        tx_hashes = tx_hashes_new

    # Format the root in big endian ascii hex
    return tx_hashes[0][::-1].hex()


################################################################################
# Block Preparation Functions
################################################################################


def block_make_header(block):
    """
    Make the block header.

    Arguments:
        block (dict): block template

    Returns:
        bytes: block header
    """

    header = b""

    # Version
    header += struct.pack("<L", block['version'])
    # Previous Block Hash
    header += bytes.fromhex(block['previousblockhash'])[::-1]
    # Merkle Root Hash
    # print("block['merkleroot']:", block['merkleroot'])
    # print("block['merkleroot'][::-1]:", block['merkleroot'][::-1])
    # print("bytes.fromhex(block['merkleroot'])[0]:", bytes.fromhex(block['merkleroot'])[0:4])
    # print("bytes.fromhex(block['merkleroot'])[::-1]:", bytes.fromhex(block['merkleroot'])[::-1])

    header += bytes.fromhex(block['merkleroot'])[::-1]
    # Time
    header += struct.pack("<L", block['curtime'])
    # Target Bits
    header += bytes.fromhex(block['bits'])[::-1]
    # Nonce
    header += struct.pack("<L", block['nonce'])
    #print("header: ", header)
    return header

def insertToDb(height, block_hash, target_hash, nonce, extranonce):
    data = {
        "height": height,
        "block_hash": block_hash,
        "target_hash": target_hash,
        "nonce": nonce,
        "extranonce": extranonce
    }
    m = MongoDb()
    m.insertMany("mined_blocks", [data])
    pass


def block_compute_raw_hash(header):
    """
    Compute the raw SHA256 double hash of a block header.

    Arguments:
        header (bytes): block header

    Returns:
        bytes: block hash
    """

    return hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1]


def block_bits2target(bits):
    """
    Convert compressed target (block bits) encoding to target value.

    Arguments:
        bits (string): compressed target as an ASCII hex string

    Returns:
        bytes: big endian target
    """

    # Bits: 1b0404cb
    #       1b          left shift of (0x1b - 3) bytes
    #         0404cb    value
    bits = bytes.fromhex(bits)
    shift = bits[0] - 3
    value = bits[1:]

    # Shift value to the left by shift
    target = value + b"\x00" * shift
    # Add leading zeros
    target = b"\x00" * (32 - len(target)) + target

    return target


def block_make_submit(block):
    """
    Format a solved block into the ASCII hex submit format.

    Arguments:
        block (dict): block template with 'nonce' and 'hash' populated

    Returns:
        string: block submission as an ASCII hex string
    """

    submission = ""

    # Block header
    submission += block_make_header(block).hex()
    # Number of transactions as a varint
    submission += int2varinthex(len(block['transactions']))
    # Concatenated transactions data
    for tx in block['transactions']:
        submission += tx['data']

    return submission


################################################################################
# Block Miner
################################################################################


def block_mine(block_template, coinbase_message, extranonce_start, address, timeout=None, debugnonce_start=False):
    """
    Mine a block.

    Arguments:
        block_template (dict): block template
        coinbase_message (bytes): binary string for coinbase script
        extranonce_start (int): extranonce offset for coinbase script
        address (string): Base58 Bitcoin address for block reward

    Timeout:
        timeout (float): timeout in seconds
        debugnonce_start (int): nonce start for testing purposes

    Returns:
        (block submission, hash rate) on success,
        (None, hash rate) on timeout or nonce exhaustion.
    """
    # Add an empty coinbase transaction to the block template transactions
    coinbase_tx = {}
    block_template['transactions'].insert(0, coinbase_tx)

    height = block_template['height']

    # Add a nonce initialized to zero to the block template
    block_template['nonce'] = 0

    # Compute the target hash
    target_hash = block_bits2target(block_template['bits'])

    # Mark our mine start time
    time_start = time.time()

    # Initialize our running average of hashes per second
    hash_rate, hash_rate_count = 0.0, 0

    # Loop through the extranonce
    #extranonce = extranonce_start
    extranonce = random.randrange(1,0xffffffff) if not extranonce_start else extranonce_start
    while extranonce <= 0xffffffff:
        # Update the coinbase transaction with the new extra nonce
        coinbase_script = coinbase_message + int2lehex(extranonce, 8)
        coinbase_tx['data'] = tx_make_coinbase(coinbase_script, address, block_template['coinbasevalue'], block_template['height'])
        coinbase_tx['hash'] = tx_compute_hash(coinbase_tx['data'])
        # print("coinbase_tx:", coinbase_tx)
        # break
        # print("block_template['transactions'][0]:", block_template['transactions'][0])
        # Recompute the merkle root
        block_template['merkleroot'] = tx_compute_merkle_root([tx['hash'] for tx in block_template['transactions']])
        #print("merkleroot:", block_template['merkleroot'])
        #break
        # Reform the block header
        block_header = block_make_header(block_template)

        # new_block_template = rpc_getblocktemplate()

        # new_height = new_block_template['height']
        # if height != new_height:
        #     return (None, None, None)

        time_stamp = time.time()

        # Loop through the nonce
        nonce = 0 if not debugnonce_start else debugnonce_start
        print(nonce)
        while nonce <= 0xffffffff:
            # Update the block header with the new 32-bit nonce
            block_header = block_header[0:76] + nonce.to_bytes(4, byteorder='little')
            
            # Recompute the block hash
            block_hash = block_compute_raw_hash(block_header)
            if nonce % 1000000 == 0:
                print("nonce: ", nonce, " extranonce: ",extranonce, " ",  block_hash.hex(), " ", target_hash.hex())
                pass
            if nonce % 5000000 == 0:
                # mininginfo = rpc_getmininginfo()

                # new_height = int(mininginfo['blocks']) + 1
                m = MongoDb()
                data = m.read("mining_block", {})
                try:
                    new_height = data[0]['current_block'] + 1
                except Exception as e:
                    new_height = None
                
                if height != new_height:
                    m = MongoDb()
                    data = m.read("blocktemplate", {})
                    if len(data) > 0:
                        d = data[0]
                        if d['height'] == height:
                            m = MongoDb()
                            m.delete("blocktemplate", {})
                    print("new_height: ", new_height)
                    return (None, None, None)

            
            # if nonce > 2:
            #     time.sleep(5)
            # Check if it the block meets the target hash
            if block_hash < target_hash:
                block_template['nonce'] = nonce
                block_template['hash'] = block_hash.hex()
                insertToDb(height, block_hash.hex(), target_hash.hex(), nonce, extranonce)
                return (block_template, hash_rate, block_hash.hex())

            # Measure hash rate and check timeout
            if nonce > 0 and nonce % 1048576 == 0:
                hash_rate = hash_rate + ((1048576 / (time.time() - time_stamp)) - hash_rate) / (hash_rate_count + 1)
                hash_rate_count += 1

                time_stamp = time.time()

                # If our mine time expired, return none
                if timeout and (time_stamp - time_start) > timeout:
                    return (None, hash_rate)

            nonce += 1
        extranonce += 1

    # If we ran out of extra nonces, return none
    return (None, hash_rate)


################################################################################
# Standalone Bitcoin Miner, Single-threaded
################################################################################


def standalone_miner(coinbase_message, address, debugnonce_start, extranonce_start):
    while True:
        block_template = getblocktemplate()
        #print("block_template:", block_template)

        mined_block = None

        while not mined_block:
            block_template = getblocktemplate()
            print("debugnonce_start: ", debugnonce_start)
            print("Mining block template, height {:d}...".format(block_template['height']))
            #def block_mine(block_template, coinbase_message, extranonce_start, address, timeout=None, debugnonce_start=False):
            mined_block, hash_rate, block_hash = block_mine(block_template, coinbase_message, extranonce_start, address, None, debugnonce_start)
            if hash_rate:
                print("    {:.4f} KH/s\n".format(hash_rate / 1000.0))

        if mined_block:
            print("Solved a block! Block hash: {}".format(mined_block['hash']))
            submission = block_make_submit(mined_block)

            #print("Submitting:", submission, "\n")
            response = submitblock(submission, block_hash, block_template["height"])
            if response is not None:
                print("Submission Error: {}".format(response))
                break


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: {:s} <coinbase message> <block reward address>".format(sys.argv[0]))
        sys.exit(1)

    standalone_miner(sys.argv[1].encode().hex(), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) )
