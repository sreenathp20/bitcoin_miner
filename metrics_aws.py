import boto3
import jmespath
import paramiko
import time
from db import MongoDb
import os


tot_prc = 0
path = '/Users/sreenath/Documents/bitcoin_code2/aws_credentials'
lines = os.popen("ls -l "+path).readlines()
for line in lines[1:]:
    file = line.split(" ")[-1][:-1]
    #os.popen("cp "+path+"/"+file+" /Users/sreenath/.aws/credentials")
    print("account: ", file)
    client = None
    session = boto3.Session(profile_name=file)
    client = session.client('ec2')
    #client = boto3.client('ec2')
    response = client.describe_instances()
    myData = None
    myData = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId, InstanceId, InstanceType, State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0]]", response)

    prc = 0
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
            inp,out,err = ssh.exec_command('ps aux | grep ntgbtminer', get_pty=True) 
            #print("out: ", out)
            l = out.readlines()
            ssh.close()
            if len(l) == 4:
                prc += 2                
            else:
                np = len(l) - 2
                prc += np
                print(f"account: {file} host: {host} {np} process(es) running")
            
    tot_prc += prc
    print(f"{len(myData)} hosts, account: {file}")

print(f"{tot_prc} process(es) running")