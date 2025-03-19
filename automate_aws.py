import boto3
import jmespath
import paramiko
import time
from db import MongoDb

client = boto3.client('ec2')
response = client.describe_instances()

myData = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId, InstanceId, InstanceType, State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0]]", response)

pass

m = MongoDb('localhost')
extranonce = m.read('extranonce', {})
if len(extranonce) > 0:
    extranonce = extranonce['extranonce']
else:
    extranonce = 0

for md in myData:
    if md[8] != 'b_core':
        host = md[6]
        keyfilename = '/Users/sreenath/Downloads/b000001.pem'
        k = paramiko.RSAKey.from_private_key_file(keyfilename)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        user = 'ubuntu'
        ssh.connect(hostname=host, username=user, pkey=k)
        sleeptime = 0.001
        ssh.exec_command('sudo su \n mkdir btc ') 
        # chan = ssh_transp.open_session()
        ssh.exec_command('sudo su \n cd btc \n git clone https://github.com/sreenathp20/bitcoin_miner.git') 
        # chan = ssh_transp.open_session()
        ssh.exec_command('sudo su \n apt update \n yes | sudo apt install python3.12-venv \n cd btc \n mkdir logs \n python3 -m venv venv \n source venv/bin/activate') 

        ssh.exec_command('sudo su \n /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 '+extranonce+' > /home/ubuntu/btc/logs/1.log &') 

        ssh.exec_command('sudo su \n /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 '+extranonce+' > /home/ubuntu/btc/logs/2.log &') 

        extranonce += 1000


ssh.close()

m = MongoDb('localhost')
data = {
    "extranonce": extranonce
}
extranonce = m.insertMany('extranonce', {})