from rdparser import Grammar

grammar = Grammar()
c = grammar.context
b = grammar.builder

# match an email address
c.email = {r"[a-zA-Z0-9_.]+@[a-zA-Z0-9_.]+"}
# match a phone number
c.phone = {r"\d{3}-\d{3}-\d{4}"}
# match a combination of rules and strings
c.contact_info = "contact_info(" + (c.email | c.phone) + ")"

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
