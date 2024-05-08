import asyncio
import time
import random
import subprocess
import threading
import sys
import requests
import numpy as np
from aiohttp import ClientSession, BasicAuth, TraceConfig
from statistics import mean
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
in_flight_counts = []


# Function to generate interarrival times
def generate_interarrival_time(rate):
    return random.expovariate(rate)

# Function to make asynchronous API calls
async def make_async_api_call(session, api_endpoint):
    s_time = time.time()
    async with session.get(api_endpoint) as response:
        response_data =  await response.text()
        response_time = time.time() - s_time
        return response_data, response_time


async def on_request_chunk_sent(session, trace_config_ctx, params):
    trace_config_ctx.start = asyncio.get_event_loop().time()

async def on_response_chunk_received(session, trace_config_ctx, params):
    elapsed = asyncio.get_event_loop().time() - trace_config_ctx.start
    print("Request took {}".format(elapsed))


async def periodic(interval):
    while True:
        await asyncio.sleep(interval)
        inflight_tasks = [task for task in asyncio.all_tasks() if not task.done()]
        in_flight_counts.append(len(inflight_tasks))


# Function to run the workload
async def run_workload(duration, api_endpoint, interval):
    count = 0
    tasks = []
    start_time = time.time()
    asyncio.create_task(periodic(interval))
    async with ClientSession() as session:
        while (time.time() - start_time) < duration:
            interarrival_time = generate_interarrival_time(rate_per_second)
            task = asyncio.ensure_future(make_async_api_call(session, api_endpoint))            
            tasks.append(task)
            count += 1
            await asyncio.sleep(interarrival_time)
        end_time = time.time()
        responses = await asyncio.gather(*tasks)
    return count, start_time, end_time, responses



        
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

    '''USAGE: python3 run_workload.py <timestamp_log> <responses_log>'''
    # Define parameters
    rate_per_second = 2  # Adjust as needed
    duration_before_measurement = 2 * 60  # 2 minutes (warm-up time)
    duration_measurement = 10 * 60  # 10 minutes (measurement time)
    api_endpoint = "http://127.0.0.1:3000/float-pyperf"
    timestamp_log = sys.argv[1]
    responses_log = sys.argv[2]
    in_flight_check = 2

    #Warm-up period (first 10 minutes)
    # trace_config = TraceConfig()
    # trace_config.on_request_start.append(on_request_chunk_sent)
    # trace_config.on_request_end.append(on_response_chunk_received)
    # print("Warm-up period: Running workload for the first duration minutes...")
    # loop = asyncio.get_event_loop()
    # _  = loop.run_until_complete(run_workload(duration_before_measurement, api_endpoint, in_flight_check))

    

    # Start the shell command in a separate thread


    #num_events, event_times, inter_arrival_times = generate_poisson_events(rate_per_second, duration_measurement)
    # Start measuring the experiment
    print("Starting measurement...")
    start_measurement_time = time.time()

    #responses = asyncio.run(run_workload(duration_measurement, api_endpoint))
    loop = asyncio.get_event_loop()
    #loop.call_later(2, count_inflight_requests)
    count, start_time, end_time, responses  = loop.run_until_complete(run_workload(duration_measurement, api_endpoint, in_flight_check))   
    end_measurement_time = time.time()
    measurement_ended.set()
    print("End of measurement.")
    # Log the starting and ending timestamps
    print("Starting Timestamp:", start_time)
    print("Ending Timestamp:", end_time)
    print("Invocation count: ", count)
    exp_inflight_counts = in_flight_counts
    print("Avg inflight counts: ", mean(exp_inflight_counts) - 2)
    #print("Avg response time", mean(responses[1]))
    print("inflight counts", len(in_flight_counts))

    response_times = [float(resp[1]) for resp in responses]
    print("Avg response time", mean(response_times))

    with open(timestamp_log, "a") as f:
        f.write(f"Experiment_Start: {start_time}\n")
        f.write(f"Experiment_End: {end_time}\n")
        f.write(f"Invocation_Count: {count}\n")
        #f.write(f"Extra_duration_if_any: {end_measurement_time - start_measurement_time}\n")

    with open(responses_log, "a") as f:
        for resp in responses:
            f.write(f"{str(resp[1])}\n")
