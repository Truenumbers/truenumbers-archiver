#! /usr/bin/env python3
import argparse
import os
import json
from InquirerPy import inquirer
from InquirerPy.separator import Separator
from helpers import get_api_domains, get_api_token
from truenumbers_python_lib.TruenumbersRestApi import TruenumbersRestApi
from truenumbers_python_lib.TruenumbersTriggerApi import TruenumbersTriggerApi

API_TOKEN_ENV_VAR = 'API_TOKEN'

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--api_token', type=str, help='Optional API token to authenticate with the API. Defaults to the API_TOKEN environment variable.', default=os.getenv(API_TOKEN_ENV_VAR, None),required=False)
parser.add_argument('--numberspaces', type=str, help='List of comma separated numberspaces to archive', default=None, required=False)
parser.add_argument('--load_all_numberspaces', dest='load_all_numberspaces', action="store_true", help='Controls whether to load all numberspaces or not')
parser.add_argument('--load_queries', dest='load_queries', action="store_true", help='Controls whether to load queries or not')
parser.add_argument('--load_triggers', dest='load_triggers', action="store_true", help='Controls whether to load triggers or not')
parser.add_argument('-a','--auth', dest='has_auth', action="store_true", help='Controls whether API requires authentication or not', default=False, required=False)
parser.add_argument('-e', '--email', type=str, help='Optional email to authenticate with the API', default=None, required=False)
parser.add_argument('-p', '--password', type=str, help='Optional password to authenticate with the API', default=None, required=False)
parser.add_argument('-o', '--organization', type=str, help='Optional organization to authenticate with the API', default=None, required=False)
parser.add_argument('--tn_rest_api', dest='tn_rest_api_domain', type=str, help='Optional domain to authenticate with the REST API', default=None, required=False)
parser.add_argument('--trigger_api', dest='trigger_api_domain', type=str, help='Optional domain to authenticate with the Trigger API', default=None, required=False)
parser.add_argument('-d', '--loader_destination', type=str, help='Optional destination to archive the numberspaces to', default="../archived_numberspaces", required=False)
parser.add_argument('--delete_existing_data', dest='delete_existing_data', action="store_true", help='Controls whether to delete existing data before loading', default=False, required=False)
parser.add_argument('--load_from', type=str, help='Optional source of the data to load', choices=["Statements", "Truenumbers"], default=None, required=False)

api_token_arg = parser.parse_args().api_token;
numberspaces_arg = parser.parse_args().numberspaces;
load_queries_arg = parser.parse_args().load_queries;
load_triggers_arg = parser.parse_args().load_triggers;
load_all_numberspaces_arg = parser.parse_args().load_all_numberspaces;
has_auth_arg = parser.parse_args().has_auth;
email_arg = parser.parse_args().email;
password_arg = parser.parse_args().password;
organization_arg = parser.parse_args().organization;
tn_rest_api_domain_arg = parser.parse_args().tn_rest_api_domain;
trigger_api_domain_arg = parser.parse_args().trigger_api_domain;
loader_destination_arg = parser.parse_args().loader_destination;
delete_existing_data_arg = parser.parse_args().delete_existing_data;
load_from_arg = parser.parse_args().load_from;

def get_numberspaces_to_load():
    os.listdir(loader_destination_arg)
    numberspace_archives = []
    for directory in os.listdir(loader_destination_arg):
        if not os.path.isdir(os.path.join(loader_destination_arg, directory)):
            continue
        for file in os.listdir(os.path.join(loader_destination_arg, directory)):
            if os.path.isfile(os.path.join(loader_destination_arg, directory, file)) and file == "numberspace.txt":
                with open(os.path.join(loader_destination_arg, directory, file), "r") as f:
                    numberspace_archives.append(f.read())

    if load_all_numberspaces_arg:
        return numberspace_archives
    if numberspaces_arg and numberspaces_arg != "":
        numberspaces_arg_list = numberspaces_arg.split(",")
        numberspaces_to_load = [numberspace for numberspace in numberspace_archives if numberspace in numberspaces_arg_list]
        return numberspaces_to_load
  
    choices = ["All", Separator(), *numberspace_archives]
    numberspaces_to_load = inquirer.checkbox(message="Select the numberspaces to load", choices=choices, default=["All"]).execute()
    if "All" in numberspaces_to_load:
        return numberspace_archives
    else:
        return [numberspace for numberspace in numberspace_archives if numberspace in numberspaces_to_load]


