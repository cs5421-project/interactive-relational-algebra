from collections import namedtuple
from sqlite3 import Cursor

from django.db import connection

from ira.model.output import Output
from ira.model.query import Query
from http import HTTPStatus


def execute_sql_query(query: Query) -> Output:
    with connection.cursor() as cursor:
        try:
            cursor.execute(query)
            if query.is_dql():
                return Output(HTTPStatus.OK,
                              result=fetch_all(cursor))
            return Output(HTTPStatus.OK,
                          message="Query {query} has updated {row_number} row(s)."
                          .format(query=query.value, row_number=cursor.rowcount))
        except Exception as exception:
            # TODO: Give specific status
            return Output(HTTPStatus.BAD_REQUEST,
                          message="Query {query} has some logic issue; "
                                  "See exception message:{exception_message}"
                          .format(query=query, exception_message=exception))


# TODO: Move over to POSTGRES Cursor
def fetch_all(cursor: Cursor):
    column_names = [column[0] for column in cursor.description]
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip(column_names, row)))
    return result
