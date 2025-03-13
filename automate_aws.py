import boto3
import jmespath
import paramiko
import time

client = boto3.client('ec2')
response = client.describe_instances()

myData = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId, InstanceId, InstanceType, State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0]]", response)

pass

host = myData[2][6]
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
ssh.exec_command('sudo su \n apt update \n yes | sudo apt install python3.12-venv \n cd btc \n python3 -m venv venv \n source venv/bin/activate') 



ssh.close()