from functools import lru_cache
from typing import List

from ira.constants import TOKEN_TYPE_OPERATORS, TOKEN_TYPE_TO_UNARY_OPERATOR, TOKEN_TYPE_TO_BINARY_OPERATOR, AND
from ira.enum.token_type import TokenType
from ira.model.attributes import Attributes
from ira.model.query import Query
from ira.model.token import Token
from ira.service.pre_populator import TABLE_TO_COLUMN_NAMES

N_JOIN_BASE_QUERY = ["select * from {{}} natural {join_type} join {{}};",
                     "select * from {{}} {join_type} join {{}} on {{conditions}};"]


def get_n_join_queries(join_type):
    return tuple(query.format(join_type=join_type) for query in N_JOIN_BASE_QUERY)


ANTI_JOIN_RIGHT_ALIAS = "cq1"

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
                TokenType.DIVISION: "",
                TokenType.ANTI_JOIN: "select * from {{}}  natural left join {{}} as {anti_join_right_alias}"
                                     " where {null_conditions};"}


# TODO: Iterative version
def get_common_columns_for_anti_join(parsed_postfix_tokens: List[Token], index, common_columns, binary_operator_stack):
    if index < 0:
        raise Exception("Relational query is wrongly formed; Binary operator is missing operands")
    if len(parsed_postfix_tokens) == 2:
        if parsed_postfix_tokens[0].type == TokenType.IDENT and parsed_postfix_tokens[1].type == TokenType.IDENT:
            return TABLE_TO_COLUMN_NAMES[parsed_postfix_tokens[0].value].intersection(
                TABLE_TO_COLUMN_NAMES[parsed_postfix_tokens[1].value])
        else:
            raise Exception("Relational query is wrongly formed; Binary operator is missing operands")
    current_token = parsed_postfix_tokens[index]
    if current_token.type == TokenType.IDENT:
        if index == 0:
            if len(binary_operator_stack) == 0 or (
                    len(binary_operator_stack) == 1 and binary_operator_stack[-1][-1] == 1):
                return TABLE_TO_COLUMN_NAMES[current_token.value], index
            else:
                raise Exception("Relational query is wrongly formed; Binary operator is missing operands")
        elif binary_operator_stack:
            stored_token, number_of_binary_operators_seen = binary_operator_stack[-1]
            if number_of_binary_operators_seen == 1:
                binary_operator_stack.pop()
                return TABLE_TO_COLUMN_NAMES[current_token.value], index
            else:
                binary_operator_stack[-1] = (stored_token, 1)
                right_side_operand_columns = TABLE_TO_COLUMN_NAMES[current_token.value]
                left_side_operand_common_column, left_side_index = get_common_columns_for_anti_join(
                    parsed_postfix_tokens, index - 1, common_columns,
                    binary_operator_stack)
                # if union  or difference or intersect prefer the left operand over the right  one, since the
                # assumption for this operator is that the number of columns are same and the column types are same.
                if stored_token.type in (TokenType.UNION, TokenType.DIFFERENCE, TokenType.INTERSECTION):
                    if len(left_side_operand_common_column) != len(right_side_operand_columns):
                        raise Exception("Relational query is wrongly formed; Operator: {token} is supposed to have the"
                                        " same number of columns".format(token=current_token))
                    return left_side_operand_common_column, left_side_index
                # if natural join or anti join use intersection.
                elif stored_token.type in (TokenType.NATURAL_JOIN, TokenType.ANTI_JOIN):
                    return right_side_operand_columns \
                        .intersection(left_side_operand_common_column), left_side_index

                # if division, then subtract the right one from the left one;
                elif stored_token.type == TokenType.DIVISION:
                    if len(left_side_operand_common_column) < len(right_side_operand_columns):
                        raise Exception("Relational query is wrongly formed; Division operator expects the right"
                                        " hand operand to be a proper subset of the left hand operand")
                    return right_side_operand_columns.difference(left_side_operand_common_column), left_side_index

                # if other join, cross join
                return right_side_operand_columns.union(left_side_operand_common_column), left_side_index
    elif current_token.type in TOKEN_TYPE_TO_BINARY_OPERATOR:
        # Keeping track of token and the number of identifiers  yet to see
        binary_operator_stack.append((current_token, 2))
        if index == len(parsed_postfix_tokens) - 1:
            # Starting point of anti-join
            right, last_reached_index = get_common_columns_for_anti_join(parsed_postfix_tokens, index - 1,
                                                                         common_columns,
                                                                         binary_operator_stack)
            left, _ = get_common_columns_for_anti_join(parsed_postfix_tokens, last_reached_index - 1, common_columns,
                                                       binary_operator_stack)
            return left.intersection(right)
    elif current_token.type == TokenType.PROJECTION:
        return current_token.attributes.get_column_names()
    return get_common_columns_for_anti_join(parsed_postfix_tokens, index - 1, common_columns, binary_operator_stack)


