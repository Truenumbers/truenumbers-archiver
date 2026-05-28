#! /usr/bin/env python3
import _venv_bootstrap  # noqa: F401, E402 — must run before other imports
import json
from InquirerPy import inquirer
from InquirerPy.separator import Separator
import os
import argparse
from helpers import get_api_token, get_api_domains, format_numberspace_srd_label, get_dir_name_for_numberspace, get_file_name_from_artifact_value
from truenumbers_python_lib import TruenumbersRestApi, TruenumbersTriggerApi, TruenumbersArtifactApi
from truenumbers_python_lib import truenumber_helpers
API_TOKEN_ENV_VAR = 'API_TOKEN'

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--api_token', type=str, help='Optional API token to authenticate with the API. Defaults to the API_TOKEN environment variable.', default=os.getenv(API_TOKEN_ENV_VAR, None),required=False)
parser.add_argument('--numberspaces', type=str, help='List of comma separated numberspaces to archive', default=None, required=False)
parser.add_argument('--archive_all_numberspaces', dest='archive_all_numberspaces', action="store_true", help='Controls whether to archive all numberspaces or not')
parser.add_argument('--archive_queries', dest='archive_queries', action="store_true", help='Controls whether to archive queries or not')
parser.add_argument('--archive_triggers', dest='archive_triggers', action="store_true", help='Controls whether to archive triggers or not')
parser.add_argument('--archive_artifacts', dest='archive_artifacts', action="store_true", help='Controls whether to archive artifacts or not')
parser.add_argument('-a','--auth', dest='has_auth', action="store_true", help='Controls whether API requires authentication or not', default=False, required=False)
parser.add_argument('-e', '--email', type=str, help='Optional email to authenticate with the API', default=None, required=False)
parser.add_argument('-p', '--password', type=str, help='Optional password to authenticate with the API', default=None, required=False)
parser.add_argument('-o', '--organization', type=str, help='Optional organization to authenticate with the API', default=None, required=False)
parser.add_argument('--tn_rest_api', dest='tn_rest_api_domain', type=str, help='Optional domain to authenticate with the REST API', default=None, required=False)
parser.add_argument('--trigger_api', dest='trigger_api_domain', type=str, help='Optional domain to authenticate with the Trigger API', default=None, required=False)
parser.add_argument('--artifact_api', dest='artifact_api_domain', type=str, help='Optional domain to authenticate with the Artifact API', default=None, required=False)
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
artifact_api_domain_arg = parser.parse_args().artifact_api_domain;
archive_artifacts_arg = parser.parse_args().archive_artifacts;

def get_numberspaces_to_archive(tn_rest_api_client):
    numberspaces = tn_rest_api_client.get_numberspaces()["numberspaces"]
    numberspace_labels = [format_numberspace_srd_label(numberspace) for numberspace in numberspaces]

    def return_numberspaces(numberspace_labels_to_return: list[str]):
        formatted_numberspace_labels_to_return = [format_numberspace_srd_label(numberspace) for numberspace in numberspace_labels_to_return]
        numberspaces_to_return = [numberspace for numberspace in numberspaces if format_numberspace_srd_label(numberspace) in formatted_numberspace_labels_to_return]
        return formatted_numberspace_labels_to_return, numberspaces_to_return

    if archive_all_numberspaces_arg:
        return return_numberspaces(numberspace_labels)
    if numberspaces_arg and numberspaces_arg != "":
        numberspaces_arg_list = numberspaces_arg.split(",")
        return return_numberspaces([numberspace for numberspace in numberspace_labels if numberspace in numberspaces_arg_list])
    else:
        choices = ["All", Separator(), *numberspace_labels]
        numberspaces_to_archive = inquirer.checkbox(message="Select the numberspaces to archive", choices=choices, default=["All"]).execute()
        if "All" in numberspaces_to_archive:
            return return_numberspaces(numberspace_labels)
        else:
            return return_numberspaces([numberspace for numberspace in numberspace_labels if numberspace in numberspaces_to_archive])

def get_truenumbers(tn_rest_api_client: TruenumbersRestApi, numberspace: str) -> list[dict]:
    limit = 1000
    offset = 0
    truenumbers = []
    initial_response = tn_rest_api_client.tnql(tnql="* has *", numberspace=numberspace, limit=limit, offset=offset)
    truenumbers.extend(initial_response["truenumbers"])
    total_count = initial_response["count"]
    while len(truenumbers) < total_count:
        offset = offset + 1
        response = tn_rest_api_client.tnql(tnql="* has *", numberspace=numberspace, limit=limit, offset=offset)
        truenumbers.extend(response["truenumbers"])
    return truenumbers

