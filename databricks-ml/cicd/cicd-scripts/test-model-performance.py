# Databricks notebook source
from argparse import ArgumentParser
import requests
import json
import sys
import time


# maximum running time in seconds when testing staging model
timeout = 20*60

parser = ArgumentParser(description="Workspace conf")

parser.add_argument("--qa-url", default=None, type=str, help="QA workspace URL")
parser.add_argument("--qa-pat", default=None, type=str, help="QA Personal Access Token")
parser.add_argument("--cmr-url", default=None, type=str, help="CMR workspace URL")
parser.add_argument("--cmr-pat", default=None, type=str, help="CMR Personal Access Token")
parser.add_argument("--path", default=None, type=str, help="Absolute path to model metadata json file")

args = parser.parse_args()


# RUN NOW
qa_workspace_url = args.qa_url.strip("/")
qa_submit_url = f"{qa_workspace_url}/api/2.0/jobs/run-now"
qa_headers = {"Authorization": f"Bearer {args.qa_pat}"}

cmr_workspace_url = args.cmr_url.strip("/")
cmr_headers = {"Authorization": f"Bearer {args.cmr_pat}"}

# load model version to test
with open(args.path) as json_file:
    model_metadata = json.load(json_file)

# if model's current stage is not None, we should not run performance tests
model_name_and_version = {
    "name": model_metadata["model_name"],
    "version": model_metadata["model_version"],
}

current_stage_req = requests.get(
    f"{cmr_workspace_url}/api/2.0/mlflow/model-versions/get",
    data=json.dumps(model_name_and_version),
    headers=cmr_headers,
)
current_stage = current_stage_req.json()["model_version"]["current_stage"]

if current_stage != "None":
    print(f'Model {model_metadata["model_name"]} version {model_metadata["model_version"]} current stage is "{current_stage}" != "None" which means no new model was created')
    print("Skipping performance testing.")
    sys.exit()


data = {
  "job_id": 1,
  "notebook_params": {
    "model_name": model_metadata["model_name"],
    "model_version": model_metadata["model_version"],
  }
}

req = requests.post(qa_submit_url, data=json.dumps(data), headers=qa_headers)
run_id = req.json()["run_id"]

run_status_url = f"{qa_workspace_url}/api/2.0/jobs/runs/get?run_id={run_id}"
status_state = requests.get(run_status_url, headers=qa_headers).json()["state"]

life_cycle_state = status_state["life_cycle_state"]
result_state = status_state.get("result_state")

start = time.time()
current = start
is_timeout = False

while life_cycle_state != "TERMINATED" and not is_timeout:
    time.sleep(10)
    status_state = requests.get(run_status_url, headers=qa_headers).json()["state"]
    life_cycle_state = status_state["life_cycle_state"]
    result_state = status_state.get("result_state")
    current = time.time()
    is_timeout = True if int(current - start) >= timeout else False

if is_timeout:
    raise Exception(f'Testing model {model_metadata["model_name"]} version {model_metadata["model_version"]} timed out.')

if not result_state:
    raise Exception("No result state, something went wrong.")

if result_state == "FAILED":
    raise Exception(f'Testing model {model_metadata["model_name"]} version {model_metadata["model_version"]} failed')