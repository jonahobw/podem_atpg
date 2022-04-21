from typing import Tuple
from gate import Node, Gate, And

class Circuit:
    def __init__(self, *primary_inputs):#, primary_outputs: list[Node], internal_nodes: list[Node], gates: list[Gate]):
        self.inputs = list(primary_inputs)
        self.outputs, self.gates, self.nodes = self.parse_circuit(self.inputs)

        self.fault_node = self.find_fault_node()

        # these will be set when investigating a fault and calling self.find_nodes_gates_from_fault
        self.fault_pos = None
        self.fault_pis = None
        self.fault_gates = None
        self.fault_internal_nodes = None

    def parse_circuit(self, inputs: list[Node]):
        # todo switch return from dicts to list
        """
        goes through the inputs and finds all the primary outputs and all of the internal nodes and gates
        :param inputs: mapping from str to Node for primary inputs
        """
        outputs = {}    # {name: Node}
        gates = {}      # {gate_depth: {name: Gate}}
        nodes = []

        unexplored_nodes = inputs.copy()
        while len(unexplored_nodes) > 0:
            node = unexplored_nodes.pop(0)
            nodes.append(node)
            if node.is_po():
                outputs[node.name] = node
            for gate in node.gates:
                if gate.output not in nodes and gate.output not in unexplored_nodes:
                    unexplored_nodes.append(gate.output)
                depth = gate.depth
                if depth in gates:
                    gates[depth][gate.name] = gate
                else:
                    gates[depth] = {gate.name: gate}

        return outputs, gates, nodes

    def find_fault_node(self):
        faulty_nodes = []
        for node in self.nodes:
            if node.is_faulty():
                faulty_nodes.append(node)
        if len(faulty_nodes) == 1:
            return faulty_nodes[0]
        raise ValueError(f"More than 1 faulty node: {faulty_nodes}")

    def find_nodes_gates_from_fault(self, fault_node: Node = None):
        """
        Given a node with a fault, return a tuple of

        (1) dict of PI's that affect this node or this node's observability from PO's {name, Node}
        (2) dict of PO's from the fanout of this node. {name: Node}
        (3) dict of gates that affect this node or this node's observability from PO's {gate_depth: {name: Gate}}
        (4) list of internal nodes that affect this node or this node's observability from PO's

        When running ATPG based on a fault on this node, we only need to consider the PI's returned from this
        algorithm, and the rest we don't care about.  We only need to look for a D/~D on the PO's returned
        by this algorithm. And we only need to care about the gates returned by this algorithm.

        Pseudocode:
        start at fault, propagate until you reach all PO's from this gate's fanout, create PO's dict
        for each PO:
            go backward until you reach all PI's reachable from this PO, add them to the dict of PI's and gates
        """
        if not fault_node:
            fault_node = self.fault_node
            if not fault_node:
                raise ValueError("No faulty nodes in circuit.")
        primary_outputs = self.find_pos_from_node(fault_node)
        outputs_list = list(primary_outputs.values())
        seen_nodes = []
        primary_inputs = {}
        gates = {}
        nodes_to_explore = outputs_list.copy()
        while len(nodes_to_explore) > 0:
            node = nodes_to_explore.pop(-1)
            seen_nodes.append(node)
            if node.is_pi():
                primary_inputs[node.name] = node
            else:
                gate = node.gate_output
                if gate not in gates:
                    gates[gate.name] = gate
                for input in gate.inputs:
                    if input not in seen_nodes:
                        nodes_to_explore.append(input)

        # construct internal node list
        for output in outputs_list:
            seen_nodes.remove(output)
        for pi in list(primary_inputs.values()):
            seen_nodes.remove(pi)

        # set instance variables
        self.fault_node = fault_node
        self.fault_gates = gates
        self.fault_pis = primary_inputs
        self.fault_pos = primary_outputs
        self.fault_internal_nodes = seen_nodes
        return primary_outputs, primary_inputs, gates, seen_nodes

    def find_pos_from_node(self, node: Node):
        """
        Find all primary outputs reachable through the fanout of a node in the circuit using a DFS.
        Return as a dict {name, Node}
        """
        primary_outputs = {}
        seen_node_names = []
        nodes_to_explore = [node]

        while len(nodes_to_explore) > 0:
            current_node = nodes_to_explore.pop(-1)     # depth first
            seen_node_names.append(current_node.name)
            if current_node.is_po():
                primary_outputs[current_node.name] = current_node
            for gate in current_node.gates:
                output_node = gate.output
                if output_node.name not in seen_node_names:
                    nodes_to_explore.append(output_node)

        return primary_outputs

    def reset(self):
        for depth in self.gates:
            for gate_name in self.gates[depth]:
                self.gates[depth][gate_name].reset()

    def set_inputs(self, inputs):
        assert len(inputs) == len(self.inputs)
        for idx in range(len(self.inputs)):
            self.inputs[idx].state = inputs[idx]

    def get_outputs(self):
        outputs = []
        for node in self.outputs.values():
            outputs.append(node.state)
        return outputs

    def propagate(self, inputs=None, verbose=False, reset=False):
        if reset:
            self.reset()
        if inputs:
            self.set_inputs(inputs)
        depths = sorted(self.gates.keys())
        for depth in depths:
            for gate_name in self.gates[depth]:
                self.gates[depth][gate_name].propagate(verbose=verbose)
        if verbose:
            print("\n\n")
        return self.get_outputs()

    def fault_propagated(self):
        outputs = self.get_outputs()
        return 'D' in outputs or '~D' in outputs

    def get_d_frontier(self):
        """Return list of nodes on d-frontier"""
        #todo speedup by adding another parameter of [nodes] which is returned as the
        # list of internal nodes from self.find_nodes_gates_from_fault
        d_frontier = [] # list of Node objects
        for node in self.nodes:
            if node.is_on_d_frontier():
                d_frontier.append(node)
        return d_frontier

    def x_path_check(self, dfrontier=None):
        """Returns true if there is an X path from any 1 of the D frontier gates to a PO."""
        if not dfrontier:
            dfrontier = self.get_d_frontier()

        # check nodes on D-frontier
        for node in dfrontier:
            if node.has_x_path():
                return True

        # no nodes on d frontier, could be because this is the initialization, check PIs
        if len(dfrontier) == 0:
            for node in self.inputs:
                if node.has_x_path():
                    return True

        return False

    def objective(self, node_with_fault, stuck_at, d_frontier=None):
        """
        Return a node and assignment for that node that attempts to activate a target node with a certain
        stuck at fault.

        :param node_with_fault: the node which is stuck at
        :param stuck_at: either 0 or 1
        :return: a tuple of node, value that node should be set to.
        """
        opposite = [1, 0]
        assert stuck_at in opposite

        # if gate unassigned, return opposite
        if node_with_fault.state == 'X':
            return node_with_fault, opposite[stuck_at]

        # select a node from the D-Frontier
        if not d_frontier:
            d_frontier = self.get_d_frontier()
        assert len(d_frontier) > 0
        # todo method of selecting node here?  maybe depth?
        node = d_frontier[0]
        # select a gate that this node is connected to
        # todo method of selecting a gate
        gate = node.gates[0]
        # select an unassigned input to this gate
        for inp in gate.inputs:
            if inp.state == 'X':
                break
        c = 0
        if gate.control_value != -1:
            c = gate.control_value
        if gate.type in ['xor', 'xnor'] and node.cc0 < node.cc1:
            c = 1
        return node, opposite[c]

    def backtrace(self, node: Node, node_value: int):
        """
        Given a node and the value to set on that node, backtrace to a PI and assign it.

        :param node: the node which we want to set
        :param node_value: the value which we want to set on that node, either 1 or 0
        :return: a tuple of primary input node, value to set on that node
        """
        opposite = [1, 0]
        while not node.is_pi():
            if node.gate_output.type in ['nand', 'not', 'nor']:
                node_value = opposite[node_value]
                node = node.gate_output.inputs[0]
            # see if all inputs need to be set
            elif (node.gate_output.type == 'and' and node_value == 1) or \
                (node.gate_output.type == 'or' and node_value == 0):
                # select unassigned input a of gate s with hardest controllability to value v
                node = node.gate_output.get_hardest_controllable_input(node_value)
            else:
                # select unassigned input a of gate s with easiest controllability to value v
                node = node.gate_output.get_easiest_controllable_input(node_value)
        return node, node_value


    def __repr__(self):
        print("Circuit Object:")
        for gate in self.gates:
            print(self.gates[gate])
        print(f"Inputs: {self.inputs}")
        print(f"Outputs: {self.outputs.values()}")