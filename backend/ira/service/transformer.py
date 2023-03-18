from typing import List

from ira.constants import TokenType, LOGICAL_OPERATORS, COMPARATIVE_OPERATORS
from ira.model.attributes import Attributes
from ira.model.query import Query
from ira.model.token import Token
from ira.service.util import split_string, is_binary_operator

QUERY_MAPPER = {TokenType.SELECT: "select * from {{}} where {conditions};",
                TokenType.PROJECTION: "select {column_names} from {{}};",
                TokenType.NATURAL_JOIN: "select * from {} natural join {};",
                TokenType.IDENT: "select * from {table_name};"}


def transform(parsed_postfix_tokens: List[Token]) -> Query:
    # TODO: Add support for other operators
    # TODO: Do validation and further sanitation while parsing and not here
    query_stack = []
    while parsed_postfix_tokens or query_stack:
        current_token = parsed_postfix_tokens.pop()
        if current_token.type == TokenType.IDENT and len(parsed_postfix_tokens) == 0:
            return generate_query(query_stack, current_token)
        elif current_token.type == TokenType.IDENT and query_stack:
            parent_token = query_stack[-1][-1]
            # Logically this token is involved in a binary op, since if there are more than one table identifier,
            # it implies that there is a binary operation between them either directly or indirectly.
            if parent_token:
                query_stack.append((None, current_token))
            else:
                raise Exception("RA query not well formed; Possible reason: binary operator ({{parent_token}}) not "
                                "getting 2 operands.".format(parent_token=parent_token))

        elif current_token.type == TokenType.SELECT:
            conditions = sanitise(current_token.attributes, current_token.type)
            query = QUERY_MAPPER[current_token.type].format(conditions=conditions)
            query_stack.append((query, current_token))

        elif current_token.type == TokenType.PROJECTION:
            column_names = sanitise(current_token.attributes, current_token.type)
            query = QUERY_MAPPER[current_token.type].format(column_names=column_names)
            query_stack.append((query, current_token))

        elif current_token.type == TokenType.NATURAL_JOIN:
            # TODO accept conditional attribute once tokenizer and parser allows it
            query = QUERY_MAPPER[current_token.type]
            query_stack.append((query, current_token))


def generate_query(query_stack, token):
    number_of_subquery = 0
    if query_stack:
        query, stored_query = process_query_stack(query_stack, token, number_of_subquery,
                                                  None)
        while query_stack:
            is_top_level_query = len(query_stack) == 1
            if not is_top_level_query:
                number_of_subquery += 1
                query, stored_query = process_query_stack(query_stack, token,
                                                          number_of_subquery,
                                                          query)
            else:
                stored_query, stored_token = query_stack.pop()
                if stored_token.type == TokenType.SELECT:
                    for column_name in stored_token.attributes.column_names:
                        # Mandatory so that postgres is able to find the column name associated with a subquery;
                        alias_prefixed_column_name = 'q{number_of_subquery}."{column_name}"' \
                            .format(number_of_subquery=number_of_subquery,
                                    column_name=column_name.capitalize())
                        stored_query = stored_query.replace('"{}"'.format(column_name), alias_prefixed_column_name)
                query = "{}".format(stored_query.format(query))
        return Query(query)
    else:
        return Query(QUERY_MAPPER[TokenType.IDENT].format(table_name=token.value))


def process_query_stack(query_stack, token, level, current_query):
    stored_query, stored_token = query_stack.pop()
    current_query = token.value if current_query is None else current_query
    if stored_query is None:
        # stored_query is None for an identifier token dealing with binary op.
        parent_query, _ = query_stack.pop()
        # Do not need an alias if it is a top level query
        level = None if len(query_stack) == 0 else level
        query = get_query_with_alias(parent_query.format(current_query, stored_token.value), level)
    else:
        # Unary operation
        query = get_query_with_alias(stored_query.format(current_query), level)
    return query, stored_query


def get_query_with_alias(query, level):
    """
    Adding alias as postgres must need alias for sub-queries
    """
    if level is not None:
        return "({}) as q{}".format(query.rstrip(';'), level)
    else:
        return query


def sanitise(attributes: Attributes, token_type: TokenType):
    """
    Using quoted identifiers to avoid ambiguity.
    Surrounding column name with " just in case if column name contain characters like "." etc
    """
    if token_type == TokenType.PROJECTION:
        return ",".join('"{column_name}"'.format(column_name=column_name)
                        for column_name in attributes.get_column_names())
    elif token_type == TokenType.SELECT:
        query_segment = str(attributes)
        for column_name in attributes.get_column_names():
            query_segment = query_segment.replace(column_name, '"{column_name}"'
                                                  .format(column_name=column_name))
        return query_segment
