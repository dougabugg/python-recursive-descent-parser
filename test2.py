from rdparser.builder import grammar
import json

comment = grammar.builder("//") + {r"[^\n]*\n?"}
c, b = grammar(comment)

identifier = b({r"[a-zA-Z_][a-zA-Z_0-9]*"})

c.something = identifier + [":" + identifier] + ";"
c.test = "{" + c.something[:] + "}"


# from rdparser.rules import print_rule_tree
# print_rule_tree(c.test.rule)

def test(s):
    offset, node, error = c.test.parse_or_print(s)
    assert(error is None)
    if node is not None:
        print(json.dumps(node.__as_dict__(), indent = 2, sort_keys = True))

test("{}")
# test("{ // a:b \n }")
test("""{ // a:b
   }""")
test("{ c; }")

c.identifier = {r"[a-zA-Z0-9_]+"}
# two identifier rules would overwrite each other unless we override their names
c.field = c.identifier["name"] + ":" + c.identifier["type"] + ";"
# zero or more field rules must be renamed and end with "[]" to turn them into a list
c.struct = "struct" + c.identifier + "{" + c.field[:]["fields[]"] + "}"

offset, node = c.struct.parse("struct my_struct { foo:bar; name:string; }")
assert(node.identifier[0].value == "my_struct")
assert(node.fields[0].name[0].value == "foo" and node.fields[1].type[0].value == "string")


# still a named rule, 
c.my_regex = {r"[a-z]+"}
c.my_rule = [c.my_regex]

offset, node = c.my_regex.parse("test")
assert(len(node) == 1 and node[0].value == "test")
offset, node = c.my_rule.parse("")
assert(node.my_regex is None)