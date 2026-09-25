"""Render a fixed parent circuit with explicit component substitution points."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Component:
    namespace: str
    slot: str
    kind: str
    width: int

    @property
    def name(self):
        return f"{self.namespace}_component_{self.slot}_{self.kind}_w{self.width}"

    @property
    def ports(self):
        from chialu.verify.family_ref import golden
        family = "ripple_carry" if self.kind == "adder" else "prefix_and_incrementer"
        return golden(self.kind, family, {}, self.width).ports

    def wrapper(self, module):
        from chialu.targets.rtl import families as FAM
        ports = self.ports
        declarations = ", ".join(f"{p.direction} wire [{p.width-1}:0] {p.name}" for p in ports)
        parameters = ", ".join(f".{k}({v})" for k, v in module.params.items())
        connections = ", ".join(f".{p.name}({p.name})" for p in ports)
        return (f"module {self.name}({declarations});\n" + module.name + " "
                + (f"#({parameters}) " if parameters else "") + f"implementation({connections});\nendmodule\n"
                + "\n".join(FAM.module_texts(module.name, module.text).values()))


@dataclass
class Template:
    name: str
    text: str = ""
    components: dict = field(default_factory=dict)

    def module(self, slot, kind, width):
        from chialu.targets.rtl.families import Module
        component = Component(self.name, slot, kind, width)
        self.components[component.name] = component
        return Module(component.name, {})

    def render(self, resolver):
        """Replace only component module bodies; the parent circuit stays fixed."""
        from chialu.targets.rtl.families import split_modules
        texts = split_modules(self.text)
        for component in self.components.values():
            module = resolver(component)
            if module is None:
                raise ValueError(f"{component.slot}: no {component.kind} at width {component.width}")
            for name, text in split_modules(component.wrapper(module)).items():
                texts[name] = text
        return "\n".join(texts.values())
