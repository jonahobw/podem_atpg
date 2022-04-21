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

    def set_stuck_at(self, stuck_at):
        self.stuck_at = stuck_at

    def reset(self):
        self.state = 'X'

    def is_faulty(self):
        return self.stuck_at != None

    def is_fanout(self):
        return len(self.gates) > 1

    def set_state(self, val):
        if self.is_faulty() and val in ['D', '~D']:
            raise ValueError(f"Trying to assign {val} to a faulty gate {self}")
        if self.stuck_at == 0 and val == 1:
            self.state = 'D'
            return
        if self.stuck_at == 1 and val == 0:
            self.state = '~D'
            return
        self.state = val

    def is_po(self):
        return len(self.gates) == 0

    def is_on_d_frontier(self):
        """
        In order to be true, the state of this node must be D or ~D and one of the gates
        which this node is connected to must have an output of X.
        """

        if self.is_po():
            return False

        if not self.state == 'D' or not self.state == '~D':
            return False

        gate_outs = [gate.output for gate in self.gates]
        return 'X' in gate_outs

    def has_x_path(self):
        """Returns true if there is a path with only X's from this node to a PO."""
        explored = []
        # list of gates which have state X
        to_explore = [gate.output for gate in self.gates if gate.output.state == 'X']
        while len(to_explore) > 0:
            node = to_explore.pop(-1)   # dfs
            explored.append(node)
            if node.is_po():
                return True
            for gate in node.gates:
                if gate.output.state == 'X':
                    to_explore.append(gate.output)
        return False

    def is_pi(self):
        return self.gate_output == None

    def __repr__(self):
        return f"Node {self.name}: {self.state}"


class Gate(Generic[GateType]):
    """
    Deals with 5 logic values:
    0, 1, X (undetermined), D (1 on good circuit, 0 on bad circuit) and ~D (not D)
    Inputs may have both X's and D's
    """
    name_counts = {
        "not": 0,
        "and": 0,
        "nand": 0,
        "or": 0,
        "nor": 0,
        "xor": 0,
        "xnor": 0
    }

    def __init__(self, type, *inputs: Node):
        self.control_value = -1     # will be set to 0 for and/nand, 1 for or/nor
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
        output = self._propagate(inputs)
        self.output.set_state(output)

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

        if 0 in inputs: # at least one 0
            return 0

        if all(inputs): # all 1's
            return 1

        # if we get to here, we know there are no 0's, just 1, X, D, ~D

        d_found = 'D' in inputs
        d_prime_found = '~D' in inputs

        if d_found and d_prime_found:
            return 0

        # if we get here, we know that there are not both D and ~D.  There also might be X's and 1's
        if 'X' in inputs:
            return 'X'

        if d_found and not d_prime_found:
            return 'D'
        if not d_found and d_prime_found:
            return '~D'

        return 0

    def or_propagate(self, inputs):
        assert len(inputs) > 1

        if 1 in inputs: # at least one 1
            return 1

        if not any(inputs): # all 0's
            return 0

        # if we get to here, we know there are no 1's, just 0, X, D, ~D
        if 'D' in inputs:
            return 'D'

        d_found = 'D' in inputs
        d_prime_found = '~D' in inputs

        if d_found and d_prime_found:      # there is at least one 1
            return 1

        if 'X' in inputs:       # covers X's and D's or X's and ~D's
            return 'X'

        if d_found:     # covers D's
            return 'D'

        # covers ~D's
        return '~D'

    def nand_propagate(self, inputs):
        return self.invert(self.and_propagate(inputs))

    def nor_propagate(self, inputs):
        return self.invert(self.or_propagate(inputs))

    def xor_propagate(self, inputs):
        def xor_2inp(a, b):
            first_and = self.and_propagate([a, self.invert(b)])
            second_and = self.and_propagate([b, self.invert(a)])
            return self.or_propagate([first_and, second_and])

        val = inputs.pop(-1)

        while len(inputs) > 0:
            new_val = inputs.pop(-1)
            val = xor_2inp(val, new_val)

        return val

    def xnor_propagate(self, inputs):
        return self.invert(self.xor_propagate(inputs))

    def __repr__(self):
        return f"Gate {self.name} (depth {self.depth}):\t{self.output} \t= \t{self.type.upper()}{self.inputs}"


class Not(Gate):
    def __init__(self, *inputs):
        super().__init__("not", *inputs)


class And(Gate):
    def __init__(self, *inputs):
        super().__init__("and", *inputs)
        self.control_value = 0


class Or(Gate):
    def __init__(self, *inputs):
        super().__init__("or", *inputs)
        self.control_value = 1

class Nand(Gate):
    def __init__(self, *inputs):
        super().__init__("nand", *inputs)
        self.control_value = 0


class Nor(Gate):
    def __init__(self, *inputs):
        super().__init__("nor", *inputs)
        self.control_value = 1

class Xor(Gate):
    def __init__(self, *inputs):
        super().__init__("xor", *inputs)

class Xnor(Gate):
    def __init__(self, *inputs):
        super().__init__("xnor", *inputs)
