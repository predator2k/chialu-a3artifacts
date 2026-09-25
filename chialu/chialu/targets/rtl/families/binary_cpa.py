"""Selected adders presented with an ordinary binary sum/carry contract.

Native EAC characterization remains modular. Binary consumers install
that same native module inside an explicit representation decoder.
"""
from __future__ import annotations


def adder_module(family, pins, width):
    from chialu.targets.rtl import families as FAM
    selected = FAM.adder_module(family, pins, width)
    if selected is None or family != 'end_around_carry':
        return selected
    from .redundant import Mod
    from .rns_cpa import raw_binary
    name = f'fam_binary_decode_{selected.name}'
    ports = f'input logic [{width-1}:0] a,b, input logic cin, output logic [{width-1}:0] s, output logic cout'
    wrapper = Mod(name,ports,'selected EAC followed by an ordinary binary sum/carry decoder')
    assert raw_binary(wrapper,family,pins,width,'a','b','cin','s','cout',module=selected)
    return FAM.Module(name,{},wrapper.render(),tuple(wrapper.control_ports.items()))
