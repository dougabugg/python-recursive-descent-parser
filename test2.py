from rd_parser import Grammar, ParseError
import json

comment = Grammar.builder("//") + {r"[^\n]*"}
grammar = Grammar(comment)
c = grammar.context
b = grammar.builder

identifier = b({r"[a-zA-Z_][a-zA-Z_0-9]*"})

c.something = identifier + [":" + identifier] + ";"
c.test = "{" + c.something[:] + "}"

def test(s):
    offset, node = c.test.parse_or_print(s)
    print(json.dumps(node.__as_dict__(), indent = 2, sort_keys = True))

test("{ // a:b \n }")
test("{}")
test("{ c; }")