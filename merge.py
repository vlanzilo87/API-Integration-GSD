from __future__ import print_function

from datetime import date

import sys

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from docusign_esign import *
from docusign_esign import ApiClient
from docusign_esign import ApiException
from docusign_esign import EnvelopesApi
from docusign_esign import EnvelopeDefinition
from docusign_esign import Tabs
from docusign_esign import TemplateRole
from docusign_esign import Text

from sdp_logger import create_logger, log 

the_logger = create_logger(__file__)
the_logger.setup_syslog("syslog")
the_logger.setup_stream_out()
the_logger.setup_file_out("logs.txt")
#the_logger.smtp_handler()               # only enable on server

api_exception = ApiException()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEETS = ["1nFA0zdWqIHRxaJqkcvXMvgrMXD3MfIvUuujVpKmHIpE", "1vIhG_nroSV3_O5O1NTI9l4yOhwIZP-XFgDmdJuGwkZU"]

def google_authorization():   # From Google
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def docusign_authorize(keys_file):   # From DocuSign
    global access_token

    # Instantiating the ApiClient
    api_client = ApiClient()

    with open(keys_file) as fill:
        private_key = fill.read().encode("ascii").decode("utf-8")

    my_app = api_client.request_jwt_user_token(
        client_id="52258420-66d5-4939-b454-079a8f051514",
        user_id="c87612fa-e554-4317-a2fa-6b34ab4ff0cc",
        oauth_host_name="account.docusign.com", # Authorization server (demo = 'account-d.docusign.com')
        private_key_bytes=private_key,
        expires_in=3600,
        scopes=["signature", "impersonation"]
    )

    access_token = my_app.access_token

    print("Authorization granted!")
    
    # Setting the base path
    api_client.host = "https://na3.docusign.net/restapi" # Base path (demo = 'https://demo.docusign.net/restapi')

    # Setting the HTTP header with authentication token
    api_client.set_default_header("Authorization", f"Bearer {access_token}")

    return api_client

def read_values(spreadsheet_id, range_name, creds):   # From Google
    """Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """

    try:
        service = build('sheets', 'v4', credentials=creds)

        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

        rows = result.get('values', [])

        #if not rows:
        #    print("No data found.")
        #    return
        
        print(f"{len(rows)} rows retrieved.")
        print(rows)
        return result
    except HttpError as error:
        print(f"An error occured: {error}")
        return error

