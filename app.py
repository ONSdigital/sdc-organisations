import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from jwt import encode, decode
from jose.exceptions import JWTError
from copy import copy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
import json
from test_data.data_generator import surveys, organisations, people
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# service name (initially used for sqlite file name and schema name)
SERVICE_NAME = 'sdc-organisations'
ENVIRONMENT_NAME = os.getenv('ENVIRONMENT_NAME', 'dev')
PORT = int(os.environ.get('PORT', 5010))

app = Flask(__name__)

# Enable cross-origin requests
CORS(app)

# Set up the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/{}.db'.format(SERVICE_NAME))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
SCHEMA_NAME = None if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite') else '{}_{}'.format(ENVIRONMENT_NAME, SERVICE_NAME)

if os.getenv('SQL_DEBUG') == 'true':
    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


# Association model
# NB: for delegation we could add start/end dates to associations,
#     which might enable us to fulfil a bunch of user needs (e.g. maternity leave).
class Association(db.Model):
    __table_args__ = {'schema': SCHEMA_NAME}
    # Columns
    id = Column(Integer, primary_key=True)
    organisation = Column(String(11))
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
    __table_args__ = {'schema': SCHEMA_NAME}
    # Columns
    id = Column(Integer, primary_key=True)
    reference = Column(String(11))
    name = Column(String(255))

    def __init__(self, reference=None, name=None):
        self.reference = reference
        self.name = name

    def __repr__(self):
        return '<Organisation %r>' % self.name

    def json(self):
        return {"reference": self.reference,
                "name": self.name}


# Survey model
class Survey(db.Model):
    __table_args__ = {'schema': SCHEMA_NAME}
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


@app.route('/respondent_ids', methods=['GET'])
def respondent_ids():
    token = request.headers.get('token')
    if validate_token(token) is not None:

        reporting_unit_ref = request.args.get('reporting_unit_ref')
        survey_ref = request.args.get('survey_ref')

        if reporting_unit_ref and survey_ref:
            # Load all associations for this user
            associations = Association.query.filter_by(organisation=reporting_unit_ref, survey=survey_ref)
            result = {'respondents': [a.respondent for a in associations]}
            return jsonify(result)

        return unauthorized("Please provide reporting_unit_ref and survey_ref query string args.")

    return unauthorized("Please provide a 'token' header containing a valid JWT.")


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
    try:
        return decode(token)
    except Exception:
        return None


def recreate_database():
    if SCHEMA_NAME:
        sql = ('DROP SCHEMA IF EXISTS "{0}" CASCADE;'
               'CREATE SCHEMA IF NOT EXISTS "{0}"'.format(SCHEMA_NAME))
        db.engine.execute(sql)
    else:
        db.drop_all()
    db.create_all()


def create_organisations():
    records = []
    result = []
    counter = 1

    # Set up a lot of organisations:
    print("Generating organisations...")
    for organisation in organisations():
        if counter < 100:
            record = Organisation(
                name=organisation["name"],
                reference=organisation["reference"]
            )
            counter += 1
            records.append(record)
            db.session.add(record)
            result.append(record.json())

            if counter % 10000 == 0:
                print(counter)

    print("Committing...")
    db.session.commit()
    print("Done!")
    print("Created {} organisations.".format(len(result)))

    return result


def create_associations(organisations):
    # This provides a many-to-many mapping between respondent, reporting_unit and survey_id.
    # These associations could carry additional information, such as validity dates (e.g. for maternity leave)
    # and information about who created/delegated access.

    print("Creating associations...")
    records = []
    total = 0
    person_total = None
    collection_instruments = surveys()
    for organisation in organisations:
        #print("Associating for " + organisation["name"] + " [" + organisation["reference"] + "]")
        #enrolments = random.sample(collection_instruments, random.randint(1, 5))
        enrolments = collection_instruments[:5]

        #organisation_people = people(random.randint(2, 10))
        organisation_people = people(2)
        for enrolment in enrolments:
            #print(" - " + enrolment["name"] + " [" + enrolment["id"] + "]")
            #respondents = random.sample(organisation_people, random.randint(1, len(organisation_people)))
            for respondent in organisation_people:
                if respondent["id"] == "101":
                    print("   - " + respondent["name"] + " [" + respondent["id"] + "]")
                record = Association(
                    organisation=organisation["reference"],
                    survey=enrolment["id"],
                    respondent=respondent["id"]
                )
                if respondent["id"] == "101":
                    print(" *** 101")
                    print(organisation)
                    print(enrolment)
                    print(respondent)
                    print("organisation: " + record.organisation + " survey: " + record.survey + " respondent: " + record.respondent)
                records.append(record)
                db.session.add(record)
                person_total = respondent["id"]
                total += 1

    print("Committing...")
    db.session.commit()
    print("Done. Created {} associations and {} people.".format(total, person_total))
    #print(Association.query.all())


if __name__ == '__main__':
    # create and populate db only if in main process (Werkzeug also spawns a child process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        recreate_database()
        organisations = create_organisations()
        create_associations(organisations)

    # Start server
    app.run(debug=True, host='0.0.0.0', port=PORT)
