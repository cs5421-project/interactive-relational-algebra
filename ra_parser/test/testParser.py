import sys
sys.path.append('..')
# setting path

from Lexer import Lexer, display_tokens, Token, TokenType
from Parser import Parser


def main():
    lexer: Lexer = Lexer()
    # Test 1
    input = "σ(not(a=10) and b = 20)(R)"
    tokens = lexer.tokenize(input)

    parser: Parser = Parser()

    expected = "R σ[( not (a=10) and b=20)]"
    parsed_postfix_form = parser.parse(tokens)
    print(parsed_postfix_form)
    print("SUCCESS" if expected == parsed_postfix_form else "FAIL")

    # Test 2
    input = "A ∪ B ∪ σ id=3 and id >= 2 (C)"
    tokens = lexer.tokenize(input)

    parser: Parser = Parser()

    expected = "A B ∪ C σ[id=3 and id>=2] ∪"
    parsed_postfix_form = parser.parse(tokens)
    print(parsed_postfix_form)
    print("SUCCESS" if expected == parsed_postfix_form else "FAIL")

    # Test 3
    input = "RTable ⋈ STable"
    tokens = lexer.tokenize(input)

    parser: Parser = Parser()

    expected = "RTable STable ⋈"

    parsed_postfix_form = parser.parse(tokens)
    print(parsed_postfix_form)
    print("SUCCESS" if expected == parsed_postfix_form else "FAIL")

    # Test 4
    input = "π name,age (A)"
    tokens = lexer.tokenize(input)

    parser: Parser = Parser()

    expected = "A π[name,age]"
    parsed_postfix_form = parser.parse(tokens)
    print(parsed_postfix_form)
    print("SUCCESS" if expected == parsed_postfix_form else "FAIL")

    # Test 5
    input = "Car * σ name=\"Lukas\" (Owner)"
    tokens = lexer.tokenize(input)

    parser: Parser = Parser()

    parsed_postfix_form = parser.parse(tokens)
    print(parsed_postfix_form)
    expected = "Car Owner σ[name=\"Lukas\"] *"
    print("SUCCESS" if expected == parsed_postfix_form else "FAIL")


if __name__ == "__main__":
    main()