def archive_numberspace(tn_rest_api_client: TruenumbersRestApi, trigger_api_client: TruenumbersTriggerApi, artifact_api_client: TruenumbersArtifactApi, numberspace_label: str, full_numberspace_name: str, should_archive_queries: bool, should_archive_triggers: bool):
    print("\n\n")
    print(f"Archiving numberspace: {numberspace_label}")

    numberspace_dir_name = get_dir_name_for_numberspace(numberspace_label)
    os.makedirs(os.path.join(archiver_destination_arg, numberspace_dir_name), exist_ok=True)
    with open(os.path.join(archiver_destination_arg, numberspace_dir_name, "numberspace.txt"), "w") as f:
        f.write(full_numberspace_name)

    print(f"Archiving truenumbers for numberspace: {numberspace_label}")
    truenumbers = get_truenumbers(tn_rest_api_client, full_numberspace_name)
    artifact_ids = []
    for truenumber in truenumbers:
        if  truenumber_helpers.is_artifact_truenumber(truenumber):
            artifact_ids.append(truenumber.get("value").get("value"))
    with open(os.path.join(archiver_destination_arg, numberspace_dir_name, "truenumbers.json"), "w") as f:
        json.dump(truenumbers, f, indent=4)
    statements = [truenumber["trueStatement"] for truenumber in truenumbers]

    print(f"Archived {len(truenumbers)} truenumbers for numberspace: {numberspace_label}")
    with open(os.path.join(archiver_destination_arg, numberspace_dir_name, "statements.txt"), "w") as f:
        f.write("\n".join(statements))
    if archive_artifacts_arg and len(artifact_ids) > 0:
        print(f"Archiving artifacts for numberspace: {numberspace_label}")
        os.makedirs(os.path.join(archiver_destination_arg, numberspace_dir_name, "files"), exist_ok=True)
        for artifact_id in artifact_ids:
            artifact = artifact_api_client.get_artifact_by_id(id=artifact_id)
            file_name = get_file_name_from_artifact_value(artifact_id)
            with open(os.path.join(archiver_destination_arg, numberspace_dir_name, "files", file_name), "wb") as f:
                f.write(artifact.content)
        print(f"Archived {len(artifact_ids)} artifacts for numberspace: {numberspace_label}")

    if should_archive_queries:
        print(f"Archiving queries for numberspace: {numberspace_label}")
        queries = tn_rest_api_client.get_saved_queries(numberspace=full_numberspace_name)["queries"]
        print(f"Archived {len(queries)} queries for numberspace: {numberspace_label}")
        with open(os.path.join(archiver_destination_arg, numberspace_dir_name, "queries.json"), "w") as f:
            json.dump(queries, f, indent=4)
            
    if should_archive_triggers:
        print(f"Archiving triggers for numberspace: {numberspace_label}")
        triggers = trigger_api_client.get_triggers(numberspace=full_numberspace_name, status=["ACTIVE", "INACTIVE"])["triggerDefinitions"]
        print(f"Archived {len(triggers)} triggers for numberspace: {numberspace_label}")
        with open(os.path.join(archiver_destination_arg, numberspace_dir_name, "triggers.json"), "w") as f:
            json.dump(triggers, f, indent=4)
    

def main():
    should_archive_queries = archive_queries_arg or inquirer.confirm(message="Do you want to archive queries?", default=True).execute()
    should_archive_triggers = archive_triggers_arg or inquirer.confirm(message="Do you want to archive triggers?", default=True).execute()
    should_archive_artifacts = archive_artifacts_arg or inquirer.confirm(message="Do you want to archive artifacts?", default=True).execute()
    tn_rest_api_domain, trigger_api_domain, artifact_api_domain = get_api_domains(should_archive_triggers, should_archive_artifacts, arguments_dict={
        "tn_rest_api_domain": tn_rest_api_domain_arg,
        "trigger_api_domain": trigger_api_domain_arg,
        "artifact_api_domain": artifact_api_domain_arg
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
    artifact_api_client = TruenumbersArtifactApi(base_url=artifact_api_domain, shared_headers={"Authorization": f"Bearer {api_token}"} if api_token is not None else None)
    numberspace_labels_to_archive, numberspaces_to_archive = get_numberspaces_to_archive(tn_rest_api_client)
    if len(numberspaces_to_archive) == 0:
        print("No numberspaces to archive. Exiting...")
        return
    print("Archiving numberspaces: ", numberspace_labels_to_archive)

    for numberspace_label in numberspace_labels_to_archive:
        archive_numberspace(tn_rest_api_client, trigger_api_client, artifact_api_client, numberspace_label, numberspaces_to_archive[numberspace_labels_to_archive.index(numberspace_label)], should_archive_queries, should_archive_triggers)

main()