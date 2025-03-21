import boto3
import jmespath
import paramiko
import time
from db import MongoDb
import os


m = MongoDb('localhost')
extranonce = m.read('extranonce', {})
if len(extranonce) > 0:
    extranonce = extranonce[0]['extranonce']
else:
    extranonce = 0

m = MongoDb('localhost')
processed = m.read('processed', {})

if len(processed) > 0:
    processed = processed[0]['processed']
else:
    processed = []

path = '/Users/sreenath/Documents/bitcoin_code2/aws_credentials'
lines = os.popen("ls -l "+path).readlines()
for line in lines[1:]:
    file = line.split(" ")[-1][:-1]
    #os.popen("cp "+path+"/"+file+" /Users/sreenath/.aws/credentials")
    pass
    if file in processed:
        continue
    processed.append(file)
    session = boto3.Session(profile_name=file)
    client = session.client('ec2')
    #client = boto3.client('ec2')
    response = client.describe_instances()

    myData = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId, InstanceId, InstanceType, State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0]]", response)


    for md in myData:
        if md[8] != 'b_core':
            host = md[6]
            print("host: ", host)
            keyfilename = '/Users/sreenath/Downloads/'+file+'.pem'
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
            ssh.exec_command('sudo su \n sudo apt update \n yes | sudo apt install python3.12-venv \n cd btc \n mkdir logs \n python3 -m venv venv \n source venv/bin/activate \n /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 '+str(extranonce)+' > /home/ubuntu/btc/logs/1.log & \n /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 '+str(extranonce+1000)+' > /home/ubuntu/btc/logs/2.log &') 

            # ssh.exec_command('sudo su \n /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 '+str(extranonce)+' > /home/ubuntu/btc/logs/1.log &') 
            # extranonce += 1000
            # ssh.exec_command('sudo su \n /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 '+str(extranonce)+' > /home/ubuntu/btc/logs/2.log &') 

            extranonce += 2000
    m = MongoDb('localhost')
    m.delete("processed", {})

    m = MongoDb('localhost')
    data = {
        "processed": processed
    }
    m.insertMany('processed', [data])

    ssh.close()

m = MongoDb('localhost')
m.delete("extranonce", {})

m = MongoDb('localhost')
data = {
    "extranonce": extranonce
}
extranonce = m.insertMany('extranonce', [data])