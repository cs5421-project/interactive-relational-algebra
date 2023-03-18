
# setting path
import sys
sys.path.append('..')
from Lexer import Lexer, Token, TokenType



def main():
    lexer: Lexer = Lexer()
    # Test 1
    input = "σa=10(R)"
    tokens = lexer.tokenize(input)
    expected = [Token("σ", TokenType.SELECT), Token("[a=10]", TokenType.EXPRESSION), Token(
        "(", TokenType.OPEN_PARENTHESIS), Token("R", TokenType.IDENT), Token(")", TokenType.CLOSED_PARENTHESIS)]
    print("TEST 1: " + input + " ", end="")
    if (tokens == expected):
        print("SUCCESS")
    else:
        print("FAILED")

    # Test 2
    input = "σa1=10(R22)"
    tokens = lexer.tokenize(input)
    expected = [Token("σ", TokenType.SELECT), Token("[a1=10]", TokenType.EXPRESSION), Token(
        "(", TokenType.OPEN_PARENTHESIS), Token("R22", TokenType.IDENT), Token(")", TokenType.CLOSED_PARENTHESIS)]
    print("TEST 2: " + input + " ", end="")
    if (tokens == expected):
        print("SUCCESS")
    else:
        print("FAILED")

    # Test 3
    input = "RTable ⋈ STable"
    tokens = lexer.tokenize(input)
    expected = [Token("RTable", TokenType.IDENT), Token(
        "⋈", TokenType.NATURAL_JOIN), Token("STable", TokenType.IDENT)]
    print("TEST 3: " + input + " ", end="")
    if (tokens == expected):
        print("SUCCESS")
    else:
        print("FAILED")


if __name__ == "__main__":
    main()
