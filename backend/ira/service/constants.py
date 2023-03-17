import enum

PRODUCT = '*'
DIFFERENCE = '-'
UNION = '∪'
INTERSECTION = '∩'
DIVISION = '÷'
NATURAL_JOIN = '⋈'
JOIN_LEFT = '⧑'
JOIN_RIGHT = '⧒'
JOIN_FULL = '⧓'
PROJECT = 'π'
SELECT = 'σ'
RENAME = 'ρ'
ARROW = '➡'


AND = "and"
OR = "or"
NOT = "not"

logical_operators = [AND, OR, NOT]

class TokenType(enum.Enum):
    SELECT = 0
    PROJECT = 1
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
    JOIN_LEFT = 18
    JOIN_RIGHT = 19
    PRODUCT = 20
    DIVISION = 21
    EXPRESSION = 22