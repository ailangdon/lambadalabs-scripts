import sys
import time
import requests
import os
import json
import paramiko

baseurl = "https://cloud.lambdalabs.com/api/v1"
API_KEY_LAMBDA_LABS=os.environ['API_KEY_LAMBDA_LABS']
GPU_TYPE = "gpu_1x_a10" # default can be overwritten by command line parameter

def http_get_data(url):
    response = requests.get(baseurl+url, auth=(API_KEY_LAMBDA_LABS,''))
    if response.status_code == 200:
        return response.json()["data"]
    print("REST call to "+url+" returned status code: "+response.status_code)
    sys.exit(1)

def http_post(url, body):    
    response = requests.post(baseurl+url, json=body, auth=(API_KEY_LAMBDA_LABS,''))
    if response.status_code == 200:
        return response.json()["data"]
    print("REST call to "+url+" returned status code: "+str(response.status_code))
    print("Please check your account")
    sys.exit(1)

# get available types
def getAvailableTypes():
    data = http_get_data("/instance-types")    
    availableGPUs = []
        
    for key, value in data.items():
        if len(value['regions_with_capacity_available'])>0:
            availableGPUs.append(value)
    return availableGPUs    

def whereIsInstanceAvailable(requestedGPUType):
    allAvailableTypes = getAvailableTypes()
    for gputype in allAvailableTypes:
        if gputype["instance_type"]["name"] == requestedGPUType:
            return gputype["regions_with_capacity_available"]
    return []

def getFirstAvailableSshKey():    
    data = http_get_data("/ssh-keys")
    if len(data) > 0:
        return data[0]["name"]
    return None

def getRunningInstances():
    data = http_get_data("/instances")
    return data
    
def waitTillActive(instanceId):
    print("Waiting for instance "+instanceId+" to become available.")
    starttime=time.time()
    count = 0
    while count < 100:
        time.sleep(10)
        data = getRunningInstances()
        instanceFound = False
        for instance in data:
            if instance["id"] == instanceId:
                print("Instance status "+instance["status"]+" startup duration "+str(time.time()-starttime)+" seconds")
                instanceFound = True
                if instance["status"] == "active":
                    print("Machine has been started and is active.")
                    return
        if not instanceFound:
            print("While waiting for the instance to start, the instance appears not to be in the list anymore. Thus canceling waiting")
            sys.exit(6)
        count += 1
    print("Waited more than 1000 seconds for the instance to start up, but it didn't start up yet. Please check status manually.")
    sys.exit(7)

def startInstance(gputype, region, ssh_key):
    body =  {
        "region_name": region,
        "instance_type_name": gputype,
        "ssh_key_names": [ssh_key],
        "quantity": 1
    }
    data = http_post("/instance-operations/launch",body) 
    instance_id = data["instance_ids"][0]   
    print("Instance start initiated. Instance Id: "+instance_id)
    return instance_id

def startNewInstance(gputype):
    runningInstances = getRunningInstances()
    if len(runningInstances)>0:
        print("Instances are already running.")        
        print(json.dumps(runningInstances, indent=4))
        sys.exit(1)

    ssh_key = getFirstAvailableSshKey()
    if not ssh_key:
        print("No SSH key is configured in lambda labs. An instance cannot be started automatically. Please setup an ssh key first.")
        sys.exit(2)
    
    regions = whereIsInstanceAvailable(gputype)
    if len(regions) > 0:        
        return startInstance(gputype, regions[0]["name"], ssh_key)
    else:
        print(gputype+" GPUs are not available in any region at the moment. Please try again later.")
        sys.exit(3)

def getInstanceInformation(instance_id):
    data = http_get_data("/instances/"+instance_id)
    return data

def initialSetupOnMachine(instance):
    ip=instance["ip"]
    sshkey = instance["ssh_key_names"][0]
    username= "ubuntu"

    # Load the PEM file
    pem_file_name = os.path.expanduser(f"~/.ssh/{sshkey}.pem")
    pkey=paramiko.RSAKey.from_private_key_file(pem_file_name)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # add ubuntu user to docker group    
    client.connect(username=username, hostname=ip, pkey=pkey)    
    _stdin, _stdout, _stderr = client.exec_command('sudo usermod -aG docker ubuntu')
    if _stdout.channel.recv_exit_status() != 0:
        print("Could not add user to group on remote instance.")
        sys.exit(8)    
    client.close()

    # copy init file to instance
    client.connect(username=username, hostname=ip, pkey=pkey)
    sftp = client.open_sftp()
    sftp.put('init.sh','init.sh')
    sftp.close()
    client.close()

    # run init
    client.connect(username=username, hostname=ip, pkey=pkey)    
    _stdin, _stdout, _stderr = client.exec_command("chmod +x ~/init.sh")
    if _stdout.channel.recv_exit_status() != 0:
        print("Could not change init.sh to executable.")
        sys.exit(9)
    _stdin, _stdout, _stderr = client.exec_command("~/init.sh")
    if _stdout.channel.recv_exit_status() != 0:
        print("Could not execute init.sh on remote instance.")
        sys.exit(10)    
    client.close()

def determineGPUType():
    global GPU_TYPE    
    if len(sys.argv) > 1:
        GPU_TYPE = sys.argv[1]
        if not GPU_TYPE in ["gpu_1x_a10","gpu_1x_a100","gpu_1x_p100","gpu_1x_v100","gpu_2x_a10","gpu_2x_a100","gpu_2x_p100","gpu_2x_v100","gpu_4x_a10","gpu_4x_a100","gpu_4x_p100","gpu_4x_v100"]:
            print(f'Unknown GPU_TYPE = {GPU_TYPE} but still trying to continue to setup the instance.')
    print("GPU type: "+GPU_TYPE)

if __name__ == "__main__":
    determineGPUType()
    instance_id = startNewInstance(GPU_TYPE)
    waitTillActive(instance_id)    
    instance = getInstanceInformation(instance_id)
    print("Instance started:")
    print(json.dumps(instance, indent=4))
    initialSetupOnMachine(instance)