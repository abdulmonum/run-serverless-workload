import asyncio
import time
import random
import subprocess
import threading
import sys
import requests
import numpy as np
from aiohttp import ClientSession, BasicAuth
import json

def generate_poisson_events(rate, time_duration):
    num_events = np.random.poisson(rate * time_duration)
    event_times = np.sort(np.random.uniform(0, time_duration, num_events))
    inter_arrival_times = np.diff(event_times)
    return num_events, event_times, inter_arrival_times


async def make_api_calls(api_endpoint, duration):
    c = 0
    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time) < duration:
        async with ClientSession() as session:
            async with session.get(api_endpoint, ssl=False) as response:
                resp = await response.text()
                interarrival_time = generate_interarrival_time(rate_per_second)
                await asyncio.sleep(interarrival_time)
        c += 1
    return c
#Flag to indicate end of experiment
measurement_ended = threading.Event()

# Function to generate interarrival times
def generate_interarrival_time(rate):
    return random.expovariate(rate)

# Function to make asynchronous API calls
async def make_async_api_call(session, api_endpoint):
    async with session.post(api_endpoint, ssl=False) as response:
        #await asyncio.sleep(inter_arrival_time)
        return await response.json()

async def make_api_call(session, api_endpoint):
    async with session.get(api_endpoint, ssl=False) as response:
        #return await response.text()
        pass

async def execute_workload(inter_arrival_times, api_endpoint, auth):
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers, auth=auth) as session:
        tasks = []
        #tasks = [asyncio.ensure_future(make_async_api_call(session, iat, api_endpoint)) for iat in inter_arrival_times]
        for iat in inter_arrival_times:
            task = asyncio.ensure_future(make_async_api_call(session, api_endpoint))
            tasks.append(task)
            await asyncio.sleep(iat)
        
        responses = await asyncio.gather(*tasks)
    
    return responses

# Function to run the workload
async def run_workload(duration, api_endpoint, auth):
    count = 0
    tasks = []
    headers = {"Content-Type": "application/json"}
    start_time = time.time()
    async with ClientSession(headers=headers, auth=BasicAuth(auth[0], auth[1])) as session:
        while (time.time() - start_time) < duration:
            interarrival_time = generate_interarrival_time(rate_per_second)
            #print(interarrival_time)
            task = asyncio.ensure_future(make_async_api_call(session, api_endpoint))            
            tasks.append(task)
            await asyncio.sleep(interarrival_time)
            count += 1
        end_time = time.time()
        responses = await asyncio.gather(*tasks)
    return count, start_time, end_time, responses
# Function to execute the shell command

def execute_shell_command(shell_command_1, shell_command_2, interval):
    while not measurement_ended.is_set():
        process1 = subprocess.Popen(shell_command_1, shell=True)
        process1.wait()
        process2 = subprocess.Popen(shell_command_2, shell=True)
        process2.wait()
        measurement_ended.wait(interval)
        
def make_request(duration, api_endpoint):
    c = 0
    start_time = time.time()
    while (time.time() - start_time) < duration:
        interarrival_time = generate_interarrival_time(rate_per_second)
        print(interarrival_time)            
        #response = await make_async_api_call(session)
        r = requests.get(api_endpoint, verify=False)
        time.sleep(interarrival_time)
        c += 1
        # print("Response:", response)
    return c




if __name__ == "__main__":

    '''USAGE: python3 run_workload.py <timestamp_log> <pod_log> <activation_log>'''
    # Define parameters
    timestamp_log = sys.argv[1]
    pod_log = sys.argv[2]
    activation_log = sys.argv[3]
    auth = ("23bc46b1-71f6-4ed5-8c54-816aa4f8c502", "123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCGuMDGIwP") 
    rate_per_second = 2  # Adjust as needed
    duration_before_measurement = 5 * 60  # 2 minutes (warm-up time)
    duration_measurement = 10 * 60  # 10 minutes (measurement time)
    #shell_command_1 = "kubectl get pods -n openwhisk --field-selector=status.phase=Running --output=\'custom-columns=NAME:.metadata.name\' --no-headers >> " + pod_log  # Replace with your shell command
    shell_command_1 = "kubectl get pods -n openwhisk --no-headers | awk '$3 == \"Running\" || $3 == \"Pending\" || $3 == \"ContainerCreating\"' >> " + pod_log
    shell_command_2 = "echo \"#####\" >> " + pod_log
    get_log_interval = 2
    #print(shell_command_1)
    # Define API endpoint
    #api_endpoint = "https://192.168.122.9:31001/api/v1/web/guest/default/hello.json"  # Replace with your API endpoint
    api_endpoint = "https://192.168.122.177:31001/api/v1/namespaces/guest/actions/float?blocking=true"
    #api_endpoint = "https://www.google.com/"
       

    #Warm-up period (first 10 minutes)
    print("Warm-up period: Running workload for the first duration minutes...")
    loop = asyncio.get_event_loop()
    _  = loop.run_until_complete(run_workload(duration_before_measurement, api_endpoint, auth))

    

    # Start the shell command in a separate thread
    print("Starting shell command...")
    shell_thread = threading.Thread(target=execute_shell_command, args=(shell_command_1, shell_command_2, get_log_interval))
    shell_thread.start()


    #num_events, event_times, inter_arrival_times = generate_poisson_events(rate_per_second, duration_measurement)
    # Start measuring the experiment
    print("Starting measurement...")
    start_measurement_time = time.time()

    #responses = asyncio.run(run_workload(duration_measurement, api_endpoint))
    loop = asyncio.get_event_loop()
    count, start_time, end_time, activations  = loop.run_until_complete(run_workload(duration_measurement, api_endpoint, auth))
    # Run workload for the next 15 minutes
    #count_invocations = asyncio.run(make_api_calls(api_endpoint, duration_measurement))
    #count_invocations = make_request(duration_measurement, api_endpoint)
    # End of measurement
    end_measurement_time = time.time()
    #print("Experiment time + gather time", end_measurement_time - start_measurement_time)
    # Indicate to the shell command thread that measurement has ended
    measurement_ended.set()
    shell_thread.join()
    print("End of measurement.")
    # Log the starting and ending timestamps
    print("Starting Timestamp:", start_time)
    print("Ending Timestamp:", end_time)
    print("Invocation count: ", count)
    with open(timestamp_log, "a") as f:
        f.write(f"Experiment_Start: {start_time}\n")
        f.write(f"Experiment_End: {end_time}\n")
        f.write(f"Invocation_Count: {count}\n")
        #f.write(f"Extra_duration_if_any: {end_measurement_time - start_measurement_time}\n")

    with open(activation_log, "a") as f:
        for activation in activations:
            f.write(f"{json.dumps(activation)}\n")
