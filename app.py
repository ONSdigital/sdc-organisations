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

    engine = create_engine('sqlite:////tmp/sdc-organisations.db')
    session = sessionmaker()
    session.configure(bind=engine)
    records = []

    result = []

    counter = 1

    # Set up a lot of organisations:
    print("Generating organisations...")
    for organisation in organisations():
        if counter < 1000:
            record = Organisation(
                name=organisation["name"],
                reference=organisation["reference"]
            )
            counter += 1
            records.append(record)
            #db.session.add(record)
            result.append(record.json())

            if counter % 10000 == 0:
                print(counter)

    print("Committing...")
    #db.session.commit()
    s = session()
    s.bulk_save_objects(records)
    s.commit()
    print("Done!")
    print("Created " + repr(len(result)) + " organisations.")

    return result


def create_associations(organisations):
    # This provides a many-to-many mapping between respondent, reporting_unit and survey_id.
    # These associations could carry additional information, such as validity dates (e.g. for maternity leave)
    # and information about who created/delegated access.

    engine = create_engine('sqlite:////tmp/sdc-organisations.db')
    session = sessionmaker()
    session.configure(bind=engine)
    records = []

    print("Creating associations...")
    total = 0
    person_total = None
    collection_instruments = surveys()
    for organisation in organisations:
        #print("Associating for " + organisation["name"] + " [" + organisation["reference"] + "]")
        enrolments = random.sample(collection_instruments, random.randint(1, 5))
        organisation_people = people(random.randint(2, 10))
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
                #db.session.add(record)
                person_total = respondent["id"]
                total += 1

    print("Committing...")
    #db.session.commit()
    s = session()
    s.bulk_save_objects(records)
    s.commit()
    print("Done. Created " + str(total) + " associations and " + person_total + " people.")
    #print(Association.query.all())


if __name__ == '__main__':

    # Create database
    create_database()
    organisations = create_organisations()
    create_associations(organisations)

    # Start server
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
