import math
from .nodes import BaseNode, Node, Token
from .rules import *

# DEPRECATED don't use this, this is dumb

SINGLE_RULES = (Rule, Repeat, Silent)
MULTI_RULES = (Join, Choice)
TERMINALS = (Terminal, Regex, Empty, EndOfStream)

def iter_rule(rule):
    if isinstance(rule, SINGLE_RULES):
        yield rule.rule
    elif isinstance(rule, MULTI_RULES):
        yield from rule.rules
    elif isinstance(rule, TERMINALS):
        yield from ()
    elif isinstance(rule, Predicate):
        yield from (rule.rule, rule.predicate)
    raise TypeError


class GrammarTemplate:
    def __init__(self):
        self.rules = {}
    
    def process(self, rule, stack=None):
        if stack is None:
            stack = ()
        if rule in stack:
            return
        stack += (rule,)
        if isinstance(rule, Rule):
            self.add_rule(rule)
        for _rule in iter_rule(rule):
            self.process(_rule, stack)

    def add_rule(self, rule):
        rules = self.rules
        name = rule.name
        if name in rules:
            return
        # prevent infinite recursion
        rules[name] = None
        rules[name] = Template(self, rule)

class Template:
    def __init__(self, grammar, rule):
        self.grammar = grammar
        self.rule = rule
        self.slots = {}
        self.values = 0
        for _rule in iter_rule(rule):
            self.process(_rule)
    
    def process(self, rule, stack=None, is_infinite=False):
        if stack is None:
            stack = ()
        if rule in stack:
            return
        stack += (rule,)
        if isinstance(rule, Rule):
            self.grammar.add_rule(rule)
            self.add_name(rule.name, is_infinite)
            return
        if isinstance(rule, (Terminal, Regex)) and not rule.ignore_token:
            self.add_value(is_infinite)
        if isinstance(rule, Repeat) and rule._max is None:
            is_infinite = True
        for _rule in iter_rule(rule):
            self.process(_rule, stack, is_infinite)

    def add_name(self, name, is_infinite):
        if name in self.slots:
            return
        self.slots[name] = is_infinite
    
    def add_value(self, is_infinite):
        if is_infinite:
            self.values = math.inf
        self.values += 1

class NodeInspector:
    def __init__(self, target, grammar):
        if not isinstance(target, Node):
            raise TypeError
        self.target = target
        self.grammar = grammar
        self.template = grammar.rules[target.name]
        self.slots = self.template.slots
        self.names = {}
        for slot in self.slots.keys():
            self.names[slot] = []
        self.values = []
        for node in target.nodes:
            if isinstance(node, Node):
                self.names[node.name] += [node]
            else:
                self.values.append(node)
        if self.template.values == 1:
            self.values = self.values[0]
        if len(self.template.slots) == 0:
            self.mask = self.values
        else:
            self.mask = NodeMask(self)

class NodeMask:
    def __init__(self, inspector):
        super().__setattr__("_inspector", inspector)
    
    def __len__(self):
        return self._inspector.target.offset

    def __getattr__(self, name):
        names = self._inspector.names
        nodes = [NodeInspector(node, self._inspector.grammar).mask for node in names[name]]
        if len(nodes) == 1 and not self._inspector.slots[name]:
            return nodes[0]
        return nodes

    def __setattr__(self, name, value):
        raise AttributeError
    
    def __getitem__(self, i):
        return self._inspector.values[i]

    def __iter__(self):
        return iter(self._inspector.values)