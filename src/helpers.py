from InquirerPy import inquirer
from truenumbers_python_lib.TruenumbersRestApi import TruenumbersRestApi
import re


def get_tn_login_api_client(tn_rest_api_domain):
    return TruenumbersRestApi(base_url=tn_rest_api_domain)

def get_api_domains(should_do_triggers_api, arguments_dict):
    tn_rest_api_domain_arg = arguments_dict.get("tn_rest_api_domain", None)
    trigger_api_domain_arg = arguments_dict.get("trigger_api_domain", None)
    if tn_rest_api_domain_arg and tn_rest_api_domain_arg != "":
        tn_rest_api_domain = tn_rest_api_domain_arg
    else:
        tn_rest_api_domain = inquirer.text(message="Enter the domain of the Truenumbers REST API").execute()
    if not should_do_triggers_api:
        return tn_rest_api_domain, ""
    if trigger_api_domain_arg and trigger_api_domain_arg != "":
        trigger_api_domain = trigger_api_domain_arg
    else:
        trigger_api_domain = inquirer.text(message="Enter the domain of the Tigger API").execute()
    return tn_rest_api_domain, trigger_api_domain

def get_api_token(tn_rest_api_domain, arguments_dict):
    email_arg = arguments_dict.get("email", None)
    password_arg = arguments_dict.get("password", None)
    organization_arg = arguments_dict.get("organization", None)
    api_token_arg = arguments_dict.get("api_token", None)
    has_auth_arg = arguments_dict.get("has_auth", False)

    def get_email():
        if email_arg and email_arg != "":
            return email_arg
        else:
            return inquirer.text(message="Enter your email").execute()
    def get_password():
        if password_arg and password_arg != "":
            return password_arg
        else:
            return inquirer.secret(message="Enter your password").execute()
    def get_organization():
        if organization_arg and organization_arg != "":
            return organization_arg
        else:
            return inquirer.text(message="Enter your organization").execute()

    if api_token_arg and api_token_arg != "":
        print("Using API token from arguments")
        return api_token_arg
    if not has_auth_arg:
        return None
    
    has_auth_creds = email_arg and password_arg and organization_arg;
    has_auth_confirm = has_auth_arg or inquirer.confirm(message="Does API require authentication?", default=True).execute()
    if not has_auth_confirm:
        return None

    def get_api_token_from_login():
        email = get_email()
        password = get_password()
        organization = get_organization()
        login_api_client = get_tn_login_api_client(tn_rest_api_domain)
        response = login_api_client.login_user(email=email, password=password, organization=organization)
        api_token = response["accessToken"]
        return api_token
    do_login = has_auth_creds or inquirer.confirm(message="Do you want to login to the API?", default=True).execute()
    if do_login:
        return get_api_token_from_login()
    else:
        api_token = inquirer.text(message="Enter your API token").execute()
        return api_token



NUMBERSPACE_PRODUCT_CODE_REGEXP = re.compile(
    r"^_system:numberspace:product_code:.*/",
    re.IGNORECASE,
)

def format_numberspace_srd_label(srd: str) -> str:
    if NUMBERSPACE_PRODUCT_CODE_REGEXP.search(srd):
        return NUMBERSPACE_PRODUCT_CODE_REGEXP.sub("", srd)
    return srd.replace("_system:numberspace/", "").strip()

