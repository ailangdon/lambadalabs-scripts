import sys
import time
import os
import requests

baseurl = "https://cloud.lambdalabs.com/api/v1"
API_KEY_LAMBDA_LABS="secret_lambdalabskey_9c4645a8cd6b4c4586f6c665f5232391.aKSRydiSYT6OGVrYT4pIFup94uGvDkhx" #os.environ['API_KEY_LAMBDA_LABS']
GPU_TYPE="gpu_1x_a10"

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

def getRunningInstances():
    data = http_get_data("/instances")
    return data
    
def waitUntilNoInstanceIsRunning():
    count = 0
    starttime = time.time()
    while count < 100:   
        time.sleep(10)
        print("Stopping for "+str(time.time()-starttime)+" seconds.")
        instances = getRunningInstances()
        if len(instances) == 0:
            print("All instances have been terminated. There are no more instances available in the account.")
            return
    print("Waited more than 1000 seconds for the instance to start up, but it didn't start up yet. Please check status manually.")
    sys.exit(3)

def stopAllInstances():
    instances = getRunningInstances()
    if len(instances) == 0:
        print("There are no instances in this account.")
        sys.exit(0)

    instanceIds = []
    for inst in instances:
        instanceIds.append(inst["id"])        
        
    print("Terminating "+str(len(instances))+" instance"+("s" if len(instances)>1 else "")+".")
    data = { 'instance_ids': instanceIds }
    http_post('/instance-operations/terminate', data)

    waitUntilNoInstanceIsRunning()

if __name__ == "__main__":
    print(sys.version)
    stopAllInstances()