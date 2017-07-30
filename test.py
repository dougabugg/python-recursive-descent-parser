from rd_parser.builder import grammar

b = grammar.builder
comments = (b("//") + {r"[^\n]*"}) | \
    ("/*" + ({r"[^*]*"} + b(b + "*" - "*/"))[:] + "*/")
c, b = grammar(comments)

def delimited_list(item, separator=","):
    item = b(item)
    separator = b(separator)
    return item + (separator + item)[:]

identifier = b({r"[a-zA-Z_][a-zA-Z_0-9]*"})
end_of_line = (b(";") | ",")[:1]

c.tuple_type = b("(") + [delimited_list(c.type_identifier)] + ")"
c.type_name_identifier = identifier + ["<" + delimited_list(c.type_identifier) + ">"]
c.type_identifier = c.tuple_type | c.type_name_identifier

c.type_name_definition = identifier + ["<" + delimited_list(identifier) + ">"]

c.struct_field = identifier + ":" + c.type_identifier + end_of_line
c.struct_definition = "struct" + c.type_name_definition + "{" + c.struct_field[:] + "}"

c.enum_field = identifier + [c.tuple_type] + end_of_line
c.enum_definition = "enum" + c.type_name_definition + "{" + c.enum_field[:] + "}"

c.type_definition = c.struct_definition | c.enum_definition

c.module_body = c.type_definition[:] + b.EOF



s = """
// comment
enum Option<T> {
    Ok(T);
    // comment
    None;
}
struct my_struct/* test / * */<A, B> {
    fieldA: Option<string>;
    // comment
    fieldB: (A, B)
    fieldC: Option<Pointer<Array<(A, B)>>>
    // comment
}
// comment
"""

def test(s):
    offset, node = c.module_body.parse_or_print(s)
    import json
    print(json.dumps(node.__as_dict__(), indent = 2, sort_keys = True))
test(s)