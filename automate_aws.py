import boto3
import jmespath
import paramiko
import time

client = boto3.client('ec2')
response = client.describe_instances()

myData = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId, InstanceId, InstanceType, State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0]]", response)

pass

def execute(outdata,errdata):
    while True:  # monitoring process
        # Reading from output streams
        while chan.recv_ready():
            outdata += str(chan.recv(1000))
        while chan.recv_stderr_ready():
            errdata += str(chan.recv_stderr(1000))
        # if chan.exit_status_ready():  # If completed
        #     break
        time.sleep(sleeptime)
    return outdata,errdata

host = myData[2][6]
keyfilename = '/Users/sreenath/Downloads/b000001.pem'
k = paramiko.RSAKey.from_private_key_file(keyfilename)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
user = 'ubuntu'
ssh.connect(hostname=host, username=user, pkey=k)
sleeptime = 0.001
outdata, errdata = '', ''
# ssh_transp = ssh.get_transport()
# chan = ssh_transp.open_session()
# chan.setblocking(0)
ssh.exec_command('sudo su \n mkdir btc ') 
# chan = ssh_transp.open_session()
ssh.exec_command('sudo su \n cd btc \n git clone https://github.com/sreenathp20/bitcoin.git') 
# chan = ssh_transp.open_session()
ssh.exec_command('sudo su \n apt update \n yes | sudo apt install python3.12-venv \n cd btc \n python3 -m venv venv \n source venv/bin/activate') 

#chan = ssh_transp.open_session()
#stdin,stdout,stderr=ssh.exec_command('yes | sudo apt install python3.12-venv') 
#stdin,stdout,stderr=ssh.exec_command('sudo su \n mkdir one \n cd one \n mkdir two') 
#stdout=stdout.readlines()
#print(stdout.read().decode('ascii'))
#outdata,errdata = execute(outdata,errdata)
# chan.exec_command('sudo su')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('mkdir btc')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('cd btc')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('apt update')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('apt install python3.12-venv')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('python3 -m venv venv')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('source venv/bin/activate')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('git clone https://github.com/sreenathp20/bitcoin.git')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('cd bitcoin/')
# #outdata,errdata = execute(outdata,errdata)
# chan.exec_command('pip install pymongo')
#outdata,errdata = execute(outdata,errdata)


ssh.close()

print(outdata)
print(errdata)
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo su')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('mkdir btc')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('cd btc')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('apt update')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('apt install python3.12-venv')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('python3 -m venv venv')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('source venv/bin/activate')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('git clone https://github.com/sreenathp20/bitcoin.git')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('cd bitcoin/')
# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('pip install pymongo')