import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from jwt import encode, decode
from jose.exceptions import JWTError
from copy import copy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
import json


app = Flask(__name__)

# Enable cross-origin requests
CORS(app)

# Set up the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/sdc-organisations.db'
db = SQLAlchemy(app)


# Association model
# NB: for delegation we could add start/end dates to associations,
#     which might enable us to fulfil a bunch of user needs (e.g. maternity leave).
class Association(db.Model):

    # Columns
    id = Column(Integer, primary_key=True)
    organisation = Column(String(10))
    survey = Column(String(10))
    respondent = Column(String(10))

    def __init__(self, organisation=None, survey=None, respondent=None):
        self.organisation = organisation
        self.survey = survey
        self.respondent = respondent

    def __repr__(self):
        return '<Association %r %r %r>' % (self.organisation, self.survey, self.respondent)

    def json(self):
        return {"organisation": self.organisation,
                "survey": self.survey,
                "respondent": self.respondent}


# Organisation model
class Organisation(db.Model):

    # Columns
    id = Column(Integer, primary_key=True)
    reference = Column(String(10))
    name = Column(String(255))

    def __init__(self, reference=None, name=None):
        self.reference = reference
        self.name = name

    def __repr__(self):
        return '<Organisation %r>' % self.name

    def json(self):
        return {"reference": self.reference,
                "name": self.name}


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


@app.route('/reporting_units', methods=['GET'])
def reporting_unit_associations():
    token = request.headers.get("token")
    data = validate_token(token)

    if data and "respondent_id" in data:

        result = {}

        # Load all associations for this user
        associations = Association.query.filter_by(respondent=data["respondent_id"])
        for association in associations:

            # Load the organisation for the current association
            organisation = Organisation.query.filter_by(reference=association.organisation).first()
            if organisation is not None:

                # Add the organisation to the result if necessary
                if association.organisation not in result:
                    result[association.organisation] = {"organisation": organisation.json(), "surveys": []}

                # Add the survey to the result
                surveys = result[association.organisation]["surveys"]
                surveys.append(association.survey)

        data["reporting_units"] = []
        for key, value in result.items():
            data["reporting_units"].append(value)

        print(json.dumps(data))

        token = encode(data)
        return jsonify({"data": data, "token": token})
    return unauthorized("Please provide a 'token' header containing a valid JWT with a respondent_id value.")


@app.errorhandler(401)
def unauthorized(error=None):
    app.logger.error("Unauthorized: '%s'", request.data.decode('UTF8'))
    message = {
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 401

    return resp


@app.errorhandler(400)
def known_error(error=None):
    app.logger.error("Bad request: '%s'", request.data.decode('UTF8'))
    message = {
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def unknown_error(error=None):
    app.logger.error("Error: '%s'", request.data.decode('UTF8'))
    message = {
        'message': "Internal server error: " + repr(error),
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


def validate_token(token):

    if token:
        try:
            return decode(token)
        except JWTError:
            return ""


def create_database():

    db.drop_all()
    db.create_all()


def create_organisations():

    reference = 1

    # Set up a lot of organisations:
    with open(os.path.abspath("test_data/words.txt")) as organisation_names:
        print("Generating organisations...")
        for organisation_name in organisation_names:
            if reference < 20000:
                organisation = Organisation(
                    name=organisation_name.rstrip("\n"),
                    reference="o"+repr(reference)
                )
                reference += 1
                db.session.add(organisation)

                if reference % 10000 == 0:
                    print(reference)

    print("Committing...")
    db.session.commit()
    print("Done!")

    # Just to see that test users are present
    print(Organisation.query.filter_by(id=1674).first().json())


def create_associations():
    # This provides a many-to-many mapping between respondent, reporting_unit and survey_id.
    # These associations could carry additional information, such as validity dates (e.g. for maternity leave)
    # and information about who created/delegated access.

    associations = [
        {
            "respondent_id": "101",
            "reporting_unit": "o1674",
            "survey_id": "023"
        },
        {
            "respondent_id": "101",
            "reporting_unit": "o1674",
            "survey_id": "024"
        },
        {
            "respondent_id": "101",
            "reporting_unit": "o1674",
            "survey_id": "025"
        },
        {
            "respondent_id": "102",
            "reporting_unit": "o8456",
            "survey_id": "023"
        },
        {
            "respondent_id": "103",
            "reporting_unit": "o223",
            "survey_id": "023"
        },
        {
            "respondent_id": "104",
            "reporting_unit": "o111",
            "survey_id": "023"
        }
    ]

    print("Creating associations...")
    for association in associations:

        record = Association(
            organisation=association["reporting_unit"],
            survey=association["survey_id"],
            respondent=association["respondent_id"]
        )
        if Association.query.filter_by(
                organisation=record.organisation,
                survey=record.survey,
                respondent=record.respondent
                ).first() is None:
            db.session.add(record)

    print("Committing...")
    db.session.commit()
    print("Done!")
    print(Association.query.all())


if __name__ == '__main__':

    # Create database
    create_database()
    create_organisations()
    create_associations()

    # Start server
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
