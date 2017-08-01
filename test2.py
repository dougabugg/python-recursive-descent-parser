from rd_parser.builder import grammar
import json

comment = grammar.builder("//") + {r"[^\n]*\n?"}
c, b = grammar(comment)

identifier = b({r"[a-zA-Z_][a-zA-Z_0-9]*"})

c.something = identifier + [":" + identifier] + ";"
c.test = "{" + c.something[:] + "}"

def test(s):
    offset, node = c.test.parse_or_print(s)
    if node is not None:
        print(json.dumps(node.__as_dict__(), indent = 2, sort_keys = True))

test("{}")
# test("{ // a:b \n }")
test("""{ // a:b
   }""")
test("{ c; }")