from django.test import TestCase

from ira.service.lexer import Token, TokenType
from ira.service.transformer import transform


class TransformerTestCase(TestCase):
    SALES_IDENTITY_TOKEN = Token('sales', TokenType.IDENT, None)
    PRODUCTS_IDENTITY_TOKEN = Token('products', TokenType.IDENT, None)
    IRIS_IDENTITY_TOKEN = Token('iris', TokenType.IDENT, None)

    MOCK_UNION_TOKEN = Token('∪', TokenType.UNION, None)
    MOCK_NATURAL_JOIN_TOKEN = Token('⋈', TokenType.NATURAL_JOIN, None)
    MOCK_INTERSECTION_TOKEN = Token('∩', TokenType.INTERSECTION, None)
    MOCK_CARTESIAN_TOKEN = Token('⨯', TokenType.CARTESIAN, None)
    MOCK_DIFFERENCE_TOKEN = Token('-', TokenType.DIFFERENCE, None)
    MOCK_PROJECTION_TOKEN = Token('π', TokenType.PROJECTION, None)
    MOCK_SELECTION_TOKEN = Token('σ', TokenType.SELECT, None)

    def test_singular_table(self):
        # RA query: (sales)
        actual_input = [self.SALES_IDENTITY_TOKEN]
        expected_output = "select * from sales;"
        actual_output = transform(actual_input)
        self.assertEqual(actual_output.value, expected_output)

    def test_simple_intersection(self):
        # RA query: (σ ProductID > 2 (sales)) ∩ (sales)
        inner_selection_join_attributes = [Token("ProductID", TokenType.IDENT), Token(
            ">", TokenType.DIGIT), Token("2", TokenType.DIGIT)]
        inner_selection_join_token = Token('σ', TokenType.SELECT, inner_selection_join_attributes)
        actual_input = [self.SALES_IDENTITY_TOKEN, inner_selection_join_token, self.SALES_IDENTITY_TOKEN,
                        self.MOCK_INTERSECTION_TOKEN]
        expected_output = "select * from sales where \"ProductID\">2 intersect select * from sales;"
        actual_output = transform(actual_input)
        self.assertEqual(actual_output.value, expected_output)

    def test_simple_difference(self):
        # RA query: (sales) - (sales)
        actual_input = [self.SALES_IDENTITY_TOKEN, self.SALES_IDENTITY_TOKEN, self.MOCK_DIFFERENCE_TOKEN]
        expected_output = "select * from sales except select * from sales;"
        actual_output = transform(actual_input)
        self.assertEqual(actual_output.value, expected_output)

    def test_simple_union(self):
        # RA query: (sales) ∪ (sales)
        actual_input = [self.SALES_IDENTITY_TOKEN, self.SALES_IDENTITY_TOKEN, self.MOCK_UNION_TOKEN]
        expected_output = "select * from sales union select * from sales;"
        actual_output = transform(actual_input)
        self.assertEqual(actual_output.value, expected_output)


    def test_complex_natural_join(self):
        # RA query: π variety (σ petal.width>0.1(π variety,petal.width (iris)))  ⋈ (iris)
        inner_projection_attributes =  [Token("variety", TokenType.IDENT),Token(",", TokenType.IDENT),
                                        Token("petal.width", TokenType.IDENT)]
        inner_projection_token = Token('π',TokenType.PROJECTION,inner_projection_attributes)
        selection_attributes = [Token("petal.width", TokenType.IDENT), Token(
            ">", TokenType.DIGIT), Token("0.1", TokenType.DIGIT)]
        selection_token = Token('σ',TokenType.SELECT,selection_attributes)
        projection_token_attributes = [Token("variety",TokenType.IDENT)]
        projection_token = Token('π',TokenType.PROJECTION,projection_token_attributes)
        actual_input = [self.IRIS_IDENTITY_TOKEN,inner_projection_token, selection_token,
                        projection_token,self.IRIS_IDENTITY_TOKEN,self.MOCK_NATURAL_JOIN_TOKEN]
        expected_output = 'select * from (select distinct "variety" from (select * from (select distinct "variety",' \
                          '"petal.width" from iris) as q0 where "petal.width">0.1) as q1) as q2 natural join iris;'
        actual_output = transform(actual_input)
        self.assertEqual(actual_output.value, expected_output)


