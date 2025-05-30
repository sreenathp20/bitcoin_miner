import os, json, random, base64
import urllib.request
import urllib.error
import urllib.parse
from db import MongoDb

RPC_URL = os.environ.get("RPC_URL", "http://127.0.0.1:8332")
RPC_USER = os.environ.get("RPC_USER", "admin")
RPC_PASS = os.environ.get("RPC_PASS", "admin")

################################################################################
# Bitcoin Daemon JSON-HTTP RPC
################################################################################


def rpc(method, params=None):
    """
    Make an RPC call to the Bitcoin Daemon JSON-HTTP server.

    Arguments:
        method (string): RPC method
        params: RPC arguments

    Returns:
        object: RPC response result.
    """
    try:
        print("RPC_URL:", RPC_URL)
        print("RPC_USER:", RPC_USER)
        print("RPC_PASS:", RPC_PASS)
        rpc_id = random.getrandbits(32)
        data = json.dumps({"id": rpc_id, "method": method, "params": params}).encode()
        auth = base64.encodebytes((RPC_USER + ":" + RPC_PASS).encode()).decode().strip()

        request = urllib.request.Request(RPC_URL, data, {"Authorization": "Basic {:s}".format(auth)})
        with urllib.request.urlopen(request) as f:
            response = json.loads(f.read())
    except:
        return rpc(method, params)

    if response['id'] != rpc_id:
        raise ValueError("Invalid response id: got {}, expected {:u}".format(response['id'], rpc_id))
    elif response['error'] is not None:
        raise ValueError("RPC error: {:s}".format(json.dumps(response['error'])))

    return response['result']


def rpc_getmininginfo():
    try:  
        out = os.popen("bitcoin-cli -rpcuser="+RPC_USER+" -rpcpassword="+RPC_PASS+" getmininginfo").read()
        #print("out:", out)
        json_out = json.loads(out)
    except:
        return rpc_getmininginfo()
    return json_out

def rpc_getblocktemplate():
    try:
        out = rpc("getblocktemplate", [{"rules": ["segwit"]}])
        #out["_id"] = 1        
        in_data = [out]
        m = MongoDb()
        m.delete("blocktemplate", {})
        m = MongoDb()
        m.insertMany("blocktemplate", in_data)
        return out
    except ValueError:
        return {}
    
def getblocktemplate():
    try:
        m = MongoDb()
        data = m.read("blocktemplate", {})
        if len(data) > 0:
            return data[0]
    except ValueError:
        return {}
    
def rpc_submitblock(block_submission, height):
    res = rpc("submitblock", [block_submission])
    data = {
        "block_submission_result": res,
        "height": height
    }
    m = MongoDb()
    m.insertMany("submitblock_result", [data])

def submitblock(block_submission, block_hash, height):
    data = {
        "block_submission": block_submission,
        "height": height
    }
    m = MongoDb()
    m.insertMany("submitblock", [data])