def generate_null_condition_for_anti_join(common_column_names, alias):
    result = ""
    for index in range(len(common_column_names)):
        and_clause = AND if index + 1 != len(common_column_names) else ""
        result += alias + '."' + common_column_names[index] + '" = null ' + and_clause + " "
    return result


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

        elif current_token.type == TokenType.ANTI_JOIN:
            if current_token.attributes:
                raise Exception("Anti join implementation does not support conditional join")
            else:
                common_column_names = get_common_columns_for_anti_join(parsed_postfix_tokens,
                                                                       len(parsed_postfix_tokens) - 1, {}, [])
                if not common_column_names:
                    raise Exception(
                        "Logical error; There are no common columns for the relation/subquery for the anti join operator")
                null_conditions = generate_null_condition_for_anti_join(list(common_column_names),
                                                                        ANTI_JOIN_RIGHT_ALIAS)
                query = QUERY_MAPPER[current_token.type].format(null_conditions=null_conditions,
                                                                anti_join_right_alias=ANTI_JOIN_RIGHT_ALIAS)
                # TODO: Need to use those common columns and need to prefix the right table_name
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
                elif stored_token.type == TokenType.ANTI_JOIN:
                    if "as" in query[len(query_stack) - 5:]:
                        # alias keyword as is usually used in the last 5 characters q0
                        query = query[:query.rindex("as")]
                query = stored_query.format(query)
        return Query(query)
    else:
        raise Exception("Empty relational algebra given")


