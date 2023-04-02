from django.test import TestCase
from ira.service.raq_converter import raq_converter
import xml.etree.ElementTree as ET


class RAQConverterTestCase(TestCase):
    def setUp(self):
        pass

    def test_case_1(self):
        xml = """
            <ra_expression>
            <unary_operator>
                <operator>σ</operator>
                <attributes>a=10</attributes>
            </unary_operator>
            <parenthesis>
                <relation>R</relation>
            </parenthesis>
            </ra_expression>
        """
        expected = "σa=10(R)"
        self.assertEqual(raq_converter(xml), expected)

    def test_case_2(self):
        xml = """
            <ra_expression>
            <unary_operator>
                <operator>π</operator>
                <attributes>a,b</attributes>
            </unary_operator>
            <parenthesis>
                <relation>R</relation>
            </parenthesis>
            <binary_operator>
                <operator>∩</operator>
            </binary_operator>
            <unary_operator>
                <operator>σ</operator>
                <attributes>a&gt;10</attributes>
            </unary_operator>
            <parenthesis>
                <relation>R</relation>
            </parenthesis>
            </ra_expression>
        """
        expected = "πa,b(R) ∩ σa>10(R)"
        self.assertEqual(raq_converter(xml), expected)

    def test_case_3(self):
        xml = """
            <ra_expression>
            <relation>RTable</relation>
            <binary_operator>
                <operator>⋈</operator>
            </binary_operator>
            <relation>STable</relation>
            </ra_expression>
        """
        expected = "RTable ⋈ STable"
        self.assertEqual(raq_converter(xml), expected)

    def test_case_4(self):
        xml = """
            <ra_expression>
              <parenthesis>
                <relation>
                    A
                </relation>
                <binary_operator>
                    <operator>
                        ∪
                    </operator>
                </binary_operator>
                <relation>
                    B
                </relation>
              </parenthesis>
                <binary_operator>
                    <operator>
                        ∪
                    </operator>
                </binary_operator>
                <relation>
                    C
                </relation>
            </ra_expression>
            """
        expected = "(A ∪ B) ∪ C"
        self.assertEqual(raq_converter(xml), expected)

    def test_case_5(self):
        xml = """
            <ra_expression>
            <unary_operator>
                <operator>π</operator>
                <attributes>name,age</attributes>
            </unary_operator>
            <parenthesis>
                <relation>A</relation>
            </parenthesis>
            </ra_expression>
            """
        expected = "πname,age(A)"
        self.assertEqual(raq_converter(xml), expected)