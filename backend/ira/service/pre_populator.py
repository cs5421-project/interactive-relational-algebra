from os.path import isfile, join

from sqlalchemy import create_engine

import pandas

from pathlib import Path
import os

from backend.settings import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD

MODULE_FOLDER = Path(os.path.abspath(os.path.dirname(__file__)))
DATABASE_URL = "postgresql://{user}:{password}@localhost:5432/{database}" \
    .format(database=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)


def pre_populate():
    engine = create_engine(DATABASE_URL)
    csv_file_paths = get_csv_file_paths()
    for csv_file_path in csv_file_paths:
        dataframe = pandas.read_csv(csv_file_path)
        try:
            dataframe.to_sql(csv_file_path.split('/').pop().split('.')[0],
                             engine, index=False)
        except Exception as exception:
            print(exception)


def get_csv_file_paths():
    """Obtains absolute paths for all csv files under resources folder"""
    resource_folder = MODULE_FOLDER.parent.absolute() \
        .joinpath("resources") \
        .joinpath("prepopulation")
    csv_file_paths = []
    for file_name in os.listdir(resource_folder):
        file_path = join(resource_folder, file_name)
        if isfile(file_path):
            csv_file_paths.append(str(file_path))
    return csv_file_paths


