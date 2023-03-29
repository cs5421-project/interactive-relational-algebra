from typing import List

from ira.constants import TOKEN_TYPE_OPERATORS, TOKEN_TYPE_TO_UNARY_OPERATOR, TOKEN_TYPE_TO_BINARY_OPERATOR
from ira.enum.token_type import TokenType
from ira.model.attributes import Attributes
from ira.model.query import Query
from ira.model.token import Token

N_JOIN_BASE_QUERY = ["select * from {{}} natural {join_type} join {{}};",
                     "select * from {{}} {join_type} join {{}} on {{conditions}};"]


def get_n_join_queries(join_type):
    return tuple(query.format(join_type=join_type) for query in N_JOIN_BASE_QUERY)


QUERY_MAPPER = {TokenType.SELECT: "select * from {{}} where {conditions};",
                TokenType.PROJECTION: "select distinct {column_names} from {{}};",
                TokenType.NATURAL_JOIN: "select * from {} natural join {};",
                # TODO: Add another variant with where clause to support conditional join
                TokenType.IDENT: "select * from {table_name};",
                TokenType.CARTESIAN: "select * from {} cross join {};",
                TokenType.UNION: "{} union {}",
                TokenType.INTERSECTION: "{} intersect {}",
                TokenType.DIFFERENCE: "{} except {}",
                TokenType.LEFT_JOIN: get_n_join_queries("left"),
                TokenType.RIGHT_JOIN: get_n_join_queries("right"),
                TokenType.FULL_JOIN: get_n_join_queries("full"),
                TokenType.ANTI_JOIN: ("select * from {left_table_name} natural left join {right_table_name} where ("
                                      "select column_name from"
                                      "information_schema.columns where table_name={left_table_name} and column_name "
                                      "in (select column_name from information_schema.columns where table_name={"
                                      "right_table_name});",
                                      "select * from {} left join {} on {conditions} where {null_conditions}")}


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
                    raise Exception("Syntactic exception: RA query not well formed; "
                                    "Possible reason: binary operator ({{parent_token}}) not "
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

        elif current_token.type in (TokenType.NATURAL_JOIN, TokenType.RIGHT_JOIN, TokenType.FULL_JOIN,
                                    TokenType.LEFT_JOIN, TokenType.FULL_JOIN, TokenType.CARTESIAN, TokenType.UNION,
                                    TokenType.INTERSECTION, TokenType.DIFFERENCE):

            query = QUERY_MAPPER[current_token.type]
            is_certain_join = current_token.type in (TokenType.LEFT_JOIN,
                                                     TokenType.RIGHT_JOIN,
                                                     TokenType.FULL_JOIN)
            if current_token.attributes and is_certain_join:
                # If certain join operator has attributes, it implies that it is a type of conditional/equi join
                conditions = sanitise(current_token.attributes, current_token.type)
                query = query[-1].format("{}", "{}", conditions=conditions)
            elif is_certain_join:
                query = query[0]
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
                query = stored_query.format(query)
        return Query(query)
    else:
        raise Exception("Empty relational algebra given")


def process_query_stack(query_stack, level, current_query):
    stored_query, stored_token = query_stack.pop()
    upcoming_operator_and_index = get_upcoming_operator_token(query_stack)
    index = upcoming_operator_and_index[-1] if upcoming_operator_and_index else None
    operator_token = upcoming_operator_and_index[0] if upcoming_operator_and_index else None
    if is_alias_not_needed(index, operator_token, query_stack, upcoming_operator_and_index, None):
        # For top level union, intersect or difference operation where operands don't involve subqueries
        parent_query, _ = query_stack.pop()
        return parent_query.format(current_query.rstrip(';'), stored_query), None
    if stored_query is None:
        # stored_query is None for an identifier token dealing with binary op.
        parent_query, _ = query_stack.pop()
        if is_alias_not_needed(index, operator_token, query_stack, upcoming_operator_and_index, None):
            # Fetches index of the upcoming binary operator and then relevant query, insert the current query as
            #  an operand to it, and update current query as stored_query + parent_query
            binary_token, index = get_upcoming_operator_token(query_stack, True)
            if binary_token:
                query_stack[index] = (query_stack[index][0].format(current_query, "{}"), query_stack[index][-1])
                return parent_query.format(stored_token.value), stored_query

            parent_query, _ = query_stack.pop()
            return parent_query.format(current_query.rstrip(';'), stored_query), stored_query

        # Do not need an alias if it is a top level query
        level = get_level(query_stack, level)
        binary_token, index = get_upcoming_operator_token(query_stack, True)
        if binary_token:
            query_stack[index] = (query_stack[index][0].format(current_query, "{}"), query_stack[index][-1])
            return get_query_with_alias(parent_query.format(stored_token.value).rstrip(';'), level), stored_query
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
    return upcoming_operator_and_index and len(query_stack) - index == difference and operator_token.type in (
        TokenType.UNION,
        TokenType.INTERSECTION,
        TokenType.DIFFERENCE)


def get_upcoming_operator_token(query_stack, is_binary=None):
    operator = TOKEN_TYPE_OPERATORS
    if is_binary is not None:
        operator = TOKEN_TYPE_TO_BINARY_OPERATOR if is_binary else TOKEN_TYPE_TO_UNARY_OPERATOR
    for index in reversed(range(len(query_stack))):
        if query_stack[index][-1].type in operator:
            return query_stack[index][-1], index
    return None, None


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
    elif token_type in (TokenType.SELECT, TokenType.NATURAL_JOIN,
                        TokenType.FULL_JOIN, TokenType.RIGHT_JOIN,
                        TokenType.LEFT_JOIN):
        query_segment = str(attributes)
        for column_name in attributes.column_names:
            query_segment = query_segment.replace(column_name, '"{column_name}"'
                                                  .format(column_name=column_name))
        return query_segment
