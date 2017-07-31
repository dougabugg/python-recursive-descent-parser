# Python Recursive Descent Parser
A quick and dirty Recursive Descent Parser written using Python 3. The frontend abuses python's [data model](https://docs.python.org/3/reference/datamodel.html) to make grammar definitions partially legible and easier to write. After a grammar is defined, it can be used to convert text into a parse tree.

# Getting Started
To begin defining your grammar, call the grammar function, and store the grammar context and grammar builder objects in separate variables.
```py
from rd_parser.builder import grammar

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
assert(node.phone[0].values == "800-555-1234")
assert(node.email is None)
# parse test_input2
end, node = c.contact_info.parse(test_input2)
assert(node.email[0].values == "john.doe@example.com")
assert(node.phone is None)
```
Call the parse method on the rule object obtained from the context, and get a 2 tuple with the offset where parsing ended and the root node of the parse tree.

# Frontend - Data Model
The builder object is used to override the semantics of built-in types and operators, and use them to construct grammar rules. When constructing a rule, you must take care to use operators on builder objects and not on built-in types. For example, the following code is an error:
```py
c.my_rule = "terminal" + [c.other_rule]
```

Python will try to add the string and list and raise a TypeError. You must wrap one of the types in a builder object to enable overriding the addition operator, as follows:
```py
# the builder object is callable, and wraps and returns its argument
c.my_rule = b("terminal") + [c.optional]
# the builder object is also the Empty rule, and can be prepended
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
c.joined_rules = c.foo + c.bar

# subtraction operator example
c.quoted_string = '"' + (ANY_CHAR - '"')[:] + '"'

# bitwise or operator example
c.sex = c.male | c.female

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

The syntax for three built-in types, list, set, and string are also overridden
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
c.example = "foo" + "bar"
# matches only "foobar"
c.example = "foo" + b & "bar"
```
The end of stream rule also ignores whitespace default, and can be disabled similarly (`b & b.EOS`).

Also by default, string literals are not included in the parse tree. This behavior can be disabled, by multiplying a builder object with a string literal.
```py
# excluded from parse tree
c.excluded = "literal"
# included in parse tree
c.included = b * "literal"
```

Finally, the builder object has two useful properties and methods
 * **`b.EOS`** or **`b.EOF`** matches the end of the stream.
 * **`rule.silent()`** returns a copy of `rule` that is excluded from the parse tree

TODO: document `parse` method here

# Backend - API
The rules can be imported from the `rd_parser.rules` module. Every rule is a subclass of Rule and has a method named `match` that takes two arguments, a source string or stream and an offset within the source, and returns a 3 item tuple with the new offset, a list of nodes, and an error. If a rule fails to match, an exception will be raised subclassed from RuleError, with 3 attributes: `offset`, `reason`, `offending_rule`. The error in the tuple returned from the `match` method is used by the `Choice` rule to make error reporting more accurate.

In total, there are 10 rule classes
 * **`Rule`** a named rule supporting forward declaration.
 * **`Join`** matches a consecutive sequence of child rules.
 * **`Choice`** matches only one rule from a set.
 * **`Repeat`** matches a rule a variable amount of times.
 * **`Predicate`** matches a rule only if a predicate rule fails first.
 * **`Terminal`** matches a string literal.
 * **`Regex`** matches a regular expression pattern.
 * **`Empty`** matches nothing.
 * **`Silent`** removes nodes returned by child rule
 * **`EndOfStream`** matches the end of the stream (skipping whitespace).

`Terminal`, `Regex`, and `EndOfStream` have an `ignore_whitespace` flag (default true) if they should skip spaces and line breaks before trying to match. `Terminal` and `Regex` have an `ignore_token` flag which prevents a `Token` node from being generated. There is also a helper method called `Option` which is equivalent to `Repeat(rule, 0, 1)`.

The method `use_explicit_new_lines` is used to change the behavior of the `ignore_whitespace` flag, and operates on a global flag variable. Calling it with no parameters (or `None`) returns the current value, and passing `True` or `False` modifies it. By default, the flag is set to `False`, and when ignoring whitespace, the new line character will also be ignored. With `True`, you must specify new lines explicitly in your rules, they will not be ignored like other whitespace.

The nodes returned by `match` are the raw, unmasked `BaseNode` objects. A node is either a `Node` or a `Token`. A `Node` has an `offset`, a `name`, and a list of child `nodes`. A `Token` has an `offset` and a `value` which is the matched text from the source. `Token` is only generated by the `Terminal` and `Regex` rules, and `Node` is only generated by `Rule`.
