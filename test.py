import requests
from json import dumps
from decoder import get_json


def get(url, parameters={}, headers={}):
    response = requests.get(url, params=parameters, headers=headers)
    return process(response)


def post(url, json, headers={}):
    headers["Content-Type"] = "application/json"
    response = requests.post(url, data=json, headers=headers)
    return process(response)


def process(response):
    if response.status_code < 400:
        #print(response.status_code)
        return {
            "status": response.status_code,
            "json": response.json()
        }
    else:
        return {
            "status": response.status_code,
            "text": response.text
        }


# Test the authentication / authorisation API

component = "sdc-login-user"
url = "https://" + component + ".herokuapp.com"
# url = "http://localhost:5000"
print(" >>> Logging in and collecting tokens... (" + url + ")")


# Data we're going to work through


# Email address options

email = "florence.nightingale@example.com"
# email = "chief.boyce@example.com"
# email = "fireman.sam@example.com"
# email = "rob.dabank@example.com"


# Internet access code options

access_code = "abc123"
# access_code= "def456"
# access_code= "ghi789"


token = None
respondent = None

# Accout login

uri = "/login"
input = {"email": email}
result = post(url + uri, dumps(input))
if result["status"] == 200:
    json = result["json"]
    token = json["token"]
    respondent = get_json(token)
else:
    print("Error: " + str(result["status"]) + " - " + repr(result["text"]))

print(" <<< Token      : " + token)
print(" <<< Respondent : " + repr(respondent))


component = "sdc-organisations"
url = "https://" + component + ".herokuapp.com"
# url = "http://localhost:5001"
print("\n\n *** Testing " + component + " at " + url)


# Questionnaires for the respondent unit

uri = "/reporting_units"
if respondent:
    print("\n --- " + uri + " ---")
    print(" >>> Respondent ID: " + repr(respondent["respondent_id"]))
    result = get(url + uri, headers={"token": token})
    if result["status"] == 200:
        json = result["json"]
        print(json)
        #token = json["token"]
        #print(" <<< Token: " + token)
        #content = get_json(token)
        #print("Token content: " + dumps(content, sort_keys=True, indent=4, separators=(',', ': ')))
        #associations = json["associations"]
        #print(" <<< " + str(len(associations)) + " result(s): " + repr(associations))
    else:
        print("Error: " + str(result["status"]) + " - " + repr(result["text"]))
else:
    print(" * No respondent to query.")

