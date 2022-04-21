from typing import List, Union
from circuit import Circuit
from gate import Node, Gate


def get_po_list(circuit:Circuit, fault_node:Node) -> List[Node]:
    return list(circuit.find_pos_from_node(fault_node).values())


# alternatively call circuit.has_fault_propagated (assumes circuit.propagate has already been called)
def has_fault_propagated(circuit:Circuit, inputs: List[Union[int, str]]):
    output = circuit.propagate(inputs=inputs)
    return 'D' in output or '~D' in output

def get_d_frontier(circuit:Circuit):
    # todo speedup by calling circuit.find_nodes_gates_from_fault()
    return circuit.get_d_frontier()


def x_path_check(circuit:Circuit, dfrontier: List[Node]):
    return circuit.x_path_check(dfrontier=dfrontier)