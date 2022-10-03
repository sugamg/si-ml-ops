# Databricks notebook source
from argparse import ArgumentParser
import requests
import json
import sys


def get_model_version_by_name(workspace_url, header, model_name, stages):
  http_get_url = f"{workspace_url}/api/2.0/mlflow/registered-models/get-latest-versions"
  payload = {'name': f'{model_name}', 'stages': stages}
  response = requests.request("POST", http_get_url, headers=headers, data=json.dumps(payload)).json()
  models = {}
  if (not response):
    raise 'No Models'
  else:
    for model in response['model_versions']:
      models[model['current_stage']] = model['version']
  return models


parser = ArgumentParser(
    description='Parameters used to compute most frequent pages per subdomain',
)

parser.add_argument("--url", default=None, type=str, help="Workspace URL")
parser.add_argument("--pat", default=None, type=str, help="Personal Access Token")
#parser.add_argument("--path", default=None, type=str, help="Absolute path to model metadata json file")
parser.add_argument("--modelName", default=None, type=str, help="Model Name")
# parser.add_argument("--modelVersion", default=None, type=str, help="Model Version")
parser.add_argument("--modelVersion", nargs='?', default='', type=str, help="Model Version")
args = parser.parse_args()

workspace_url = args.url.strip("/")
headers = {"Authorization": f"Bearer {args.pat}"}

model_version = args.modelVersion
model_name = args.modelName

# load model version to test
#with open(args.path) as json_file:
#    model_metadata = json.load(json_file)

model_list = []

if (model_version is None or model_version == ''):
  print('Model version unavailable, retrieving version using Stage name')
  model_list = get_model_version_by_name(workspace_url, headers, model_name, ['None'])
  model_version = model_list['None']
  print(f'Model version retrieved: {model_version}')

# Check current stage before transitioning
model_name_and_version = {
    "name": model_name,
    "version": model_version
}

payload={}

# print(worskpace_url)
# print(headers)

http_get_url = f"{workspace_url}/api/2.0/mlflow/model-versions/get?name={args.modelName}&version={model_version}"
print(http_get_url)
current_stage_req = requests.request("GET", http_get_url, headers=headers, data=payload)
print(current_stage_req)
current_stage = current_stage_req.json()['model_version']['current_stage']

if current_stage != "None":
    print(f"Model stage is '{current_stage}' != 'None' which means no new model was created. Skipping transition to Staging.")
    sys.exit()

# transition staging model to prod
new_model_to_staging_data = {
    "name": args.modelName,
    "version": model_version,
    "stage": "Staging",
    "archive_existing_versions": "False",
}

new_model_to_staging_req = requests.post(f"{workspace_url}/api/2.0/mlflow/model-versions/transition-stage", data=json.dumps(new_model_to_staging_data), headers=headers)
print(new_model_to_staging_req)
print("Moved new model to staging")
