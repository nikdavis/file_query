from pyparsing import (
    Word,
    alphas,
    alphanums,
    QuotedString,
    delimitedList,
    Optional,
    Group,
    Suppress,
    ZeroOrMore,
    oneOf,
    Forward,
    Literal,
    OneOrMore,
    infixNotation,
    opAssoc,
    c_style_comment,
    nums,
    pyparsing_common,
    CaselessKeyword,
)

# Define keywords
SELECT = Suppress(CaselessKeyword("SELECT"))
FROM = Suppress(CaselessKeyword("FROM"))
WHERE = Suppress(CaselessKeyword("WHERE"))
AND = CaselessKeyword("AND")
OR = CaselessKeyword("OR")
NOT = CaselessKeyword("NOT")
LIKE = CaselessKeyword("LIKE")

# Define identifiers and literals
IDENTIFIER = Word(alphas + "_")
STRING_LITERAL = QuotedString("'", unquoteResults=True)
# Use pyparsing_common for numeric literals
NUMERIC_LITERAL = pyparsing_common.integer
DIRECTORY_LIST = Group(delimitedList(STRING_LITERAL))

# Define comparison operators
COMPARISON_OP = oneOf("= == != <> < <= > >=") | LIKE
ATTRIBUTE = IDENTIFIER + Suppress("=") + STRING_LITERAL

# Define basic condition with support for both string and numeric literals
VALUE = STRING_LITERAL | NUMERIC_LITERAL
basic_condition = Group(IDENTIFIER + COMPARISON_OP + VALUE)

# Define logical expressions using infixNotation for better handling of AND and OR
condition_expr = Forward()
condition_expr <<= infixNotation(
    basic_condition,
    [
        (NOT, 1, opAssoc.RIGHT),
        (AND, 2, opAssoc.LEFT),
        (OR, 2, opAssoc.LEFT),
    ],
)

# Define the full query structure
query = (
    SELECT
    + (Literal("*") | Group(OneOrMore(IDENTIFIER))).setResultsName("select")
    + FROM
    + DIRECTORY_LIST.setResultsName("from_dirs")
    + Optional(WHERE + condition_expr.setResultsName("where"))
)
