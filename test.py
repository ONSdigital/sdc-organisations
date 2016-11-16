import requests
from json import loads, dumps
from decoder import get_json
import unittest
from app import app
from jose import jwt
from jwt import encode, JWT_ALGORITHM
from app import recreate_database
from app import create_organisations
from app import create_associations

login_url = "https://sdc-login-user.herokuapp.com/login"

# Email address options
email = "florence.nightingale@example.com"
# email = "chief.boyce@example.com"
# email = "fireman.sam@example.com"
# email = "rob.dabank@example.com"
password = "password"

ok = 200
unauthorized = 401

valid_token = None


class ComponentTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_should_return_unauthorized_for_no_token(self):

        # Given
        # A request with no "token" header

        # When
        # We try to get reporting units
        response = self.app.get("/reporting_units")

        # Then
        # We should get a bad request status code
        self.assertEqual(response.status_code, unauthorized)

    def test_should_return_unauthorized_for_invalid_token(self):

        # Given
        # An invalid token
        token = jwt.encode({"respondent_id": "111"}, "wrong key", algorithm=JWT_ALGORITHM)

        # When
        # We try to get reporting units with the token
        response = self.app.get("/reporting_units", headers={"token": token})

        # Then
        # We should get an unauthorized status code
        self.assertEqual(response.status_code, unauthorized)

    def test_should_return_unauthorized_for_token_without_respondent_id(self):

        # Given
        # A token that doesn't contain a "respondent_id" value
        token = encode({"user_id": "111"})

        # When
        # We try to get reporting units with the token
        response = self.app.get("/reporting_units", headers={"token": token})

        # Then
        # We should get an unauthorized status code
        self.assertEqual(response.status_code, unauthorized)

    def test_should_return_reporting_units_for_valid_token(self):

        # Given
        # A valid token and an expected association
        token = encode({"respondent_id": "101"})

        # When
        # We try to get reporting units with the token
        response = self.app.get("/reporting_units", headers={"token": token})

        # Then
        # We should get a response containing "reporting_units" in the data and the updated token.
        self.assertEqual(response.status_code, ok)
        string = response.data.decode()
        json = loads(string)
        self.assertTrue("data" in json)
        self.assertTrue("reporting_units" in json["data"])
        self.assertTrue("token" in json)
        self.assertTrue("reporting_units" in get_json(json["token"]))
        print(json)


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


def get(url, parameters=None, headers=None):
    if parameters is None:
        parameters = {}
    if headers is None:
        headers = {}
    response = requests.get(url, params=parameters, headers=headers)
    return process(response)


def post(url, json, headers=None):
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"
    response = requests.post(url, data=json, headers=headers)
    return process(response)


def log_in():
    global valid_token
    # Account login
    print(" >>> Logging in and collecting tokens... (" + login_url + ")")
    message = {"email": email, "password": password}
    result = post(login_url, dumps(message))
    if result["status"] == 200:
        json = result["json"]
        valid_token = json["token"]
    else:
        print("Error: " + str(result["status"]) + " - " + repr(result["text"]))
    print(" <<< Token      : " + valid_token)


if __name__ == '__main__':
    log_in()

    # Create database
    recreate_database()
    organisations = create_organisations()
    create_associations(organisations)

    unittest.main()

