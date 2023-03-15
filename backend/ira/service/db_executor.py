
from django.db import connection

from ira.model.output import Output
from ira.model.query import Query
from http import HTTPStatus


def execute_sql_query(query: Query) -> Output:
    with connection.cursor() as cursor:
        try:
            cursor.execute(query.value)
            if query.is_dql:
                return Output(HTTPStatus.OK,
                              query,
                              result=fetch_all(cursor))
            return Output(HTTPStatus.OK,
                          query,
                          message="Query {query} has updated {row_number} row(s)."
                                  .format(query=query.value, row_number=cursor.rowcount))
        except Exception as exception:
            return Output(HTTPStatus.BAD_REQUEST,
                          query,
                          message="Query {query} faced logic issue; "
                                  "See exception message:{exception_message}"
                                  .format(query=query.value, exception_message=exception))


def fetch_all(cursor):
    column_names = [column[0] for column in cursor.description]
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip(column_names, row)))
    return result
