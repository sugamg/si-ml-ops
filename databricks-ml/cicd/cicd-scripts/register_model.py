# Databricks notebook source
from argparse import ArgumentParser
import requests
import json
import sys
import mlflow
from mlflow.entities import ViewType


parser = ArgumentParser(
    description='Parameters used to compute most frequent pages per subdomain',
)

#parser.add_argument("--src", default=None, type=str, help="Source workspace profile")
parser.add_argument("--experiment", default=None, type=str, help="Experiment id in source workspace")
parser.add_argument("--run", default=None, type=str, help="Run ID in experiment")
parser.add_argument("--src", default=None, type=str, help="Source workspace profile")
parser.add_argument("--dst", default=None, type=str, help="Destination workspace profile")
parser.add_argument("--model", default=None, type=str, help="Model name in MLflow registry")

args = parser.parse_args()

######### Configure pipeline to use MLFlow tracking server in source workspace #########

mlflow.set_tracking_uri("databricks://{}".format(args.src))
tracking_uri = mlflow.get_tracking_uri()
print("Current tracking uri: {}".format(tracking_uri))

def print_run_infos(run_infos):
    for r in run_infos:
        print("- run_id: {}, lifecycle_stage: {}".format(r.run_id, r.lifecycle_stage))

print("All runs:")
print_run_infos(mlflow.list_run_infos(args.experiment, run_view_type=ViewType.ALL))

######### Configure pipeline to use MLFlow registry in destination workspace #########

mlflow.set_registry_uri("databricks://{}".format(args.dst))
mr_uri = mlflow.get_registry_uri()
print("Current registry uri: {}".format(mr_uri))

model_name = args.model
mlflow.register_model(model_uri=args.run, name=model_name)