from datetime import date 

from docusign_esign import ApiClient
from docusign_esign import ApiException
from docusign_esign import AccountsApi
from docusign_esign import CustomFields
from docusign_esign import EnvelopesApi, EnvelopeDefinition, EnvelopeEvent
from docusign_esign import EventNotification
from docusign_esign import FoldersApi
from docusign_esign import Tabs
from docusign_esign import TemplatesApi, TemplateRole
from docusign_esign import Text, TextCustomField

api_client = ApiClient()
api_exception = ApiException()

with open(r"\Users\Vincent Lanzilotti\Documents\digs\keys.txt") as fill: # make sure file path is updated to server path
    private_key = fill.read().encode("ascii").decode("utf-8")

my_app = api_client.request_jwt_user_token(
    client_id="52258420-66d5-4939-b454-079a8f051514",
    user_id="6ba13a02-d9ac-4346-98ce-9f1e1d31086b",
    oauth_host_name="account-d.docusign.com", # Authorization server - or "https://account-d.docusign.com/oauth/auth?"
    private_key_bytes=private_key,
    expires_in=3600,
    scopes=["signature", "impersonation"]
)

access_token = my_app.access_token

#print(access_token)
print("Authorization granted!")
    
# Setting the base path
api_client.host = "https://demo.docusign.net/restapi" # Base url path

# Setting the HTTP header with authentication token
api_client.set_default_header("Authorization", f"Bearer {access_token}")

envelope_api = EnvelopesApi(api_client)

template_api = TemplatesApi(api_client)

template_list = template_api.list_templates("bc57f2fd-8120-4ae0-aed2-480c6256fd24")
print(template_list)

# user_info = api_client.get_user_info(access_token)
# print(user_info.attribute_map("name"))