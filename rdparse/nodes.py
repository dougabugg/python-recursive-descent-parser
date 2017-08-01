class BaseNode:
    pass

class Node(BaseNode):
    def __init__(self, offset, name=None, **opts):
        self.offset = offset
        self.end_offset = None
        self.name = name
        self.nodes = []
        self.opts = opts

    def __as_dict__(self):
        return {"name": self.name, "nodes": [node.__as_dict__() for node in self.nodes]}

class Token(BaseNode):
    def __init__(self, offset, value):
        self.offset = offset
        self.value = value

    def __as_dict__(self):
        return {"offset": self.offset, "value": self.value}


class NodeInspector:
    def __init__(self, target):
        if not isinstance(target, Node):
            raise TypeError("target should be an instance of Node, not " + target.__class__)
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
        if target.opts.get("flatten"):
            if target.opts.get("as_list"):
                if len(self.names) >= 1:
                    nodes = list(self.names.values())[0]
                else:
                    nodes = []
                self.mask = [NodeInspector(node).mask for node in nodes]
            elif len(self.names) >= 1:
                nodes = list(self.names.values())[0]
                self.mask = NodeInspector(nodes[0]).mask
            else:
                self.mask = None
        # elif len(self.names) == 0 and len(self.values) == 1:
        #     self.mask = self.values[0]
        else:
            self.mask = NodeMask(self)

class NodeMask:
    def __init__(self, inspector):
        super().__setattr__("_inspector", inspector)
        super().__setattr__("_offset", inspector.target.offset)
        super().__setattr__("_end_offset", inspector.target.end_offset)
        super().__setattr__("_name", inspector.target.name)

    def __str__(self):
        target = self._inspector.target
        n = target.name
        v = len(self._inspector.values)
        s = ", ".join(("{}[{}]".format(k, len(v)) for k,v in self._inspector.names))
        return "<NodeMask name={}; values=[{}], nodes=[{}]>".format(n, v, s)

    def __getattr__(self, name):
        names = self._inspector.names
        nodes = names.get(name)
        if nodes:
            node = NodeInspector(nodes[0]).mask
        else:
            node = None
        return node

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