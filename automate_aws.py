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
ssh.exec_command('sudo su \n apt update \n yes | sudo apt install python3.12-venv \n cd btc \n mkdir logs \n python3 -m venv venv \n source venv/bin/activate \n /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 > ../logs/1.log &') 


ssh.exec_command('sudo su \n sudo /home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py sreenath 1DpMnorqAqtuEuZhD3tNujL83QhD9qEvG4 0 > /home/ubuntu/btc/logs/1.log &') 

_stdin, stdout, _stderr = ssh.exec_command("/home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py")
for line in iter(lambda: stdout.readline(2048).rstrip(), ""):
    print(line)

ssh.close()

try:
    with paramiko.SSHClient() as client:
            client.load_system_host_keys()
            client.connect(host, username=user, key_filename=keyfilename)
            _stdin, stdout, _stderr = client.exec_command("/home/ubuntu/btc/venv/bin/python /home/ubuntu/btc/bitcoin_miner/ntgbtminer.py")
            for line in iter(lambda: stdout.readline(2048).rstrip(), ""):
                print(line)
            stderr = _stderr.read()
            if len(stderr) > 0:
                raise SystemExit(stderr)
except Exception as err:
        raise SystemExit("There was an issue with ssh command: {}".format(err))