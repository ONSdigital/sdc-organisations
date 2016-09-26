import os
import random

first_names_file = os.path.abspath("test_data/first_names.txt")
last_names_file = os.path.abspath("test_data/last_names.txt")
surveys_file = os.path.abspath("test_data/surveys.txt")
companies_file = os.path.abspath("test_data/companies.txt")

person_counter = 1


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
        person = {"name": random.choice(first) + " " + random.choice(last), "id": repr(person_counter)}
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
            result.append({"name": survey_name.rstrip("\n"), "id": "s" + repr(counter)})
            counter += 1

    return result


def organisations():
    counter = 1
    result = []
    with open(companies_file) as organisation_names:
        for organisation_name in organisation_names:
            result.append({"name": organisation_name.rstrip("\n"), "reference": "o" + repr(counter)})
            counter += 1

    return result
