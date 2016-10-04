from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
import inspect



app = Flask(__name__)

# Enable cross-origin requests
CORS(app)

# Set up the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/models.db'
db = SQLAlchemy(app)





class Survey(db.Model):
    """
    The use of a Collection Instrument to obtain information on all
    or part of a population of interest.
    """
    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Survey %s>' % (self.name)

    def dict(self):
        return {"name": self.name}


class ReportingUnit(db.Model):
    """
    A Statistical Unit approached in connection with provision of a Response
    (potentially on behalf of other Statistical Units as well as itself).
    May be an individual or organisation.
    """
    # Columns
    id = Column(Integer, primary_key=True)
    unique_reference = Column(String(100))
    business_name = Column(String(255))

    def __init__(self, unique_reference=None, business_name=None):
        self.unique_reference = unique_reference
        self.business_name = business_name

    def __repr__(self):
        result = "<" + self.__class__.__name__
        for key, value in self.dict().items():
            result += " " + key + "=" + repr(value)
        return result + ">"

    def dict(self):
        result = dict(self.__dict__)
        del result["_sa_instance_state"]
        return result


# Survey model
class Test(db.Model):
    # Columns
    id = Column(Integer, primary_key=True)
    reference = Column(String(10))
    name = Column(String(255))

    def __init__(self, reference=None, name=None):
        self.reference = reference
        self.name = name

    def __repr__(self):
        return '<Survey %rs>' % self.name

    def json(self):
        return {"reference": self.reference,
                "name": self.name}


db.drop_all()
db.create_all()
print(ReportingUnit())
