import time
from utils import rpc, rpc_getmininginfo, rpc_getblocktemplate, rpc_submitblock
from db import MongoDb

while True:
    minfo = rpc_getmininginfo()
    m = MongoDb()
    d = m.read("submitblock", {"height": minfo['blocks']})
    if len(d) > 0:
        block_submission = d[0]["block_submission"]
    else:
        block_submission = None
    if block_submission:
        rpc_submitblock(block_submission, minfo['blocks'])

    

    time.sleep(3)
    