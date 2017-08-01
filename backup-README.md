# Python Recursive Descent Parser
A quick and dirty Recursive Descent Parser written using Python 3. The frontend abuses python's [data model](https://docs.python.org/3/reference/datamodel.html) to make grammar definitions partially legible and easier to write. After a grammar is defined, it can be used to convert text into a parse tree.

# Getting Started
To begin defining your grammar, call the grammar function, and store the grammar context and grammar builder objects in separate variables.
```py
from rdparser import grammar

c, b = grammar()
```
The grammar context helps organize named rules and forward definitions. The grammar builder helps define syntax rules using built-in python data types and operations.

Next, construct rules using the builder and context objects.
```py
# match an email address
c.email = {r"[a-zA-Z0-9_.]+@[a-zA-Z0-9_.]+"}
# match a phone number
c.phone = {r"\d{3}-\d{3}-\d{4}"}
# match a combination of rules and strings
c.contact_info = "contact_info(" + (c.email | c.phone) + ")"
```
Define rules using built-in python types and operators, like sets, strings, add, and bitwise-or, and assign them as attributes on the context object.

Finally, lets test our grammar.
```py
test_input1 = "contact_info(800-555-1234)"
test_input2 = "contact_info(john.doe@example.com)"
# parse test_input1
end, node = c.contact_info.parse(test_input1)
assert(node.phone[0].value == "800-555-1234")
assert(node.email is None)
# parse test_input2
end, node = c.contact_info.parse(test_input2)
assert(node.email[0].value == "john.doe@example.com")
assert(node.phone is None)
```
Call the parse method on the rule object obtained from the context, and get a 2 tuple with the ending offset and the root node of the parse tree.

# Frontend - Data Model
The `grammar` function returns the grammar context and grammar builder objects. The context object lets you create named rules by assigning rule expressions to attributes, and create forward declarations simply by referencing an attribute and defining/assigning to it later. The `grammar` takes an optional `comment_rule` parameter, which allows you to supply a rule to be interleaved between all joined rules. The comment rule is automatically made zero or more and silenced (no node output), but this behavior can be override by using the `raw_comment_rule` parameter.

The builder object is used to override the semantics of built-in types and operators, and use them to construct grammar rules. When constructing a rule, you must take care to use operators on builder objects and not on built-in types. For example, the following code is an error:
```py
c.my_rule = "terminal" + [c.other_rule]
```

Python will try to add the string and list and raise a TypeError. You must wrap one of the types in a builder object to enable overriding the addition operator:
```py
# the builder object is callable, and wraps and returns its argument
c.my_rule = b("terminal") + [c.optional]
# the builder object is also the Empty rule, and can be prepended for the same effect
c.my_rule = b + "terminal" + [c.optional]
```

Note that when assigning a rule to the grammar context, the value is automatically wrapped in a builder object for you.

A few python operators are overridden, like addition, subtraction, bitwise or, and slicing

 * **Addition** joins two rules, and only matches when the first rule is followed by the second.
 * **Subtraction** only matches the first rule if the second rule (the predicate) fails to match.
 * **Bitwise Or** matches either the first rule or the second rule.
 * **Slicing** repeats a rule (depending on the slice arguments).
```py
# addition operator example
c.joined_rules = c.foo + c.bar + c.baz

# subtraction operator example
c.quoted_string = '"' + (ANY_CHAR - '"')[:] + '"'

# bitwise or operator example
c.pet = c.cat | c.dog | c.bird

# exactly N times
c.my_rule[n]
# zero or more
c.my_rule[:]
# optional (zero or one)
c.my_rule[:1]
# one or more
c.my_rule[1:]
# repeat N to M times
c.my_rule[n:m]
```

The syntax for three built-in types, list, set, and string, are also overridden

 * **List** with a single element means the element is optional (short cut for slicing).
 * **Set** with a single string is interpreted as a regular expression pattern.
 * **String** is interpreted as a terminal or literal, exact match.
```py
# avoid using built-in types improperly
# both of the following examples raise a TypeError
c.wont_work = ["a list with", "more than one element"]
c.wont_work = {c.should_be_a_string}
```

It should be noted that sets and strings, when wrapped in a grammar builder object, are special matching rules called terminals. By default, terminals will ignore preceding whitespace before attempting to match. This behavior can be disabled by and-ing a builder object with a set or string.
```py
# matches "foobar" and "foo bar"
c.example = b("foo") + "bar"
# matches only "foobar"
c.example = "foo" + b & "bar"
```
The end of stream rule also ignores whitespace default, and can be disabled similarly (`b & b.EOS`).

Also by default, string literals are not included in the parse tree. This behavior can be disabled by multiplying a builder object with a string literal.
```py
# excluded from parse tree
c.excluded = "literal"
# included in parse tree
c.included = b * "literal"
```