# TODO: refactor redundant code
def process_query_stack(query_stack, level, current_query):
    stored_query, stored_token = query_stack.pop()
    upcoming_operator_and_index = get_upcoming_operator_token(query_stack)
    index = upcoming_operator_and_index[-1] if upcoming_operator_and_index else None
    operator_token = upcoming_operator_and_index[0] if upcoming_operator_and_index else None
    if is_alias_not_needed(operator_token, index, query_stack, upcoming_operator_and_index, None):
        # Alias not needed for top level union, intersect or difference operation  and for anti-joins
        parent_query, parent_token = query_stack.pop()
        if "as" in current_query[len(current_query) - 5:]:
            # alias keyword as is usually used in the last 5 characters q0
            current_query = current_query[:current_query.rindex("as")]
        if parent_token.type == TokenType.ANTI_JOIN:
            return parent_query.format(current_query, stored_token.value), None
        return parent_query.format(current_query.rstrip(';'), stored_query), None
    if stored_query is None:
        # stored_query is None for an identifier token dealing with binary op.
        parent_query, parent_token = query_stack.pop()
        if is_alias_not_needed(operator_token, index, query_stack, upcoming_operator_and_index, None):
            # Fetches index of the upcoming binary operator and then relevant query, insert the current query as
            #  an operand to it, and update current query as stored_query + parent_query

            binary_token, index = get_upcoming_operator_token(query_stack, True)
            is_ancestor_binary = parent_query is None and stored_query is None and current_query is not None
            if is_ancestor_binary:
                # Scenario where ident, ident, operator and current_query already exist
                # Scenario where ident, ident, unary operator, binary operator and current_query already exist
                parent_binary_token, parent_binary_index = get_upcoming_operator_token(
                    query_stack[:len(query_stack) - 1],True)
                query_stack[parent_binary_index] = (query_stack[parent_binary_index][0].format(current_query, "{}"),
                                                    query_stack[parent_binary_index][-1])
                binary_query, binary_token = query_stack.pop()
                if binary_token.type == TokenType.ANTI_JOIN:
                    query = binary_query.format(stored_token.value, parent_token.value)
                else:
                    query = get_query_with_alias(binary_query.format(stored_token.value, parent_token.value), level)
                return query, binary_query

            if binary_token:
                query_stack[index] = (query_stack[index][0].format(current_query, "{}"), query_stack[index][-1])
                return parent_query.format(stored_token.value), stored_query

            parent_query, _ = query_stack.pop()
            return parent_query.format(current_query.rstrip(';'), stored_query), stored_query

        # Do not need an alias if it is a top level query
        level = get_level(query_stack, level)

        binary_token, index = get_upcoming_operator_token(query_stack, True)

        is_ancestor_binary = parent_query is None and stored_query is None and current_query is not None
        if is_ancestor_binary:
            # Scenario where ident, ident, operator and current_query already exist
            # Scenario where ident, ident, unary operator, binary operator and current_query already exist
            parent_binary_token, parent_binary_index = get_upcoming_operator_token(query_stack[:len(query_stack) - 1],
                                                                                   True)
            if is_alias_not_needed(parent_binary_token,is_simple_mode=True):
                if "as" in current_query[len(current_query) - 5:]:
                    # alias keyword as is usually used in the last 5 characters q0
                    current_query = current_query[:current_query.rindex("as")]
                elif stored_token.type == TokenType.IDENT and parent_token.type == TokenType.IDENT \
                        and current_query in TABLE_TO_COLUMN_NAMES:
                    # For right associative scenario, example: (sales) ∪ ((sales) ⨯ (products));
                    current_query = QUERY_MAPPER[TokenType.IDENT].format(table_name = current_query).rstrip(';')
                query_stack[parent_binary_index] = (query_stack[parent_binary_index][0].format(current_query, "{}"),
                                                    query_stack[parent_binary_index][-1])
            binary_query, binary_token = query_stack.pop()
            if binary_token.type == TokenType.ANTI_JOIN:
                query = binary_query.format(stored_token.value, parent_token.value)
            elif is_alias_not_needed(parent_binary_token, is_simple_mode=True):
                    query = binary_query.format(stored_token.value, parent_token.value)
            else:
                    query = get_query_with_alias(binary_query.format(stored_token.value, parent_token.value), level)
            return query, binary_query

        elif binary_token:
            parent_query = parent_token.value if not parent_query else parent_query
            if level == 0:
                # TODO check for any upcoming operator which does not need an alias
                return get_query_with_alias(parent_query.format(current_query,stored_token.value).rstrip(';'),
                                            level), stored_query

            query_stack[index] = (query_stack[index][0].format(current_query, "{}"), query_stack[index][-1])
            placeholder_length = parent_query.count("{}")

            placeholders = ["{}" for _ in range(placeholder_length - 1 if placeholder_length >= 2 else 0)]
            return get_query_with_alias(parent_query.format(stored_token.value, *placeholders).rstrip(';'), level), \
                stored_query
        query = get_query_with_alias(parent_query.format(current_query.rstrip(';'), stored_token.value), level)
    else:
        # Unary operation
        if is_alias_not_needed(operator_token, index, query_stack, upcoming_operator_and_index, stored_query):
            return stored_query.format(current_query), stored_query
        level = get_level(query_stack, level)
        query = get_query_with_alias(stored_query.format(current_query), level)
    return query, stored_query


def is_alias_not_needed(operator_token, index=None, query_stack=None, upcoming_operator_and_index=None,
                        stored_query=None, is_simple_mode = False):
    difference = 2 if stored_query else 1
    is_top_level = is_simple_mode or ( upcoming_operator_and_index and query_stack is not None and len(query_stack) - index == difference)
    return operator_token.type == TokenType.ANTI_JOIN or (is_top_level and operator_token.type in (
        TokenType.UNION,
        TokenType.INTERSECTION,
        TokenType.DIFFERENCE))


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
