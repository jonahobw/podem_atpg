from typing import Tuple
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
            print(f"\nImplication Stack:\tAssigned {node} to {val}")
            print(f"Implication Stack:\t{self.get_assignments()}\n")

    def backtrack(self):
        if self.verbose:
            print("\nImplication Stack:\tbacktracking.")
        if self.all_combinations_tried:
            return False
        current = self.set_x()
        while current.alternative_tried:
            if len(self.stack) == 0:
                # no combinations left
                if self.verbose:
                    print(
                        "\nImplication Stack:\tSetting all_combinations_tried to True."
                    )
                self.all_combinations_tried = True
                return False
            current = self.set_x()

        opposite = [1, 0]
        self.imply(current.node, opposite[current.val], True)
        return True

    def set_x(self):
        """Sets the last implied node to an X and removes from the implication stack."""
        last_implication = self.stack.pop(-1)
        last_implication.assign("X")
        if self.verbose:
            print(
                f"\nImplication Stack:\tUnassigned {last_implication.node} to {last_implication.node.state}"
            )
            print(f"Implication Stack:\t{self.get_assignments()}\n")
        return last_implication

    def get_assignments(self):
        assigments = {}
        for assigment in self.stack:
            assigments[assigment.node] = assigment.val
        return assigments

    def more_tests_possible(self):
        res = not self.all_combinations_tried
        if self.verbose:
            print(
                f"\nImplication Stack:\t{'all combinations exhausted!' if not res else 'more combinations to check.'}"
            )
        return res


def podem(
    circuit: Circuit,
    faulty_node: Node,
    stuck_at: int,
    implication_stack: ImplicationStack,
    verbose: bool = False,
):
    while not circuit.fault_propagated(verbose=verbose):
        if (
            circuit.x_path_check(fault_node=faulty_node, verbose=verbose)
            and implication_stack.more_tests_possible()
        ):
            node, val = circuit.objective(faulty_node, stuck_at, verbose=verbose)
            pi, pi_val = circuit.backtrace(node, val, verbose=verbose)
            implication_stack.imply(pi, pi_val)
            circuit.propagate(verbose=verbose)
            if podem(
                circuit, faulty_node, stuck_at, implication_stack, verbose=verbose
            ):
                return True
            # backtrack
            backtrack_success = implication_stack.backtrack()
            circuit.propagate(verbose=verbose)
            if backtrack_success and podem(
                circuit, faulty_node, stuck_at, implication_stack, verbose=verbose
            ):
                return True
            if backtrack_success:
                implication_stack.set_x()
            return False
        elif not implication_stack.more_tests_possible():
            return False
        else:
            implication_stack.backtrack()
            circuit.propagate(verbose=verbose)
    return True


def run_podem(
    circuit: Circuit, faulty_node: Node, stuck_at: int, verbose=True
) -> Tuple[bool, ImplicationStack]:
    circuit.reset()
    circuit.propagate(verbose=False)
    faulty_node.make_faulty(stuck_at=stuck_at, set=False)
    if verbose:
        print(f"Testing node {faulty_node} stuck at {stuck_at}.")
    implication_stack = ImplicationStack(verbose=verbose)
    res = podem(circuit, faulty_node, stuck_at, implication_stack, verbose=verbose)
    if verbose:
        print(implication_stack.get_assignments())
    faulty_node.remove_fault()
    return res, implication_stack


def run_all_nodes_podem(circuit: Circuit, verbose: bool = True):
    res = {}  # See details below on this data structure
    """
    {
        Node_name:
        {
            0:  # for stuck at 0
            {
                "test_possible": True,
                "assignements":
                {
                    PI_Node: value
                }
            }
            1:
            {
                ...
            }
        }
    }
    """

    for node in circuit.nodes:
        if node.is_pi() or node.is_po():
            continue
        res[node] = {}
        for stuck_at in [0, 1]:
            test_possible, stack = run_podem(
                circuit, faulty_node=node, stuck_at=stuck_at, verbose=verbose
            )
            res[node][stuck_at] = {
                "test_possible": test_possible,
                "assignments": stack.get_assignments(),
            }
    return res