Finally, the builder object has a few useful properties and methods
 * **`b.EOS`** or **`b.EOF`** matches the end of the stream.
 * **`b.EOL`** matches all whitespace, including new lines, and is silent (doesn't generate token nodes). used when new lines are explicit.
 * **`rule.silent()`** returns a copy of `rule` that is excluded from the parse tree.
 * **`rule.parse(source, ...)`** parses the source input, raising a `ParseError` when parsing fails.
 * **`rule.parse_or_print(source, ...)`** same as `rule.parse` except it catches any parsing errors and pretty prints them.

All builder objects have a `parse` method, that takes a `source`, an `offset`, and an `explicit_new_lines` flag as arguments, which uses the rule and parses the source input, outputting a tuple with the ending offset and a special `NodeMask` object. The `NodeMask` wraps a raw `BaseNode`. Details on the `explicit_new_lines` flag and the `BaseNode` class are detailed below in the backend section.

A regex or string literal (with `b * "literal"`) rule will return a token node. Token nodes have an `offset` and `value` property. A named rule will return a named node, with `_offset`, `_end_offset`, and `_name` attributes. All the child rules of a parent rule will generate named nodes as children of the parent node when returned from `parse`. These child named nodes can be accessed by their name as attributes on the parent named node. If an attribute access is made but matches no child named node, `None` will be returned. For each regex or string literal rule in a named rule, a token node will be present. They can be accessed either by subscripting/indexing or iterating.

```py
# still a named rule, 
c.my_regex = {r"[a-z]+"}
c.my_rule = [c.my_regex]

offset, node = c.my_regex.parse("test")
# node is my_regex with a single token node, at index 0.
# access token node's value attribute and compare.
assert(len(node) == 1 and node[0].value == "test")
offset, node = c.my_rule.parse("")
# even though my_rule has a my_regex child rule,
# since its optional and doesn't match, my_regex is None.
assert(node.my_regex is None)
```

What happens if you use the same named rule in a rule twice, or a named rule repeats zero or more times? By design, any duplicate names will overwrite each other on the named node's attributes. To get around this, you can override the name of a rule when defining your grammar by passing a string into the subscript (`__getitem__`) operator on a builder object. The child node will be accessed by this name instead of its original name. If you end the name with "[]", the attribute access will result in a list of nodes.

```py
c.identifier = {r"[a-zA-Z0-9_]+"}
# two identifier rules would overwrite each other unless we override their names
c.field = c.identifier["name"] + ":" + c.identifier["type"] + ";"
# zero or more field rules must be renamed and end with "[]" to turn them into a list
c.struct = "struct" + c.identifier + "{" + c.field[:]["fields[]"] + "}"

offset, node = c.struct.parse("struct my_struct { foo:bar; name:string; }")
assert(node.identifier[0].value == "my_struct")
assert(node.fields[0].name[0].value = "foo" and node.fields[1].type[0].value = "string")
```

**TIP:** You can use the following snippet to view the tree of backend rule classes generated by the frontend
```py
# import the print_rule_tree utility function
from rdparser.rules import print_rule_tree
# make sure to "unwrap" the builder object by extracting the inner rule object
print_rule_tree(c.my_rule.rule)
```

# Backend - API
The rules can be imported from the `rdparser.rules` module. Every rule is a subclass of Rule and has a method named `match` that takes two arguments, a source string and an offset within the source, and returns a 3 item tuple with the new offset, a list of nodes, and an optional error. If a rule fails to match, an exception will be raised subclassed from RuleError, with 3 attributes: `offset`, `reason`, `offending_rule`. The error in the tuple returned from the `match` method is used by the `Join`, `Choice`, and `Repeat` rules to make error reporting more accurate.

In total, there are 10 rule classes
 * **`Rule`** a named rule supporting forward declaration.
 * **`Join`** matches a consecutive sequence of child rules.
 * **`Choice`** matches only one rule from a sequence.
 * **`Repeat`** matches a rule some amount of times.
 * **`Predicate`** only matches a rule if a predicate rule fails first.
 * **`Terminal`** matches a string literal.
 * **`Regex`** matches a regular expression pattern.
 * **`Empty`** matches nothing, doesn't generate nodes or advance the offset.
 * **`Silent`** "silences" or removes nodes returned by child rule.
 * **`EndOfStream`** matches the end of the stream (skipping whitespace).

`Terminal`, `Regex`, and `EndOfStream` have an `ignore_whitespace` flag (default true) if they should skip spaces and line breaks before trying to match. `Terminal` and `Regex` have an `ignore_token` flag which prevents a `Token` node from being generated. There is also a helper method called `Option` which is equivalent to `Repeat(rule, 0, 1)`.

The global method `use_explicit_new_lines` is used to change the behavior of the `ignore_whitespace` flag, and operates on a global flag variable. Calling it with no parameters (or `None`) returns the current value, and passing `True` or `False` modifies it. By default, the flag is set to `False`, and when ignoring whitespace, the new line character will also be ignored. With `True`, you must specify new lines explicitly in your rules, they will not be ignored like other whitespace. On the frontend's parse method, the `explicit_new_lines` flag is implemented using `use_explicit_new_lines` to temporarily change the global flag while it's matching.

The nodes returned by `match` are the raw, unmasked `BaseNode` objects. A node is either a `Node` or a `Token`. A `Node` has an `offset`, a `name`, an `opts`, and a list of child `nodes`. A `Token` has an `offset` and a `value` which is the matched text from the source. `Token` is only generated by the `Terminal` and `Regex` rules, and `Node` is only generated by `Rule`.
