def generate_name(count):
    quot, rem = divmod(count - 1, 26)
    return generate_name(quot) + chr(rem + ord('A')) if count != 0 else ''


class Node:
    name_count = 0

    def __init__(self, name=None):
        self.state = None
        self.gates = [] # gates for which this node is an input
        if name is not None:
            self.name = name
        else:
            Node.name_count += 1
            self.name = generate_name(self.name_count)

    def reset(self):
        self.state = None

    def is_po(self):
        return len(self.gates) == 0

    def __repr__(self):
        return f"Node {self.name}: {self.state}"

class Gate:
    """
    Deals with 5 logic values:
    0, 1, X (undetermined), D (1 on good circuit, 0 on bad circuit) and D' (Opposite of D)
    Inputs may not have both X's and
    """
    name_counts = {
        "not": 0,
        "and": 0,
        "or": 0,
        "nand": 0
    }

    def __init__(self, type, *inputs: Node):
        self.type = type
        Gate.name_counts[type] += 1
        self.name = f"{type}{Gate.name_counts[type]}"
        self.inputs = list(inputs)
        for node in self.inputs:
            node.gates.append(self)
        self.output = Node()       # will get set after propagate() is called

    def reset(self):
        for node in self.inputs:
            node.reset()
        self.output.reset()

    def propagate(self, verbose=False):
        """Propagate the current value of the gate's input Node to the output Node."""
        inputs = []
        for node in self.inputs:
            if node.state == None:
                raise ValueError(f"{node} for input to gate {self.name} has state None, must be set before"
                                 f" calling propagate().")
            inputs.append(node.state)
        self.output.state = self._propagate(inputs)
        if verbose:
            print(self)
        return self.output.state

    def _propagate(self, inputs):
        """To be overridden by subclasses"""
        return int(getattr(self, f"{self.type}_propagate")(inputs))

    def not_propagate(self, inputs):
        assert len(inputs) == 1
        return not inputs[0]

    def and_propagate(self, inputs):
        assert len(inputs) > 1
        for inp in inputs:
            if inp == 0:
                return 0
        return 1

    def or_propagate(self, inputs):
        assert len(inputs) > 1
        for inp in inputs:
            if inp == 1:
                return 1
        return 0

    def nand_propagate(self, inputs):
        return not self.and_propagate(inputs)

    def __repr__(self):
        return f"{self.output} \t\t= \t{self.type.upper()}{self.inputs}"


class Not(Gate):
    def __init__(self, *inputs):
        super().__init__("not", *inputs)


class And(Gate):
    def __init__(self, *inputs):
        super().__init__("and", *inputs)


class Or(Gate):
    def __init__(self, *inputs):
        super().__init__("or", *inputs)

