# Databricks notebook source
from argparse import ArgumentParser
import requests
import json
import time
#import subprocess


# maximum running time in seconds when testing staging model
timeout = 20*60

parser = ArgumentParser(description="Workspace conf")

parser.add_argument("--url", default=None, type=str, help="Workspace URL")
parser.add_argument("--pat", default=None, type=str, help="Personal Access Token")
parser.add_argument("--jobid", default=None, type=str, help="Job ID")
parser.add_argument("--notebook", default=None, type=str, help="Notebook")
parser.add_argument("--clusterid", default=None, type=str, help="Cluster ID")


args = parser.parse_args()


# RUN NOW
workspace_url = args.url.strip("/")
submit_url = f"{workspace_url}/api/2.0/jobs/runs/submit"
print("Job submit URL : " + submit_url)
headers = {"Authorization": f"Bearer {args.pat}"}

data = {
    "run_name": "Run notebook",
    "existing_cluster_id": f"{args.clusterid}", #"0621-165139-wikis225",
    "notebook_task": {
        "notebook_path": f"{args.notebook}", #parameter  "/databricks-demo/app/notebooks/model_train", 
        "base_parameters": {
        }
    }
}

req = requests.post(submit_url, data=json.dumps(data), headers=headers)
print(req.json())
run_id = req.json()["run_id"]

run_status_url = f"{workspace_url}/api/2.0/jobs/runs/get-output?run_id={run_id}"
#status_state = requests.get(run_status_url, headers=headers).json()["state"]
response = requests.get(run_status_url, headers=headers).json()['metadata']
status_state =  response["state"]

life_cycle_state = status_state["life_cycle_state"]
result_state = status_state.get("result_state")

start = time.time()
current = start
is_timeout = False

while life_cycle_state != "TERMINATED" and not is_timeout:
    time.sleep(10)
    #status_state = requests.get(run_status_url, headers=headers).json()["state"]
    response = requests.get(run_status_url, headers=headers).json()
    status_state = response['metadata']["state"]
    life_cycle_state = status_state["life_cycle_state"]
    result_state = status_state.get("result_state")
    current = time.time()
    is_timeout = True if int(current - start) >= timeout else False

if is_timeout:
    raise Exception('Job timed out.')

if not result_state:
    raise Exception("No result state, something went wrong.")

if result_state == "FAILED":
    raise Exception('Job failed')

results = ''
print(response['notebook_output'])
if (response['notebook_output']):
  if ('result' in response['notebook_output']):
    results = response['notebook_output']['result']

print(f"##vso[task.setvariable variable=deploymodel;isOutput=true]{results}")
