from typing import TypeVar, Generic

# needed because node and gate classes reference each other
GateType = TypeVar("GateType")

def generate_name(count):
    quot, rem = divmod(count - 1, 26)
    return generate_name(quot) + chr(rem + ord('A')) if count != 0 else ''


class Node:
    name_count = 0

    def __init__(self, name: str=None, gate_output: GateType=None, stuck_at=None):
        self.stuck_at = stuck_at
        self.state = 'X'
        self.gates = []  # gates for which this node is an input
        self.gate_output = gate_output  # gate for which this node is an output, None for PI
        if name is not None:
            self.name = name
        else:
            Node.name_count += 1
            self.name = generate_name(self.name_count)

    def reset(self):
        self.state = 'X'

    def set_state(self, val):
        if self.stuck_at == 0 and val == 1:
            self.state = 'D'
            return
        if self.stuck_at == 1 and val == 0:
            self.state = '~D'
            return
        self.state = val

    def is_po(self):
        return len(self.gates) == 0

    def is_pi(self):
        return self.gate_output == None

    def __repr__(self):
        return f"Node {self.name}: {self.state}"


class Gate(Generic[GateType]):
    """
    Deals with 5 logic values:
    0, 1, X (undetermined), D (1 on good circuit, 0 on bad circuit) and ~D (not D)
    Inputs may not have both X's and D's
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
        self.output = Node(gate_output=self)  # will get set after propagate() is called
        self.depth = self.set_depth()  # max number of gates between this one and PIs

    def set_depth(self):
        """
        Determines max number of gates between this one and primary inputs.  Used so that circuit
        propagation does not run into any dependency issues.

        Depth = max(depth of gates connected to inputs) + 1
        """
        depth = 0
        for input in self.inputs:
            if input.is_pi():
                continue
            # the input is the output of some gate
            if input.gate_output.depth > depth:
                depth = input.gate_output.depth
        return depth + 1

    def reset(self):
        for node in self.inputs:
            node.reset()
        self.output.reset()

    def propagate(self, verbose=False):
        """Propagate the current value of the gate's input Node to the output Node."""
        inputs = []
        for node in self.inputs:
            # if node.state == None:
            #     raise ValueError(f"{node} for input to gate {self.name} has state None, must be set before"
            #                      f" calling propagate().")
            inputs.append(node.state)
        self.output.set_state(self._propagate(inputs))
        if verbose:
            print(self)
        return self.output.state

    def _propagate(self, inputs):
        """Calls appropriate function"""
        return int(getattr(self, f"{self.type}_propagate")(inputs))

    def invert(self, val):
        inverted = {
            'X': 'X',
            'D': '~D',
            '~D': 'D',
            0: 1,
            1: 0,
        }
        return inverted[val]

    def not_propagate(self, inputs):
        assert len(inputs) == 1
        return self.invert(inputs[0])

    def and_propagate(self, inputs):
        assert len(inputs) > 1

        if 0 in inputs: # at least 1 zero
            return 0

        if all(inputs): # all ones
            return 1

        if 'X' in inputs:
            return 'X'

        # now there should only be D and/or ~D and 1's.
        d_found = 'D' in inputs
        d_prime_found = '~D' in inputs

        if d_found and not d_prime_found:
            return 'D'
        if not d_found and d_prime_found:
            return '~D'

        return 0

    def or_propagate(self, inputs):
        assert len(inputs) > 1
        for inp in inputs:
            if inp == 1:
                return 1
        return 0

    def nand_propagate(self, inputs):
        return self.invert(self.and_propagate(inputs))

    def __repr__(self):
        return f"Gate {self.name} (depth {self.depth}):\t{self.output} \t= \t{self.type.upper()}{self.inputs}"


class Not(Gate):
    def __init__(self, *inputs):
        super().__init__("not", *inputs)


class And(Gate):
    def __init__(self, *inputs):
        super().__init__("and", *inputs)


class Or(Gate):
    def __init__(self, *inputs):
        super().__init__("or", *inputs)
