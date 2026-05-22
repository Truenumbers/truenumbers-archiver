#! /usr/bin/env python3
import _venv_bootstrap  # noqa: F401, E402 — must run before other imports
import argparse
import os
import json
from InquirerPy import inquirer
from InquirerPy.separator import Separator
from helpers import format_numberspace_srd_label, get_api_domains, get_api_error_code, get_api_token
from truenumbers_python_lib import TruenumbersRestApi, TruenumbersTriggerApi

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
        numberspaces_to_load = [numberspace for numberspace in numberspace_archives if format_numberspace_srd_label(numberspace) in numberspaces_arg_list]
        return numberspaces_to_load
  
    formatted_numberspace_archives = [format_numberspace_srd_label(numberspace) for numberspace in numberspace_archives]
    choices = ["All", Separator(), *formatted_numberspace_archives]
    numberspaces_to_load = inquirer.checkbox(message="Select the numberspaces to load", choices=choices, default=["All"]).execute()
    if "All" in numberspaces_to_load:
        return numberspace_archives
    else:
        return [numberspace for numberspace in numberspace_archives if format_numberspace_srd_label(numberspace) in numberspaces_to_load]


def load_triggers(trigger_api_client: TruenumbersTriggerApi, numberspace: str, delete_existing_data: bool):
    numberspace_label = format_numberspace_srd_label(numberspace)
    triggers = []
    try:
        with open(os.path.join(loader_destination_arg, numberspace_label, "triggers.json"), "r") as f:
            triggers = json.load(f)
        if len(triggers) > 0:
            if delete_existing_data:
                print(f"Deleting existing triggers for numberspace: {numberspace_label}")
                trigger_api_client.delete_triggers(numberspace=numberspace)
            for trigger in triggers:
                print(f"Loading trigger: {trigger['name']} for numberspace: {numberspace_label}")
                trigger_api_client.create_trigger(numberspace=numberspace, name=trigger["name"], tnql=trigger["tnql"],
                execute_on=trigger["executeOn"], description=trigger["description"], status=trigger["status"],
                tag_on_trigger=trigger["tagOnTrigger"], destinations=trigger["destinations"])
    except Exception as e:
        print(f"Error loading triggers for numberspace: {numberspace_label}")
        print(e)
        return

def load_queries(tn_rest_api_client: TruenumbersRestApi, numberspace: str, delete_existing_data: bool):
    numberspace_label = format_numberspace_srd_label(numberspace)
    queries = []
    try:
        with open(os.path.join(loader_destination_arg, numberspace_label, "queries.json"), "r") as f:
            queries = json.load(f)
        if len(queries) > 0:
            if delete_existing_data:
                print(f"Deleting existing queries for numberspace: {numberspace_label}")
                tn_rest_api_client.delete_saved_queries(numberspace=numberspace)
            for query in queries:
                print(f"Loading query: {query['name']} for numberspace: {numberspace_label}")
                tn_rest_api_client.create_saved_query(numberspace=numberspace, name=query["name"], tnql=query["tnql"])
    except Exception as e:
        print(f"Error loading queries for numberspace: {numberspace_label}")
        print(e)
        return


def load_numberspace(tn_rest_api_client: TruenumbersRestApi, trigger_api_client: TruenumbersTriggerApi, numberspace: str, should_load_queries: bool, should_load_triggers: bool, delete_existing_data: bool, load_from: str):
    numberspace_label = format_numberspace_srd_label(numberspace)
    print("\n\n")
    print(f"Loading numberspace: {numberspace_label}")
    from_statements = load_from == "Statements"
    from_truenumbers = load_from == "Truenumbers"
    statements = ''
    truenumbers = []
    try:
        tn_rest_api_client.create_numberspace(numberspace=numberspace)
    except Exception as e:
        if get_api_error_code(e) == "NUMBERSPACE_ALREADY_EXISTS":
            print(f"Numberspace already exists: {numberspace_label}. Skipping create numberspace.")
        else:
            print(f"Error creating numberspace: {numberspace_label}")
            print(e)
            return
    with open(os.path.join(loader_destination_arg, numberspace_label, "statements.txt"), "r") as f:
        statements = f.read()
    with open(os.path.join(loader_destination_arg, numberspace_label, "truenumbers.json"), "r") as f:
        truenumbers = json.load(f)

    try:
        if delete_existing_data:
            print(f"Deleting existing data for numberspace: {numberspace_label}")
            tn_rest_api_client.delete_truenumbers(numberspace=numberspace, tnql="* has *")
        has_statements = from_statements and statements and len(statements) > 0;
        has_truenumbers = from_truenumbers and truenumbers and len(truenumbers) > 0;
        if not has_statements and not has_truenumbers:
            print(f"No truenumber data to load for numberspace: {numberspace_label}")
        if from_statements and has_statements:
            print(f"Loading statements for numberspace: {numberspace_label}")
            tn_rest_api_client.create_truenumbers_from_statement(numberspace=numberspace, true_statement=statements)
        if from_truenumbers and has_truenumbers:
            batch_size = 500
            total = len(truenumbers)
            print(f"Loading {total} truenumbers for numberspace: {numberspace_label}")
            for start in range(0, total, batch_size):
                batch = truenumbers[start:start + batch_size]
                batch_num = start // batch_size + 1
                batch_count = (total + batch_size - 1) // batch_size
                print(f"  Posting batch {batch_num}/{batch_count} ({len(batch)} truenumbers)")
                tn_rest_api_client.create_truenumbers_from_json(numberspace=numberspace, truenumbers_json=batch)
    except Exception as e:
        print(f"Error loading numberspace: {numberspace_label}")
        print(e)
        return

    if should_load_queries:
        load_queries(tn_rest_api_client, numberspace, delete_existing_data)
    if should_load_triggers:
        load_triggers(trigger_api_client, numberspace, delete_existing_data)

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
    print(f"Numberspaces to load: {[format_numberspace_srd_label(numberspace) for numberspace in numberspaces_to_load]}")
    load_from = load_from_arg or inquirer.select(message="Select the source of the data to load", choices=["Statements", "Truenumbers"], default="Truenumbers").execute()
    for numberspace in numberspaces_to_load:
        load_numberspace(tn_rest_api_client, trigger_api_client, numberspace, should_load_queries, should_load_triggers, delete_existing_data, load_from)

main()