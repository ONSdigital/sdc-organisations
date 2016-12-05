import os
import random
import re

first_names_file = os.path.abspath("test_data/first_names.txt")
last_names_file = os.path.abspath("test_data/last_names.txt")
surveys_file = os.path.abspath("test_data/surveys.txt")
companies_file = os.path.abspath("test_data/companies.txt")

person_counter = 1

def abbreviate(text):
    blacklist = ['and', 'of', 'in', 'the', 'by', 'for']
    words = re.findall('\w+', text)
    first_letters = [word[0] for word in words if word not in blacklist]
    return ''.join(first_letters).upper()

def people(number):
    global person_counter

    first = []
    with open(first_names_file) as first_names:
        for first_name in first_names:
            first.append(first_name.rstrip("\n").lower().capitalize())

    last = []
    with open(last_names_file) as last_names:
        for last_name in last_names:
            last.append(last_name.rstrip("\n").lower().capitalize())

    result = []
    for i in range(1, number):
        #person = {"name": random.choice(first) + " " + random.choice(last), "id": repr(person_counter)}
        person = {"name": first[i] + " " + last[i], "id": repr(person_counter)}
        result.append(person)
        person_counter += 1
        if person["id"] == "101":
            print(" 101 : " + repr(person))

    return result


def surveys():
    counter = 1
    result = []
    with open(surveys_file) as survey_names:
        for survey_name in survey_names:
            result.append({"name": survey_name.rstrip("\n"), "id": abbreviate(survey_name.rstrip("\n"))})
            counter += 1

    return result


def organisations():
    counter = 1
    result = []
    with open(companies_file) as organisation_names:
        for organisation_name in organisation_names:
            org_ref, org_name = organisation_name.split('|')
            result.append({"name": org_name.rstrip("\n"), "reference": org_ref})
            counter += 1

    return result
