from pyparsing import (
    Word,
    alphas,
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
    c_style_comment,
)

# Define keywords
SELECT = Suppress(Word("SELECT"))
FROM = Suppress(Word("FROM"))
WHERE = Suppress(Word("WHERE"))
AND = Literal("AND")
OR = Literal("OR")
NOT = Literal("NOT")

# Define identifiers and literals
IDENTIFIER = Word(alphas + "_")
STRING_LITERAL = QuotedString("'", unquoteResults=True)
DIRECTORY_LIST = Group(delimitedList(STRING_LITERAL))

# Define comparison operators
COMPARISON_OP = oneOf("== != < <= > >=")
ATTRIBUTE = IDENTIFIER + Suppress("=") + STRING_LITERAL

# Define conditions
condition_expr = Forward()
condition = (
    Group(
        IDENTIFIER
        + COMPARISON_OP
        + STRING_LITERAL
    )
    | Group(NOT + condition_expr)
    | Group(
        condition_expr
        + (AND | OR)
        + condition_expr
    )
)
condition_expr <<= condition

# Define the full query structure
query = (
    SELECT
    + (Literal("*") | Group(OneOrMore(IDENTIFIER))).setResultsName("select")
    + FROM
    + DIRECTORY_LIST.setResultsName("from_dirs")
    + Optional(WHERE + condition_expr.setResultsName("where"))
)