def update_values(spreadsheet_id, range_name, value_input_option, _values, creds):   # From Google
    """Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """

    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """

    try:
        service = build('sheets', 'v4', credentials=creds)
        values = [
            # Cell values ... no square brackets
        ],
        # Additional rows ...
        body = {
            'values': _values
        }
        result = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption=value_input_option, body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
        print(result)
        return result
    except HttpError as error:
        print(f"An error occured: {error}")
        return error

def get_rows_google_sheet(spreadsheet_id, creds):
    # Retrieve values from google sheet to send to generate docusign envelope only if the first 6 columns are completed and the last two columns are empty. 
    result = read_values(spreadsheet_id, "A2:G", creds)
    # Add logger
    log().info("Retrieving results from Google Sheet.")

    rows = result.get('values', [])
    row_id = 1
    new_dict = {}

    for row in rows:
        row_id += 1
        print(row_id)
        print(row)
        if len(row) != 6: # DO NOT send to docusign if not enough fields filled out
            print("ERROR: Number of cells present in row is either too many or too few.")
        elif (row[0] != '' and row[1] != '' and row[2] != '' and row[3] != '' and row[4] != '' and row[5] == 'Send'):
            # SEND/WRITE to docusign if required fields are filled out and the last two fields are empty
            new_dict[row_id] = row
        else:
            print("ERROR: Cell values are incorrect.")

    return new_dict

def create_the_envelope(keys_file):

    api_client = docusign_authorize(keys_file)

    # Set up envelope parameters
    envelope_args = {
        "template_id": "c42816d6-c20e-41e6-a46a-153e9942c068",
    }

    args = {
        "account_id": "8922693f-285d-465d-bf7a-dc2b8766737e",
        "envelope_args": envelope_args
    }

    creds = google_authorization()

    for spreadsheet in SPREADSHEETS:
        # Add for loop within this for loop to include sub sheets in each spreadsheet?
        # Retrieve new_list returned from Google Sheet
        values_from_google_list = get_rows_google_sheet(spreadsheet, creds)

        # Loop through list of lists
        for row_id, each_row in values_from_google_list.items():

            text1 = Text(
                tab_label="employee id",
                value=each_row[0]
            )

            text2 = Text(
                tab_label="name",    # This value can come from template roles or Google sheet
                value=each_row[1]
            )

            text3 = Text(
                tab_label="device serial number",
                value=each_row[3]
            )
    
            text4 = Text(                       
                tab_label="device assigned",
                value=each_row[4]
            )

            tabs = Tabs(text_tabs=[text1, text2, text3, text4])

            # Instantiating the EnvelopesApi
            envelope_api = EnvelopesApi(api_client)

            # Creating the envelope definition
            envelope_definition = EnvelopeDefinition(
                status = "sent",
                template_id = envelope_args['template_id']
            )

            # Create template role elements
            signer = TemplateRole(
                email = each_row[2],
                name = each_row[1],
                role_name = "SDP Employee",
                tabs = tabs
            )

            # Add the TemplateRole objects to the envelope object
            envelope_definition.template_roles = [signer]
    
            #**TRY/EXCEPT**#
            try:
                results = envelope_api.create_envelope(
                    account_id = args['account_id'],
                    envelope_definition = envelope_definition
                )

            except Exception as api_exception:
                print("Got ya!")
                print(api_exception)
                log().exception("EXCEPTION!")
                print("End Got ya!")
            
            else:
                envelope_id = results.envelope_id
                # Checking sent status
                if (results.status != 'sent'):
                    log().critical(f"Envelope '{envelope_id}' for '{signer.name}' at '{signer.email}' has not been sent!")
                else:
                    print(f"Envelope '{envelope_id}' has been generated and sent to '{signer.name}' at '{signer.email}'.")
                    # Add logger
                    log().info(f"Envelope '{envelope_id}' has been generated and sent to '{signer.name}' at '{signer.email}'.")
            
                    print("Envelope Status: " + results.status)

                    # Update status column with 'Sent'
                    update_values(spreadsheet, f"G{row_id}", "USER_ENTERED", [['Sent']], creds)
                    # Add logger
                    log().info("Updating status column to 'Sent'.")

                    # Update date column
                    print(date.today().strftime("%m/%d/%y"))
                    update_values(spreadsheet, f"H{row_id}", "USER_ENTERED", [[date.today().strftime("%m/%d/%y")]], creds)
                    # Add logger
                    log().info("Updating date column.")

                    # Add envelope ID to column 'I' - *could be a column at the end
                    update_values(spreadsheet, f"I{row_id}", "USER_ENTERED", [[envelope_id]], creds)
                    # Add logger
                    log().info("Updating envelope ID.")

# Check envelope status
def check_status(keys_file):
    api_client = docusign_authorize(keys_file)

    envelope_api = EnvelopesApi(api_client)

    args = {
        "account_id": "8922693f-285d-465d-bf7a-dc2b8766737e"
    }

    creds = google_authorization()

    for spreadsheet in SPREADSHEETS:
    
        result = read_values(spreadsheet, "G2:I", creds)
        # Add logger
        log().info("Retrieving envelope IDs and statuses.")

        rows = result.get('values', [])
        row_id = 1

        for row in rows:
            row_id += 1
            print(row)
            print(len(row))

            if len(row) == 3:
                if row[0] == 'Sent':
                    envelope_id = row[2]
                
                    #**TRY/EXCEPT**#
                    try:
                        envelope_results = envelope_api.get_envelope(args['account_id'], envelope_id)
                        status = envelope_results.status
                        print(status)

                    except Exception as api_exception:
                        print("Got ya!")
                        print(api_exception)
                        log().exception("EXCEPTION!")
                        print("End got ya!")

                    else:        
                        if status == 'completed':
                            update_values(spreadsheet, f"G{row_id}", "USER_ENTERED", [['Completed']], creds)
                            # Add logger
                            log().info("Updating status column to 'Completed'.")
                        elif status == 'voided':
                            update_values(spreadsheet, f"G{row_id}", "USER_ENTERED", [['Voided']], creds)
                            # Add logger
                            log().info("Updating status column to 'Voided'.")
                            
# Report errors - SMTP
def report_error():
    pass

# VS Code Terminal: Run application with file name "keys.txt"
# MS Command Prompt: In directory, "python Merger.py keys.txt"

def main():
    keys_file = sys.argv[1]
    create_the_envelope(keys_file)
    check_status(keys_file)

if __name__ == '__main__':
    main()