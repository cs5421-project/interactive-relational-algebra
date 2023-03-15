from typing import List

from ira.model.query import Query


def transform(binary_tree: List[str]):
    # TODO
    for index in range(len(binary_tree)):
        if index % 2 == 0:
            operator = binary_tree.pop()
            # TODO: Remove stub
    return Query("select * from sample;")


def map_ra_query_operator_to_sql_operator(operator: str):
    # TODO
    pass
