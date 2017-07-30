class BaseNode:
    pass

class Node(BaseNode):
    def __init__(self, offset, name=None):
        self.offset = offset
        self.end_offset = None
        self.name = name
        self.nodes = []

    def __as_dict__(self):
        return {"name": o.name, "nodes": [node.__as_dict__() for node in o.nodes]}

class Token(BaseNode):
    def __init__(self, offset, value):
        self.offset = offset
        self.value = value

    def __as_dict__(self):
        return {"offset": o.offset, "value": o.value}


class NodeInspector:
    def __init__(self, target):
        if not isinstance(target, Node):
            raise TypeError
        self.target = target
        self.names = {}
        self.values = []
        for node in target.nodes:
            if isinstance(node, Node):
                if node.name in self.names:
                    self.names[node.name] += [node]
                else:
                    self.names[node.name] = [node]
            else:
                self.values.append(node)
        self.mask = NodeMask(self)

class NodeMask:
    def __init__(self, inspector):
        super().__setattr__("_inspector", inspector)
        super().__setattr__("_offset", inspector.target.offset)
        super().__setattr__("_end_offset", inspector.target.end_offset)

    def __str__(self):
        target = self._inspector.target
        n = target.name
        v = len(self._inspector.values)
        s = ", ".join(("{}[{}]".format(k, len(v)) for k,v in self._inspector.names))
        return "<NodeMask name={}; values=[{}], nodes=[{}]>".format(n, v, s)

    def __getattr__(self, name):
        names = self._inspector.names
        nodes = names.get(name)
        if nodes is not None:
            nodes = [NodeInspector(node).mask for node in nodes]
        return nodes

    def __setattr__(self, name, value):
        raise AttributeError
    
    def __getitem__(self, i):
        return self._inspector.values[i]
    
    def __len__(self):
        return len(self._inspector.values)

    def __iter__(self):
        return iter(self._inspector.values)

    def __as_dict__(self):
        return self._inspector.target.__as_dict__()