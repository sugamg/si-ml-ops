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
parser.add_argument("--modelName", default=None, type=str, help="Model Name")
parser.add_argument("--modelVersion", nargs='?', default=None, type=str, help="Model Version")
args = parser.parse_args()

workspace_url = args.url.strip("/")

headers = {"Authorization": f"Bearer {args.pat}"}


# load model version to test
#with open(args.path) as json_file:
#    model_metadata = json.load(json_file)

model_version = args.modelVersion
model_name = args.modelName
model_list = []

if (model_version is None or model_version == ''):
  model_list = get_model_version_by_name(workspace_url, headers, model_name, ['Staging'])
  model_version = model_list['Staging']

model_metadata = {
    "model_name": model_name,
    "model_version": model_version,
}


# check that new model version's stage is Staging
new_model_data = {
    "name": model_metadata["model_name"],
    "version": model_metadata["model_version"],
}

new_model_resp = requests.get(
    f"{workspace_url}/api/2.0/mlflow/model-versions/get",
    data=json.dumps(new_model_data),
    headers=headers,
)

new_model_current_stage = new_model_resp.json()["model_version"]["current_stage"]
# NB: this we will have to proceed differently when we allow automatic retraining
if new_model_current_stage == "Production":
    print(f'Model {model_metadata["model_name"]} version {model_metadata["model_version"]} is already in Production: no new model was created.')
    print("Skipping any transition.")
    sys.exit()

# retrieve current prod model version
old_prod_model_data = {
    "name": model_metadata["model_name"],
    "stages": ["Production"],
}

old_prod_model_resp = requests.get(
    f"{workspace_url}/api/2.0/mlflow/registered-models/get-latest-versions",
    data=json.dumps(old_prod_model_data),
    headers=headers,
)

# transition staging model to prod
new_model_to_prod_data = {
    "name": model_metadata["model_name"],
    "version": model_metadata["model_version"],
    "stage": "Production",
    "archive_existing_versions": "False",
}

new_model_to_prod_resp = requests.post(
    f"{workspace_url}/api/2.0/mlflow/model-versions/transition-stage",
    data=json.dumps(new_model_to_prod_data),
    headers=headers,
)
print(f'Transitioned model {model_metadata["model_name"]} version {model_metadata["model_version"]} from {new_model_current_stage} to Production')

if not old_prod_model_resp.json():
    print(f'There was no model {model_metadata["model_name"]} in Production before, no need to archive it then.')
else:
    # transition old prod model to archived
    # NB: this assumes we have only one model in production at any given time
    old_prod_model_version = old_prod_model_resp.json()["model_versions"][0]["version"]

    old_prod_model_to_archived_data = {
        "name": model_metadata["model_name"],
        "version": old_prod_model_version,
        "stage": "Archived",
        "archive_existing_versions": "False",
    }

    old_prod_model_to_archived_resp = requests.post(
        f"{workspace_url}/api/2.0/mlflow/model-versions/transition-stage",
        data=json.dumps(old_prod_model_to_archived_data),
        headers=headers,
    )
    print(f'Transitioned old Production model {model_metadata["model_name"]} version {old_prod_model_version} to Archived')
