import os
import sys
import json
import base64
import requests
import dotenv

ACCESS_TOKEN_URL = 'https://api.princeton.edu:443/token'
BASE_URL = 'https://api.princeton.edu:443/student-app/1.0.3'

# ENDPOINT = '/users'
ENDPOINT = '/courses/courses'
# ENDPOINT = '/users/full'

dotenv.load_dotenv()
CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']

def main():

     if (len(sys.argv) != 2):
         print('usage: %s term' % sys.argv[0], file=sys.stderr)
         sys.exit(1)

     netid = sys.argv[1]

     # Use the CONSUMER_KEY and CONSUMER_SECRET to get an access token.

     auth_header = CONSUMER_KEY + ":" + CONSUMER_SECRET
     auth_header = bytes(auth_header, 'utf-8')
     auth_header = base64.b64encode(auth_header)
     auth_header = auth_header.decode('utf-8')
     auth_header = 'Basic ' + auth_header
     response = requests.post(
         ACCESS_TOKEN_URL,
         data={'grant_type': 'client_credentials'},
         headers={'Authorization': auth_header})
     response_json_doc = json.loads(response.text)
     access_token = response_json_doc['access_token']

     # Use the access token to get the data.

     auth_header = 'Bearer ' + access_token
     print('Access token:', access_token)
     data_url = BASE_URL + ENDPOINT

     response = requests.get(
         data_url,
         params={'uid': netid},
         headers={'Authorization': auth_header})
     response_json_doc = json.loads(response.text)

     # Pretty-print the data.

     print(json.dumps(response_json_doc, indent=3))

if __name__ == '__main__':
     main()