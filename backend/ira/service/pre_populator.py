from os.path import isfile, join

from sqlalchemy import create_engine

import pandas

from pathlib import Path
import os

import psycopg2


module_folder = Path(os.path.abspath(os.path.dirname(__file__)))
credential = {"user": "postgres", "password": "postgres"}
database_name = "ira"


def pre_populate():
    # instantiate_database()
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/ira")
    csv_file_paths = get_csv_file_paths()
    for csv_file_path in csv_file_paths:
        dataframe = pandas.read_csv(csv_file_path)
        dataframe.to_sql(str(csv_file_path).split('/').pop().split('.')[0],
                         engine, index=False)


def is_database_there():
    # TODO
    pass


def create_table():
    pass


def instantiate_database():
    # FIXME: psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed:
    #  FATAL:  Peer authentication failed for user "postgres"
    # Current work around: Manually instantiate database locally:
    # sudo -u postgres psql
    # create database ira;
    credentials = "user={user} password={password}".format(**credential)
    connection = psycopg2.connect(credentials)
    cursor = connection.cursor()

    connection.autocommit = True
    query = "create database {database}".format(database=database_name)

    try:
        cursor.execute(query)
    except Exception as exception:
        print("Exception occurred when trying to instantiate a database; {exception}".format(exception=exception))

    cursor.close()
    connection.close()


def get_csv_file_paths():
    """Obtains absolute paths for all csv files under resources folder"""
    resource_folder = module_folder.parent.absolute() \
        .joinpath("resources") \
        .joinpath("prepopulation")
    csv_file_paths = []
    for file_name in os.listdir(resource_folder):
        file_path = join(resource_folder, file_name)
        if isfile(file_path):
            csv_file_paths.append(file_path)
    return csv_file_paths


if __name__ == '__main__':
    pre_populate()
