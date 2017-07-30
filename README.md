# Python Recursive Descent Parser
A quick and dirty Recursive Descent Parser written using Python 3. The frontend abuses python's [data model](https://docs.python.org/3/reference/datamodel.html) to make grammar definitions partially legible. Syntax error messages will probably never be as good as table-based parsers, and has room for improvement. However, they are useful in their current state.

# Getting Started
To begin defining your grammar, create an instance of the `Grammar` class, and grab a copy of the grammar context and the grammar builder.
```py
from rd_parser import Grammar

grammar = Grammar()
c = grammar.context
b = grammar.builder
```
The grammar context helps organize named rules and forward definitions. The grammar builder helps define syntax rules using built-in python data types and operations.

Next, construct rules using the builder and context objects.
```py
# matches either "red", "blue", or "yellow"
c.color = b("red") | "blue" | "yellow"
# a regular expression to match a number
c.number = {"[0-9]*"}
# match a combination of rules and strings
c.message = "I have" + c.number + c.color + "hats"
```
Notice when defining the color rule, we needed to call the builder object with `"red"` as an argument. The native string type in python doesn't support the bitwise or operator. However, by wrapping the string with the builder object, we can now use python operators to construct rules.

Finally, lets try parsing a message with our grammar.
```py
my_message = "I have 3 blue hats"
# parse my_message
offset, node = grammar.parse(c.message, my_message)
# extract a value from the parse tree
assert(node.nodes[0].nodes[0].value == "3")
```
We pass in the rule we want to start parsing from, along with our message. The parse method returns a tuple with the offset where the parser stopped and the parse tree. Then we assert the string that was parsed as a number.

# Frontend - Data Model
The builder object is used to override the semantics of built-in types and operators, and use them to construct grammar rules. When constructing a rule, you must take care to use operators on builder objects and not on built-in types. For example, the following code is an error:
```py
c.my_rule = "terminal" + [c.other_rule]
```
Python will try to add the string and list and raise a TypeError. You must wrap one of the types in a builder object to enable overriding the addition operator, as follows:
```py
c.my_rule = b("terminal") + [c.other_rule]
```
Note that when assigning a rule to the grammar context, the value is automatically wrapped in a builder object for you.

A few python operators are overridden, like addition, subtraction, bitwise or, and slicing

 - **Addition** joins two rules, and only matches when the first rule is followed by the second.
 - **Subtraction** only matches the first rule if the second rule (the predicate) fails to match.
 - **Bitwise Or** matches either the first rule or the second rule.
 - **Slicing** repeats a rule (depending on the slice arguments).
```py
# addition operator example
c.joined_rules = c.foo + c.bar

# subtraction operator example
c.quoted_string = '"' + (ANY_CHAR - '"')[:] + '"'

# bitwise or operator example
c.sex = c.male | c.female

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
 - **List** with a single element means the element is optional (short cut for slicing).
 - **Set** with a single string is interpreted as a regular expression pattern.
 - **String** is interpreted as a terminal or literal, exact match.

It should be noted that sets and strings, when wrapped in a grammar builder object, are special matching rules called terminals. By default, terminals will ignore preceding whitespace before attempting to match. The frontend currently doesn't expose anyway to disable this behavior.

Also by default, string literals are not included in the parse tree. This behavior can be disabled, by multiplying a string literal with a builder object.
```py
# excluded from parse tree
c.exclude = "literal"
# included in parse tree
c.include = b*"literal"
```

Finally, the builder object has two useful properties
 - **`b.EOS`** matches the end of the stream.
 - **`rule.silent()`** returns a copy of `rule` that is excluded from the parse tree

# Backend - API
The rules can be imported from the `rd_parser.rules` model. A base class `Rule` is
