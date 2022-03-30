from typing import Tuple
from gate import Node, Gate, And

class Circuit:
    def __init__(self, *primary_inputs):#, primary_outputs: list[Node], internal_nodes: list[Node], gates: list[Gate]):
        self.inputs = list(primary_inputs)
        self.outputs, self.gates, self.nodes = self.parse_circuit(self.inputs)
        # self.outputs = primary_outputs
        # self.internal_nodes = internal_nodes
        # self.gates = gates
        # todo find outputs automatically from gates

    def parse_circuit(self, inputs: list[Node]):
        """
        goes through the inputs and finds all the primary outputs and all of the internal nodes and gates
        :param inputs: mapping from str to Node
        """
        outputs = {}
        gates = {}
        nodes = {}

        unexplored_nodes = inputs.copy()
        while len(unexplored_nodes) > 0:
            node = unexplored_nodes.pop(0)
            nodes[node.name] = node
            if node.is_po():
                outputs[node.name] = node
            for gate in node.gates:
                if gate.output.name not in nodes and gate.output.name not in unexplored_nodes:
                    unexplored_nodes.append(gate.output)
                gates[gate.name] = gate

        return outputs, gates, nodes


    def reset(self):
        for gate in self.gates:
            gate.reset()

    def set_inputs(self, inputs):
        assert len(inputs) == len(self.inputs)
        for idx in range(len(self.inputs)):
            self.inputs[idx].state = inputs[idx]

    def get_outputs(self):
        outputs = []
        for node in self.outputs.values():
            outputs.append(node.state)
        return outputs

    def propagate(self, inputs, verbose=False):
        self.set_inputs(inputs)
        for gate in self.gates.values():
            gate.propagate(verbose=verbose)
        return self.get_outputs()

    def __repr__(self):
        print("Circuit Object:")
        for gate in self.gates:
            print(self.gates[gate])
        print(f"Inputs: {self.inputs.values()}")
        print(f"Outputs: {self.outputs.values()}")