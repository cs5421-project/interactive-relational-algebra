from typing import List

from ira.constants import TOKEN_TYPE_OPERATORS
from ira.enum.token_type import TokenType
from ira.model.attributes import Attributes
from ira.model.query import Query
from ira.model.token import Token

QUERY_MAPPER = {TokenType.SELECT: "select * from {{}} where {conditions};",
                TokenType.PROJECTION: "select distinct {column_names} from {{}};",
                TokenType.NATURAL_JOIN: "select * from {} natural join {};",
                TokenType.IDENT: "select * from {table_name};",
                TokenType.CARTESIAN: "select * from {} cross join {};",
                TokenType.UNION: "{} union {}",
                TokenType.INTERSECTION: "{} intersect {}",
                TokenType.DIFFERENCE: "{} except {}"}


def transform(parsed_postfix_tokens: List[Token]) -> Query:
    # TODO: Add support for other operators
    # TODO: Do validation and further sanitation while parsing and not here
    query_stack = []
    while parsed_postfix_tokens or query_stack:
        current_token = parsed_postfix_tokens.pop()
        if current_token.type == TokenType.IDENT:
            # TODO: Make this part of the logic simpler: Prolly link child token to each token (implicit linked list)
            if query_stack:
                parent_token = query_stack[-1][-1]
                ancestor_token = None
                if len(parsed_postfix_tokens) == 0:
                    if len(query_stack) >= 2:
                        ancestor_token = query_stack[-2][-1]
                    if ancestor_token and ancestor_token.type in [TokenType.UNION, TokenType.INTERSECTION,
                                                                  TokenType.DIFFERENCE]:
                        query = QUERY_MAPPER[current_token.type].format(table_name=current_token.value)
                    else:
                        query = current_token.value

                    query_stack.append((query, current_token))
                    return generate_query(query_stack)
                # Logically this token is involved in a binary op, since if there are more than one table identifier,
                # it implies that there is a binary operation between them either directly or indirectly.
                if parent_token.type not in [TokenType.UNION, TokenType.INTERSECTION, TokenType.DIFFERENCE]:
                    query_stack.append((None, current_token))
                elif not parent_token:
                    raise Exception("RA query not well formed; Possible reason: binary operator ({{parent_token}}) not "
                                    "getting 2 operands.".format(parent_token=parent_token))
                else:
                    query = QUERY_MAPPER[current_token.type].format(table_name=current_token.value)
                    query_stack.append((query, current_token))
            else:
                return Query(QUERY_MAPPER[current_token.type].format(table_name=current_token.value))
        elif current_token.type == TokenType.SELECT:
            conditions = sanitise(current_token.attributes, current_token.type)
            query = QUERY_MAPPER[current_token.type].format(conditions=conditions)
            query_stack.append((query, current_token))

        elif current_token.type == TokenType.PROJECTION:
            column_names = sanitise(current_token.attributes, current_token.type)
            query = QUERY_MAPPER[current_token.type].format(column_names=column_names)
            query_stack.append((query, current_token))

        elif current_token.type in [TokenType.NATURAL_JOIN, TokenType.CARTESIAN, TokenType.UNION,
                                    TokenType.INTERSECTION, TokenType.DIFFERENCE]:
            # TODO accept conditional attribute once tokenizer and parser allows it
            query = QUERY_MAPPER[current_token.type]
            query_stack.append((query, current_token))


def generate_query(query_stack):
    # TODO: Make logic simpler
    number_of_subquery = 0
    if query_stack:
        current_query, token = query_stack.pop()
        query, stored_query = process_query_stack(query_stack, number_of_subquery,
                                                  current_query)
        while query_stack:
            is_top_level_query = len(query_stack) == 1
            if not is_top_level_query:
                number_of_subquery += 1
                query, stored_query = process_query_stack(query_stack,
                                                          number_of_subquery,
                                                          query)
            else:
                stored_query, stored_token = query_stack.pop()
                if stored_token.type == TokenType.SELECT:
                    for column_name in stored_token.attributes.column_names:
                        # Mandatory so that postgres is able to find the column name associated with a subquery;
                        alias_prefixed_column_name = 'q{number_of_subquery}."{column_name}"' \
                            .format(number_of_subquery=number_of_subquery,
                                    column_name=column_name)
                        stored_query = stored_query.replace('"{}"'.format(column_name), alias_prefixed_column_name)
        return Query(query)
    else:
        raise Exception("Empty relational algebra given")


def process_query_stack(query_stack, level, current_query):
    stored_query, stored_token = query_stack.pop()
    upcoming_operator_and_index = get_upcoming_operator_token(query_stack)
    index = upcoming_operator_and_index[-1] if upcoming_operator_and_index else None
    operator_token = upcoming_operator_and_index[0] if upcoming_operator_and_index else None
    if is_alias_not_needed(index, operator_token, query_stack, upcoming_operator_and_index, None):
        # For top level union, intersect or difference operation were operands don't involve subqueries
        parent_query, _ = query_stack.pop()
        return parent_query.format(current_query.rstrip(';'), stored_query), None
    if stored_query is None:
        # stored_query is None for an identifier token dealing with binary op.
        parent_query, _ = query_stack.pop()
        if is_alias_not_needed(index, operator_token, query_stack, upcoming_operator_and_index, None):
            parent_query, _ = query_stack.pop()
            return parent_query.format(current_query.rstrip(';'), stored_query), None
        # Do not need an alias if it is a top level query
        level = get_level(query_stack, level)
        query = get_query_with_alias(parent_query.format(current_query, stored_token.value), level)
    else:
        # Unary operation
        if is_alias_not_needed(index, operator_token, query_stack, upcoming_operator_and_index, stored_query):
            return stored_query.format(current_query), stored_query
        level = get_level(query_stack, level)
        query = get_query_with_alias(stored_query.format(current_query), level)
    return query, stored_query


def is_alias_not_needed(index, operator_token, query_stack, upcoming_operator_and_index, stored_query):
    difference = 2 if stored_query else 1
    return upcoming_operator_and_index and len(query_stack) - index == difference and operator_token.type in [
        TokenType.UNION,
        TokenType.INTERSECTION,
        TokenType.DIFFERENCE]


def get_upcoming_operator_token(query_stack):
    for index in reversed(range(len(query_stack))):
        if query_stack[index][-1].type in TOKEN_TYPE_OPERATORS:
            return query_stack[index][-1], index


def get_level(query_stack, level):
    return None if len(query_stack) == 0 else level


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
