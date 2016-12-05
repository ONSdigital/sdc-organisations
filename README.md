
External user association with RUs and surveys.

# Technical debt

All of the organisations, respondents, and the relationships between them, either come from text files or are being
generated. They are not coming from a real data source.

# sdc-organisations

This component provides access to RUs and surveys for a respondent. It also allows you to see, for a given RU, the respondent and survey combinations.

## Endpoints

The following endpoints are available on this service:

### /reporting_units

*GET* a list of all reporting units and the surveys for the logged-in user.

*NB* You'll need to provide your JWT token in a *token* header.

This endpoint returns a map of: 

```json
{"organisation_ref" : {
    "organisation": {
        "name": "..." , 
        "reference": "..." 
    }, 
    "surveys": [ 
        "... list of survey references ..."
    ]
}
```

### /respondent_ids

*GET* a list of all respondents for a given RU and survey combination.

*NB* You'll need to provide your JWT token in a *token* header.

This endpoint returns:

```json
{"respondents" : [ 
    "... list of respondent references ..."
  ]
}
```

## Links

Try:
 * https://sdc-organisations.herokuapp.com

## Setting up

Run the following from a terminal:

```bash
mkvirtualenv -p `which python3.5` sdc-organisations
pip install -r requirements.txt
```

## Running it

```bash
workon sdc-organisations
python3 app.py
```
