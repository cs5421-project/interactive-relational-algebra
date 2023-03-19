import enum


class TokenType(enum.Enum):
    SELECT = 0
    PROJECTION = 1
    UNION = 2
    DIFFERENCE = 3
    CARTESIAN = 4
    RENAME = 5
    NATURAL_JOIN = 6
    ANTI_JOIN = 7
    IDENT = 8
    EQUALS = 9
    AND = 10
    OR = 11
    NOT = 12
    OPEN_PARENTHESIS = 13
    CLOSED_PARENTHESIS = 14
    DIGIT = 15
    ARROW = 16
    INTERSECTION = 17
    LEFT_JOIN = 18
    RIGHT_JOIN = 19
    PRODUCT = 20
    DIVISION = 21
    EXPRESSION = 22
