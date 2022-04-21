from circuit import Circuit
from gate import Node

class PIAssignment:
    def __init__(self, node: Node, val: int, alternative=False):
        self.node = node
        assert val in [0, 1]
        self.val = val
        self.alternative_tried = alternative

    def assign(self, val=None):
        if not val:
            val = self.val
        self.node.set_state(val)

class ImplicationStack:

    def __init__(self, verbose=True):
        self.stack = []
        self.verbose = verbose
        self.all_combinations_tried = False

    def imply(self, node: Node, val: int, alternative=False):
        assignment = PIAssignment(node, val, alternative=alternative)
        self.stack.append(assignment)
        assignment.assign()
        if self.verbose:
            print(f"\nAssigned {node} to {val}\n")

    def backtrack(self):
        current = self.stack.pop(-1)
        while(current.alternative_tried):
            if len(self.stack) == 0:
                # no combinations left
                self.all_combinations_tried = True
                return False
            current = self.stack.pop(-1)

        opposite = [1, 0]
        self.imply(current.node, opposite[current.val], True)
        return True

    def set_x(self):
        """Sets the last implied node to an X and removes from the implication stack."""
        last_implication = self.stack.pop(-1)
        last_implication.assign('X')

    def get_assignments(self):
        assigments = {}
        for assigment in self.stack:
            assigments[assigment.node] = assigment.val
        return assigments


def podem(circuit: Circuit, faulty_node, stuck_at, implication_stack, verbose=True):
    while not circuit.fault_propagated():
        if circuit.x_path_check() or len(implication_stack.stack) == 0:
            node, val = circuit.objective(faulty_node, stuck_at)
            pi, pi_val = circuit.backtrace(node, val)
            implication_stack.imply(pi, pi_val)
            circuit.propagate(verbose=verbose)
            if podem(circuit, faulty_node, stuck_at, implication_stack):
                return True
            # backtrack
            implication_stack.backtrack()
            circuit.propagate(verbose=verbose)
            if podem(circuit, faulty_node, stuck_at, implication_stack):
                return True
            implication_stack.set_x()
            return False
        elif implication_stack.all_combinations_tried:
            return False
        else:
            implication_stack.backtrack()
            circuit.propagate(verbose=verbose)
    return True


def run_podem(circuit: Circuit):
    faulty_node = circuit.fault_node
    stuck_at = faulty_node.stuck_at
    implication_stack = ImplicationStack()
    circuit.reset()
    circuit.propagate(verbose=True)
    res = podem(circuit, faulty_node, stuck_at, implication_stack)
    return res, implication_stack.get_assignments()