def load_numberspace(tn_rest_api_client: TruenumbersRestApi, trigger_api_client: TruenumbersTriggerApi, numberspace: str, should_load_queries: bool, should_load_triggers: bool, delete_existing_data: bool, load_from: str):
    print(f"Loading numberspace: {numberspace}")
    from_statements = load_from == "Statements"
    from_truenumbers = load_from == "Truenumbers"
    statements = ''
    truenumbers = []
    if delete_existing_data:
        tn_rest_api_client.delete_truenumbers(numberspace=numberspace, tnql="* has *")
        # Delete queries
        # Delete triggers
        
    with open(os.path.join(loader_destination_arg, numberspace, "statements.txt"), "r") as f:
        statements = f.read()
    with open(os.path.join(loader_destination_arg, numberspace, "truenumbers.json"), "r") as f:
        truenumbers = json.load(f)

    if from_statements:
        tn_rest_api_client.create_truenumbers_from_statement(numberspace=numberspace, true_statement=statements)
    if from_truenumbers:
        tn_rest_api_client.create_truenumbers_from_json(numberspace=numberspace, truenumbers_json=truenumbers)

    if should_load_queries:
        queries = []
        with open(os.path.join(loader_destination_arg, numberspace, "queries.json"), "r") as f:
            queries = json.load(f)
        for query in queries:
            tn_rest_api_client.create_saved_query(numberspace=numberspace, name=query["name"], tnql=query["tnql"])
    if should_load_triggers:
        triggers = []
        with open(os.path.join(loader_destination_arg, numberspace, "triggers.json"), "r") as f:
            triggers = json.load(f)
        for trigger in triggers:
            trigger_api_client.create_trigger(numberspace=numberspace, name=trigger["name"], tnql=trigger["tnql"],
            execute_on=trigger["execute_on"], description=trigger["description"], status=trigger["status"],
            tag_on_trigger=trigger["tag_on_trigger"], load_historic_data=trigger["load_historic_data"], destinations=trigger["destinations"])

def main():
    should_load_triggers = load_triggers_arg or inquirer.confirm(message="Do you want to load triggers?", default=True).execute()
    should_load_queries = load_queries_arg or inquirer.confirm(message="Do you want to load queries?", default=True).execute()
    tn_rest_api_domain, trigger_api_domain = get_api_domains(should_load_triggers, arguments_dict={
        "tn_rest_api_domain": tn_rest_api_domain_arg,
        "trigger_api_domain": trigger_api_domain_arg
    })
    api_token = get_api_token(tn_rest_api_domain, arguments_dict={
        "email": email_arg,
        "password": password_arg,
        "organization": organization_arg,
        "api_token": api_token_arg,
        "has_auth": has_auth_arg
    })
    tn_rest_api_client = TruenumbersRestApi(base_url=tn_rest_api_domain, shared_headers={"Authorization": f"Bearer {api_token}"} if api_token is not None else None)
    trigger_api_client = TruenumbersTriggerApi(base_url=trigger_api_domain, shared_headers={"Authorization": f"Bearer {api_token}"} if api_token is not None else None)

    delete_existing_data = delete_existing_data_arg or inquirer.confirm(message="Do you want to delete existing data before loading?", default=False).execute()
    numberspaces_to_load = get_numberspaces_to_load()
    load_from = load_from_arg or inquirer.select(message="Select the source of the data to load", choices=["Statements", "Truenumbers"], default="Truenumbers").execute()
    print(f"Numberspaces to load: {numberspaces_to_load}")
    for numberspace in numberspaces_to_load:
        load_numberspace(tn_rest_api_client, trigger_api_client, numberspace, should_load_queries, should_load_triggers, delete_existing_data, load_from)

main()