# creating a token handler which is given by google to my app to gain access into user's gmail account
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle' #user's access and refresh token are store here.. basically login session

def get_gmail_credentials():

    creds=None

    # load existing token if exists
    if os.path.exists(TOKEN_FILE):
        try:
             with open(TOKEN_FILE,'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            creds = None

    # if no valid credentials, start auth flow or authenticate
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                # refresh expired token
                creds.refresh(Request())
            else:
                # start the auth flow - for first time login or no valid token
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'wb')as token:
                pickle.dump(creds,token)
        except Exception as e:
            raise RuntimeError(f"Failed to get Gmail credentials: {str(e)}")

    return creds