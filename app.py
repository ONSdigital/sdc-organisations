import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from jwt import encode, decode
from jose.exceptions import JWSError
from copy import copy


app = Flask(__name__)
CORS(app)

# NB: for delegation we could add start/end dates to associations,
#     which might enable us to fulfil a bunch of user needs (e.g. maternity leave).

reporting_units = [
    {
        "reference": "222",
        "name": "Nursing Ltd."
    },
    {
        "reference": "223",
        "name": "Pontypandy fire station."
    },
    {
        "reference": "224",
        "name": "Morgan Stanley"
    }
]


# This provides a many-to-many mapping between respondent, reporting_unit and survey_id.
# These associations could carry additional information, such as validity dates (e.g. for maternity leave)
# and information about who created/delegated access.

associations = [
    {
        "respondent_id": "101",
        "reporting_unit": "222",
        "survey_id": "023"
    },
    {
        "respondent_id": "102",
        "reporting_unit": "223",
        "survey_id": "023"
    },
    {
        "respondent_id": "103",
        "reporting_unit": "223",
        "survey_id": "023"
    },
    {
        "respondent_id": "104",
        "reporting_unit": "224",
        "survey_id": "023"
    }
]


@app.route('/', methods=['GET'])
def info():
    return """
        </ul>
            <li>Try GET to <a href="/reporting_units">/reporting_units</a></li>
            <li>Pass a "token" header that includes a respondent_id.</li>
            <li>This will return the set of organisations and surveys for those organisations that
            the respondent is associated with.</li>
        </ul>
        """


def collate_reporting_unit(reporting_unit, result):
    for existing in result["reporting_units"]:
        if existing["reference"] == reporting_unit["reference"]:
            return existing
    ru = copy(reporting_unit)
    result["reporting_units"].append(ru)
    ru["surveys"] = []
    return ru


def collate_survey(survey_id, reporting_unit):
    if survey_id not in reporting_unit["surveys"]:
        reporting_unit["surveys"].append(survey_id)


def add_association(association, result):
    for reporting_unit in reporting_units:
        if reporting_unit["reference"] == association["reporting_unit"]:
            # De-duplicate reporting units:
            ru = collate_reporting_unit(reporting_unit, result)
            # Ensure we avoid duplicate survey IDs:
            collate_survey(association["survey_id"], ru)


@app.route('/reporting_units', methods=['GET'])
def reporting_unit_associations():
    token = request.headers.get("token")
    data = validate_token(token)

    data["reporting_units"] = []
    if data and "respondent_id" in data:
        for association in associations:
            if association["respondent_id"] == data["respondent_id"]:
                add_association(association, data["reporting_units"])

        token = encode(data)
        return jsonify({"data": data, "token": token})
    return known_error("Please provide a 'token' header containing a JWT with a respondent_id value.")


@app.errorhandler(401)
def unauthorized(error=None):
    app.logger.error("Unauthorized: '%s'", request.data.decode('UTF8'))
    message = {
        'status': 401,
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 401

    return resp


@app.errorhandler(400)
def known_error(error=None):
    app.logger.error("Bad request: '%s'", request.data.decode('UTF8'))
    message = {
        'status': 400,
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def unknown_error(error=None):
    app.logger.error("Error: '%s'", request.data.decode('UTF8'))
    message = {
        'status': 500,
        'message': "Internal server error: " + repr(error),
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


def validate_token(token):

    if token:
        try:
            return decode(token)
        except JWSError:
            return ""


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
