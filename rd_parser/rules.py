import re
from .nodes import Node, Token

__all__ = ('BaseRule', 'Rule', 'Join', 'Choice', 'Repeat', 'Option', 'Predicate', 'Terminal',
    'Regex', 'Empty', 'Silent', 'EndOfStream', 'RuleError', 'TerminalError',
    'RegexError', 'PredicateError', 'EndOfStreamError', 'use_explicit_new_lines')

class BaseRule:
    pass

class Rule(BaseRule):
    def __init__(self, name="", rule=None):
        self.name = name
        self.rule = rule

    def match(self, source, offset):
        if self.rule is None:
            raise RuntimeError("rule `{}` is None or assign_rule never called".format(self.name))
        node = Node(offset, self.name)
        offset, node.nodes, error = self.rule.match(source, offset)
        node.end_offset = offset
        return offset, [node], error

    def assign_rule(self, rule):
        self.rule = rule

class Join(BaseRule):
    def __init__(self, rules):
        self.rules = rules

    def match(self, source, offset):
        nodes = []
        furthest = None
        failed = False
        for rule in self.rules:
            try:
                offset, new_nodes, error = rule.match(source, offset)
                if error is not None and (furthest is None or error.offset >= furthest.offset):
                    furthest = error
                nodes.extend(new_nodes)
            except RuleError as error:
                if furthest is None or error.offset >= furthest.offset:
                    raise
                else:
                    raise furthest
        return offset, nodes, furthest

class Choice(BaseRule):
    def __init__(self, rules):
        self.rules = rules
    
    def match(self, source, offset):
        nodes = None
        furthest = None
        for rule in self.rules:
            try:
                offset, nodes, error = rule.match(source, offset)
                if error is not None and (furthest is None or error.offset >= furthest.offset):
                    furthest = error
                break
            except RuleError as e:
                if furthest is None or e.offset >= furthest.offset:
                    furthest = e
        if nodes is None:
            raise furthest
        return offset, nodes, furthest

class Repeat(BaseRule):
    def __init__(self, rule, _min=None, _max=None):
        self.rule = rule
        self._min = _min
        self._max = _max
    
    def match(self, source, offset):
        nodes = []
        last_error = None
        count = 0
        _max = self._max
        while _max is None or count < _max:
            try:
                offset, new_nodes, last_error = self.rule.match(source, offset)
                nodes.extend(new_nodes)
                count += 1
            except RuleError as e:
                if self._min is not None and count < self._min:
                    raise
                else:
                    last_error = e
                    break
        return offset, nodes, last_error

class Predicate(BaseRule):
    def __init__(self, rule, predicate):
        self.rule = rule
        self.predicate = predicate
    
    def match(self, source, offset):
        try:
            new_offset, nodes, error = self.predicate.match(source, offset)
        except RuleError as e:
            return self.rule.match(source, offset)
        else:
            raise PredicateError(offset, "predicate matched", self.predicate)

class Terminal(BaseRule):
    def __init__(self, terminal, ignore_token=False, ignore_whitespace=True):
        self.terminal = terminal
        self.ignore_token = ignore_token
        self.ignore_whitespace = ignore_whitespace
    
    def match(self, source, offset):
        _offset = offset
        if self.ignore_whitespace:
            offset = _skip_whitespace(source, offset)
        if source.startswith(self.terminal, offset):
            offset += len(self.terminal)
            node = Token(offset, self.terminal)
            if self.ignore_token:
                return offset, [], None
            return offset, [node], None
        else:
            raise TerminalError(_offset, "terminal failed to match", self)

class Regex(BaseRule):
    def __init__(self, expression, ignore_token=False, ignore_whitespace=True):
        self.expression = expression
        self.ignore_token = ignore_token
        self.ignore_whitespace = ignore_whitespace
    
    def match(self, source, offset):
        _offset = offset
        if self.ignore_whitespace:
            offset = _skip_whitespace(source, offset)
        result = self.expression.match(source, offset)
        if not result:
            raise RegexError(_offset, "regex failed to match", self)
        match = result[0]
        offset += len(match)
        if self.ignore_token:
            return offset, [], None
        return offset, [Token(offset, match)], None

class Empty(BaseRule):
    def match(self, source, offset):
        return offset, [], None

class Silent(BaseRule):
    def __init__(self, rule):
        self.rule = rule
    
    def match(self, source, offset):
        offset, nodes, error = self.rule.match(source, offset)
        return offset, [], None

class EndOfStream(BaseRule):
    def __init__(self, ignore_whitespace=True):
        self.ignore_whitespace = ignore_whitespace
    def match(self, source, offset):
        _offset = offset
        if self.ignore_whitespace:
            offset = _skip_whitespace(source, offset)
        if offset < len(source):
            raise EndOfStreamError(offset, "expected end of stream", self)
        return offset, [], None

# matching rule errors
class RuleError(Exception):
    def __init__(self, offset, reason, offending_rule):
        self.offset = offset
        self.reason = reason
        self.offending_rule = offending_rule

class TerminalError(RuleError):
    pass

class RegexError(RuleError):
    pass

class PredicateError(RuleError):
    pass

class EndOfStreamError(RuleError):
    pass


# helpers and extensions
def Option(rule):
    return Repeat(rule, 0, 1)

def use_explicit_new_lines(b=None):
    if b is None:
        return explicit_new_lines
    explicit_new_lines = b

explicit_new_lines = False

_match_all_whitespace = re.compile(r"\s*")
_match_whitespace_no_new_lines = re.compile(r"[^\S\n]*")

def _skip_whitespace(source, offset):
    if not explicit_new_lines:
        expression = _match_all_whitespace
    else:
        expression = _match_whitespace_no_new_lines
    result = expression.match(source, offset)
    if not result:
        return offset
    else:
        return offset + len(result[0])
