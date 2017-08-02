import re
from .rules import *
from .nodes import NodeInspector


class Grammar:
    def __init__(self, comment_rule=None, raw_comment_rule=None):
        self.rules = {}
        if comment_rule is not None:
            comment_rule = Grammar.builder(comment_rule).silent()[:]
        self.comment_rule = comment_rule or raw_comment_rule
        self.context = GrammarContext(self)
        self.builder = RuleBuilder(None, self.comment_rule)

    # placeholder for RuleBuilder
    builder = None

def grammar(comment_rule=None, raw_comment_rule=None):
    grammar = Grammar(comment_rule, raw_comment_rule)
    return grammar.context, grammar.builder

# placeholder for RuleBuilder
grammar.builder = None

class GrammarContext:
    def __init__(self, grammar):
        super().__setattr__("_grammar", grammar)
    
    def __getattr__(self, name, raw=False):
        g = self._grammar
        rules = g.rules
        if name not in rules:
            rule = Rule(name)
            rules[name] = rule
        if raw or g.comment_rule is None:
            return g.builder(rules[name])
        else:
            return g.builder(Join((g.comment_rule.rule, rules[name], g.comment_rule.rule)))

    def __setattr__(self, name, value):
        rule = self.__getattr__(name, True).rule
        rule.assign_rule(RuleBuilder.unwrap(value))


class RuleBuilder:
    def __init__(self, rule=None, comment_rule=None):
        self.rule = self.unwrap(rule)
        self.comment_rule = self.unwrap(comment_rule)

    @property
    def EOS(self):
        return self._wrap(EndOfStream())
    EOF = EOS

    @property
    def EOL(self):
        return self._wrap(self.unwrap({r"\s*"})).silent()

    def silent(self):
        return self._wrap(Silent(self.rule))

    def parse(self, source, offset=0, explicit_new_lines=None):
        rule = self.rule
        old_flag_value = use_explicit_new_lines()
        use_explicit_new_lines(explicit_new_lines)
        try:
            nodes = []
            offset, error = rule.match(source, offset, nodes)
            return offset, NodeInspector(nodes[0]).mask
        except RuleError as e:
            raise ParseError(e, source, NodeInspector(nodes[0]).mask) from e
        finally:
            use_explicit_new_lines(old_flag_value)

    def parse_or_print(self, source, offset=0, explicit_new_lines=None):
        try:
            return self.parse(source, offset, explicit_new_lines)
        except ParseError as e:
            e.print()
            return e.rule_error.offset, e

    @staticmethod
    def unwrap(target):
        if target is None:
            return Empty()
        elif isinstance(target, BaseRule):
            return target
        elif isinstance(target, RuleBuilder):
            return target.rule
        elif isinstance(target, str):
            rule = Terminal(target)
            rule.ignore_token = True
            return rule
        elif isinstance(target, list) and len(target) == 1:
            return Option(RuleBuilder.unwrap(target[0]))
        elif isinstance(target, set):
            expression = target.pop()
            if isinstance(expression, str):
                return Regex(re.compile(expression))
        raise TypeError("failed to unwrap unsupported data type " + target.__class__)

    def _wrap(self, rule):
        return RuleBuilder(rule, self.comment_rule)

    def __add__(self, other):
        other = self.unwrap(other)
        if self.comment_rule is None:
            return self._wrap(Join((self.rule, other)))
        else:
            return self._wrap(Join((self.rule, self.comment_rule, other)))

    def __radd__(self, other):
        other = self.unwrap(other)
        if self.comment_rule is None:
            return self._wrap(Join((other, self.rule)))
        else:
            return self._wrap(Join((other, self.comment_rule, self.rule)))
    
    def __or__(self, other):
        other = self.unwrap(other)
        return self._wrap(Choice((self.rule, other)))

    def __ror__(self, other):
        other = self.unwrap(other)
        return self._wrap(Choice((other, self.rule)))
    
    def __getitem__(self, other):
        if isinstance(other, str):
            if other.endswith("[]"):
                return self._wrap(Rule(other[:-2], self.rule, flatten=True, as_list=True))
            else:
                return self._wrap(Rule(other, self.rule, flatten=True))
        elif isinstance(other, slice):
            return self._wrap(Repeat(self.rule, other.start, other.stop))
        elif isinstance(other, int):
            return self._wrap(Repeat(self.rule, other, other))
        elif isinstance(other, tuple) and len(other) == 2:
            return self._wrap(Repeat(self.rule, other[0], other[1]))
        raise TypeError("operation only valid with str, slice, int or tuple, not " + other.__class__)

    __iter__ = None

    def __sub__(self, other):
        other = self.unwrap(other)
        return self._wrap(Predicate(self.rule, other))

    def __mul__(self, other):
        if isinstance(other, str):
            return self._wrap(Terminal(other))
        raise TypeError("operation only valid on Terminal, not " + other.__class__)

    def __and__(self, other):
        if isinstance(other, (EndOfStream, str, set)):
            other = self.unwrap(other)
            other.rule.ignore_whitespace = False
            return other
        raise TypeError("operation only valid on EndOfStream, Regex, or Terminal, not " + other.__class__)

    def __call__(self, rule):
        # return RuleBuilder(self.unwrap(rule), self.comment_rule)
        return self._wrap(self.unwrap(rule))
    
Grammar.builder = RuleBuilder()
grammar.builder = RuleBuilder()


class ParseError(Exception):
    def __init__(self, rule_error, source, node):
        self.rule_error = rule_error
        self.source = source
        self.node = node

    def __str__(self):
        rule = self.rule_error
        return "at {}: {}".format(rule.offset, rule.reason)

    def _print_source_error(self):
        offset = self.rule_error.offset
        count = 0
        for line in self.source.splitlines():
            start = count
            count += len(line) + 1
            if count > offset:
                print(line)
                print(" " * (offset - start) + "^")
                break

    def print(self):
        print(self.__class__.__name__ + " " + str(self))
        self._print_source_error()
        error = self.rule_error
        error_name = error.__class__.__name__
        message = error.reason
        if isinstance(error, TerminalError):
            term = error.offending_rule.terminal
            message = "expected `{}`".format(term)
        elif isinstance(error, RegexError):
            pattern = error.offending_rule.expression.pattern
            message = "regex failed to match `{}`".format(pattern)
        elif isinstance(error, PredicateError):
            message = "predicate matched " + error.offending_rule.predicate
        print("{}: {}".format(error_name, message))
