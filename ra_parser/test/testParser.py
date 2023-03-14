
# setting path
import sys
sys.path.append('..')
from Lexer import Lexer, display_tokens, Token, TokenType
from Parser import Parser


def main():
    lexer: Lexer = Lexer()
    # Test 1
    input = "σ(not(a=10) and b = 20)(R)"
    tokens = lexer.convert_based_on_priority(lexer.tokenize(input))

    parser: Parser = Parser()

    parsed_tree = parser.parse(tokens)
    print(parsed_tree.print_tree())

    # Test 2
    input = "A ∪ B ∪ σ id=3 and id >= 2 (C)"
    tokens = lexer.convert_based_on_priority(lexer.tokenize(input))

    parser: Parser = Parser()

    parsed_tree = parser.parse(tokens)
    print(parsed_tree.print_tree())

    # Test 3
    input = "RTable ⋈ STable"
    tokens = lexer.convert_based_on_priority(lexer.tokenize(input))

    parser: Parser = Parser()

    parsed_tree = parser.parse(tokens)
    print(parsed_tree.print_tree())

    # Test 4
    input = "π name,age (A)"
    tokens = lexer.convert_based_on_priority(lexer.tokenize(input))

    parser: Parser = Parser()

    parsed_tree = parser.parse(tokens)
    print(parsed_tree.print_tree())


if __name__ == "__main__":
    main()
