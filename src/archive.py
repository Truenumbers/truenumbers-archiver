#! /usr/bin/env python3
import _venv_bootstrap  # noqa: F401, E402 — must run before other imports
import json
from InquirerPy import inquirer
from InquirerPy.separator import Separator
import os
import argparse
from helpers import get_api_token, get_api_domains, format_numberspace_srd_label
from truenumbers_python_lib import TruenumbersRestApi, TruenumbersTriggerApi
API_TOKEN_ENV_VAR = 'API_TOKEN'

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--api_token', type=str, help='Optional API token to authenticate with the API. Defaults to the API_TOKEN environment variable.', default=os.getenv(API_TOKEN_ENV_VAR, None),required=False)
parser.add_argument('--numberspaces', type=str, help='List of comma separated numberspaces to archive', default=None, required=False)
parser.add_argument('--archive_all_numberspaces', dest='archive_all_numberspaces', action="store_true", help='Controls whether to archive all numberspaces or not')
parser.add_argument('--archive_queries', dest='archive_queries', action="store_true", help='Controls whether to archive queries or not')
parser.add_argument('--archive_triggers', dest='archive_triggers', action="store_true", help='Controls whether to archive triggers or not')
parser.add_argument('-a','--auth', dest='has_auth', action="store_true", help='Controls whether API requires authentication or not', default=False, required=False)
parser.add_argument('-e', '--email', type=str, help='Optional email to authenticate with the API', default=None, required=False)
parser.add_argument('-p', '--password', type=str, help='Optional password to authenticate with the API', default=None, required=False)
parser.add_argument('-o', '--organization', type=str, help='Optional organization to authenticate with the API', default=None, required=False)
parser.add_argument('--tn_rest_api', dest='tn_rest_api_domain', type=str, help='Optional domain to authenticate with the REST API', default=None, required=False)
parser.add_argument('--trigger_api', dest='trigger_api_domain', type=str, help='Optional domain to authenticate with the Trigger API', default=None, required=False)
parser.add_argument('-d', '--archiver_destination', type=str, help='Optional destination to archive the numberspaces to', default="../archived_numberspaces", required=False)

api_token_arg = parser.parse_args().api_token;
numberspaces_arg = parser.parse_args().numberspaces;
archive_queries_arg = parser.parse_args().archive_queries;
archive_triggers_arg = parser.parse_args().archive_triggers;
archive_all_numberspaces_arg = parser.parse_args().archive_all_numberspaces;
has_auth_arg = parser.parse_args().has_auth;
email_arg = parser.parse_args().email;
password_arg = parser.parse_args().password;
organization_arg = parser.parse_args().organization;
tn_rest_api_domain_arg = parser.parse_args().tn_rest_api_domain;
trigger_api_domain_arg = parser.parse_args().trigger_api_domain;
archiver_destination_arg = parser.parse_args().archiver_destination;


def get_numberspaces_to_archive(tn_rest_api_client):
    numberspaces = tn_rest_api_client.get_numberspaces()["numberspaces"]
    numberspace_labels = [format_numberspace_srd_label(numberspace) for numberspace in numberspaces]
    if archive_all_numberspaces_arg:
        return numberspace_labels
    if numberspaces_arg and numberspaces_arg != "":
        numberspaces_arg_list = numberspaces_arg.split(",")
        numberspaces_to_archive = [numberspace for numberspace in numberspace_labels if numberspace in numberspaces_arg_list]
        return numberspaces_to_archive
    else:
        choices = ["All", Separator(), *numberspace_labels]
        numberspaces_to_archive = inquirer.checkbox(message="Select the numberspaces to archive", choices=choices, default=["All"]).execute()
        if "All" in numberspaces_to_archive:
            return numberspace_labels
        else:
            return [numberspace for numberspace in numberspace_labels if numberspace in numberspaces_to_archive]

def get_truenumbers(tn_rest_api_client: TruenumbersRestApi, numberspace_label: str) -> list[dict]:
    limit = 1000
    offset = 0
    truenumbers = []
    initial_response = tn_rest_api_client.tnql(tnql="* has *", numberspace=numberspace_label, limit=limit, offset=offset)
    truenumbers.extend(initial_response["truenumbers"])
    total_count = initial_response["count"]
    while len(truenumbers) < total_count:
        offset += limit
        response = tn_rest_api_client.tnql(tnql="* has *", numberspace=numberspace_label, limit=limit, offset=offset)
        truenumbers.extend(response["truenumbers"])
    return truenumbers

def archive_numberspace(tn_rest_api_client: TruenumbersRestApi, trigger_api_client: TruenumbersTriggerApi, numberspace_label: str, should_archive_queries: bool, should_archive_triggers: bool):
    print(f"Archiving numberspace: {numberspace_label}")
    os.makedirs(os.path.join(archiver_destination_arg, numberspace_label), exist_ok=True)
    with open(os.path.join(archiver_destination_arg, numberspace_label, "numberspace.txt"), "w") as f:
        f.write(numberspace_label)
    truenumbers = get_truenumbers(tn_rest_api_client, numberspace_label)
    print(truenumbers)
    with open(os.path.join(archiver_destination_arg, numberspace_label, "truenumbers.json"), "w") as f:
        json.dump(truenumbers, f, indent=4)
    statements = [truenumber["trueStatement"] for truenumber in truenumbers]
    with open(os.path.join(archiver_destination_arg, numberspace_label, "statements.txt"), "w") as f:
        f.write("\n".join(statements))
    if should_archive_queries:
        queries = tn_rest_api_client.get_saved_queries(numberspace=numberspace_label)["queries"]
        with open(os.path.join(archiver_destination_arg, numberspace_label, "queries.json"), "w") as f:
            json.dump(queries, f, indent=4)
    if should_archive_triggers:
        triggers = trigger_api_client.get_triggers(numberspace=numberspace_label)["triggerDefinitions"]
        with open(os.path.join(archiver_destination_arg, numberspace_label, "triggers.json"), "w") as f:
            json.dump(triggers, f, indent=4)
    

def main():
    should_archive_queries = archive_queries_arg or inquirer.confirm(message="Do you want to archive queries?", default=True).execute()
    should_archive_triggers = archive_triggers_arg or inquirer.confirm(message="Do you want to archive triggers?", default=True).execute()
    tn_rest_api_domain, trigger_api_domain = get_api_domains(should_archive_triggers, arguments_dict={
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
    numberspaces_to_archive = get_numberspaces_to_archive(tn_rest_api_client)
    if len(numberspaces_to_archive) == 0:
        print("No numberspaces to archive. Exiting...")
        return
    print("Archiving numberspaces: ", numberspaces_to_archive)

    for numberspace_label in numberspaces_to_archive:
        archive_numberspace(tn_rest_api_client, trigger_api_client, numberspace_label, should_archive_queries, should_archive_triggers)

main()