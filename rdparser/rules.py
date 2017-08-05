import re
from .nodes import Node, Token

__all__ = ('BaseRule', 'Rule', 'Join', 'Choice', 'Repeat', 'Option', 'Predicate', 'Terminal',
    'Regex', 'Empty', 'Silent', 'EndOfStream', 'RuleError', 'TerminalError',
    'RegexError', 'PredicateError', 'EndOfStreamError', 'use_explicit_new_lines')

class BaseRule:
    pass

class Rule(BaseRule):
    def __init__(self, name="", rule=None, **opts):
        self.name = name
        self.rule = rule
        self.opts = opts

    def match(self, source, offset, nodes):
        if self.rule is None:
            raise RuntimeError("rule `{}` was forward declared, but never given a value with assign_rule()".format(self.name))
        node = Node(offset, self.name, **self.opts)
        nodes.append(node)
        offset, error = self.rule.match(source, offset, node.nodes)
        node.end_offset = offset
        return offset, error

    def assign_rule(self, rule):
        self.rule = rule

class Join(BaseRule):
    def __init__(self, rules):
        self.rules = rules

    def match(self, source, offset, nodes):
        furthest = None
        failed = False
        for rule in self.rules:
            try:
                new_nodes = []
                offset, error = rule.match(source, offset, new_nodes)
                if error is not None and (furthest is None or error.offset >= furthest.offset):
                    furthest = error
            except RuleError as error:
                if furthest is None or error.offset >= furthest.offset:
                    raise
                else:
                    raise furthest
            finally:
                nodes.extend(new_nodes)
        return offset, furthest

class Choice(BaseRule):
    def __init__(self, rules):
        self.rules = rules
    
    def match(self, source, offset, nodes):
        furthest = None
        furthest_nodes = None
        success = False
        for rule in self.rules:
            try:
                new_nodes = []
                offset, error = rule.match(source, offset, new_nodes)
                furthest_nodes = new_nodes
                success = True
                if error is not None and (furthest is None or error.offset >= furthest.offset):
                    furthest = error
                break
            except RuleError as e:
                if furthest is None or e.offset >= furthest.offset:
                    furthest_nodes = new_nodes
                    furthest = e
        if not success:
            raise furthest
        nodes.extend(furthest_nodes)
        return offset, furthest

class Repeat(BaseRule):
    def __init__(self, rule, _min=None, _max=None):
        self.rule = rule
        self._min = _min
        self._max = _max
    
    def match(self, source, offset, nodes):
        last_error = None
        count = 0
        _max = self._max
        while _max is None or count < _max:
            try:
                _offset = offset
                new_nodes = []
                offset, last_error = self.rule.match(source, offset, new_nodes)
                nodes.extend(new_nodes)
                if _offset == offset:
                    raise RuntimeError("infinite loop detected inside Repeat rule")
                count += 1
            except RuleError as e:
                if self._min is not None and count < self._min:
                    nodes.extend(new_nodes)
                    raise
                else:
                    last_error = e
                    break
        return offset, last_error

class Predicate(BaseRule):
    def __init__(self, rule, predicate):
        self.rule = rule
        self.predicate = predicate
    
    def match(self, source, offset, nodes):
        try:
            new_offset, error = self.predicate.match(source, offset, [])
        except RuleError as e:
            return self.rule.match(source, offset, nodes)
        else:
            raise PredicateError(offset, "predicate matched", self.predicate)

class Terminal(BaseRule):
    def __init__(self, terminal, ignore_token=False, ignore_whitespace=True):
        self.terminal = terminal
        self.ignore_token = ignore_token
        self.ignore_whitespace = ignore_whitespace
    
    def match(self, source, offset, nodes):
        _offset = offset
        if self.ignore_whitespace:
            offset = _skip_whitespace(source, offset)
        if source.startswith(self.terminal, offset):
            offset += len(self.terminal)
            node = Token(offset, self.terminal)
            if not self.ignore_token:
                nodes.append(node)
            return offset, None
        else:
            raise TerminalError(_offset, "terminal failed to match", self)

class Regex(BaseRule):
    def __init__(self, expression, ignore_token=False, ignore_whitespace=True):
        self.expression = expression
        self.ignore_token = ignore_token
        self.ignore_whitespace = ignore_whitespace
    
    def match(self, source, offset, nodes):
        _offset = offset
        if self.ignore_whitespace:
            offset = _skip_whitespace(source, offset)
        result = self.expression.match(source, offset)
        if not result:
            raise RegexError(_offset, "regex failed to match", self)
        match = result[0]
        offset += len(match)
        if not self.ignore_token:
            nodes.append(Token(offset, match))
        return offset, None

class Empty(BaseRule):
    def match(self, source, offset, nodes):
        return offset, None

class Silent(BaseRule):
    def __init__(self, rule):
        self.rule = rule
    
    def match(self, source, offset, nodes):
        offset, error = self.rule.match(source, offset, [])
        return offset, None

class EndOfStream(BaseRule):
    def __init__(self, ignore_whitespace=True):
        self.ignore_whitespace = ignore_whitespace
    def match(self, source, offset, nodes):
        if self.ignore_whitespace:
            offset = _skip_whitespace(source, offset)
        if offset < len(source):
            raise EndOfStreamError(offset, "expected end of stream", self)
        return offset, None

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

explicit_new_lines = False

def use_explicit_new_lines(b=None):
    global explicit_new_lines
    if b is None:
        return explicit_new_lines
    explicit_new_lines = b

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
    else:
        raise TypeError("rule should be an instance of BaseRule, not " + rule.__class__)

def print_rule_tree(rule, indent="| ", indent_count=0, truncate=40):
    padding = indent * indent_count
    details = ""
    if isinstance(rule, Terminal):
        details = '"' + rule.terminal + '"'
    elif isinstance(rule, Rule):
        details = 'name=' + rule.name
    print(padding + "[{}] {}".format(rule.__class__.__name__, details))
    if truncate is not None and len(padding) > truncate:
        print(padding + indent + "<full output truncated (truncate={})>".format(truncate))
        return
    for _rule in iter_rule(rule):
        print_rule_tree(_rule, indent, indent_count + 1, truncate)
