import time
from utils import rpc, rpc_getmininginfo, rpc_getblocktemplate
from db import MongoDb

while True:
    minfo = rpc_getmininginfo()
    m = MongoDb()
    data = m.read("mining_block", {})
    try:
        dbinfo = data[0]['current_block']
    except Exception as e:
        dbinfo = None
    if not dbinfo or dbinfo != minfo['blocks']:
        rpc_getblocktemplate()
        m = MongoDb()
        m.delete("mining_block", {})
        m = MongoDb()
        m.insertMany("mining_block", [{"current_block": minfo['blocks']}])
        m = MongoDb()
        data = m.read("mining_block", {})
        dbinfo = data[0]['current_block']
        print("new block minging: ", dbinfo)

    time.sleep(10)
    