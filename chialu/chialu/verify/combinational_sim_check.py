"""Independently check a straight-line SV evaluation against Yosys cells.

The checker parses source; it does not re-render or import the emitter.
Input copies establish the induction base. Each subsequent assignment
must implement one complete JSON cell using already-written wire bits.
The verified output concatenation closes the induction. This proves the
restricted SV source corresponds to the supplied, elaborated JSON graph;
it does not prove the frontend's transformation of the original RTL.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


SOURCE_SHA256_AT_IMPORT = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class CorrespondenceError(ValueError):
    """The source or graph is outside the checked correspondence."""


_BINARY = {
    '$and': '&', '$or': '|', '$xor': '^', '$ge': '>=', '$gt': '>',
    '$lt': '<', '$logic_and': '&&', '$mul': '*', '$sub': '-', '$add': '+', '$eq': '==',
}
_MUXES = {'$mux', '$_MUX_'}
_UNARY = {'$not': '~', '$logic_not': '!', '$neg': '-'}
_CONSTANTS = {'0', '1', 'x'}
_IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z', re.ASCII)
# These are reserved by Verilog/SystemVerilog, not available as bare names.
_KEYWORDS = set("""
accept_on alias always always_comb always_ff always_latch and assert assign
assume automatic before begin bind bins binsof bit break buf bufif0 bufif1
byte case casex casez cell chandle checker class clocking cmos config const
constraint context continue cover covergroup coverpoint cross deassign default
defparam design disable dist do edge else end endcase endchecker endclass
endclocking endconfig endfunction endgenerate endgroup endinterface endmodule
endpackage endprimitive endprogram endproperty endsequence endspecify endtable
endtask enum event eventually expect export extends extern final first_match
for force foreach forever fork forkjoin function generate genvar global highz0
highz1 if iff ifnone ignore_bins illegal_bins implements implies import incdir
include initial inout input inside instance int integer interconnect interface
intersect join join_any join_none large let liblist library local localparam
logic longint macromodule matches medium modport module nand negedge nettype
new nexttime nmos nor noshowcancelled not notif0 notif1 null or output package
packed parameter pmos posedge primitive priority program property protected
pull0 pull1 pulldown pullup pulsestyle_ondetect pulsestyle_onevent pure rand
randc randcase randsequence rcmos real realtime ref reg reject_on release repeat
restrict return rnmos rpmos rtran rtranif0 rtranif1 s_always s_eventually
s_nexttime s_until s_until_with scalared sequence shortint shortreal
showcancelled signed small soft solve specify specparam static string strong
strong0 strong1 struct super supply0 supply1 sync_accept_on sync_reject_on
table tagged task this throughout time timeprecision timeunit tran tranif0
tranif1 tri tri0 tri1 triand trior trireg type typedef union unique unique0
unsigned until until_with untyped use uwire var vectored virtual void wait
wait_order wand weak weak0 weak1 while wildcard wire with within wor xnor xor
""".split())


def _require(condition, message):
    if not condition:
        raise CorrespondenceError(message)


def _identifier(value):
    _require(isinstance(value, str) and bool(_IDENTIFIER.fullmatch(value))
             and value not in _KEYWORDS, f'unsupported identifier {value!r}')
    return value


def _parameter(value, name):
    if type(value) is int:
        return value
    _require(isinstance(value, str) and len(value) <= 64
             and bool(re.fullmatch('[01]+', value)), f'invalid cell parameter {name}')
    return int(value, 2)


def _bits(value, where):
    _require(isinstance(value, list) and bool(value), f'empty or invalid connection {where}')
    for bit in value:
        _require((type(bit) is int and bit >= 2)
                 or (type(bit) is str and bit in _CONSTANTS), f'invalid wire bit {bit!r} in {where}')
    return tuple(value)


@dataclass(frozen=True, slots=True)
class _Cell:
    name: str
    kind: str
    a: tuple
    b: tuple
    select: tuple
    y: tuple
    cast_a: bool
    cast_b: bool


class _Source:
    # Whitespace is the only skipped material: no attributes, directives,
    # comments, strings, declarations or statements can hide in ignored text.
    token = re.compile(r"\s*(1'b[01x]|[0-9]+|\$signed|[A-Za-z_][A-Za-z_0-9]*|>=|&&|==|[&|^~!>*<+\-?:=,;(){}\[\]])",
                       re.ASCII)

    def __init__(self, source, last_bank):
        _require(isinstance(source, str) and source.isascii(), 'source must be ASCII text')
        self.source = source
        self.position = 0
        self.cached = None
        self.last_bank = last_bank

    def fail(self, message):
        raise CorrespondenceError(f'{message} near source offset {self.position}')

    def peek(self):
        if self.cached is None:
            if self.position == len(self.source):
                self.cached = ''
            else:
                match = self.token.match(self.source, self.position)
                if match is None:
                    if self.source[self.position:].strip():
                        self.fail('token outside the restricted grammar')
                    self.cached = ''
                    self.position = len(self.source)
                else:
                    self.cached = match[1]
                    self.position = match.end()
        return self.cached

    def take(self):
        value = self.peek()
        self.cached = None
        return value

    def expect(self, value):
        if self.take() != value:
            self.fail(f'expected {value!r}')

    def uint(self):
        value = self.take()
        if not value.isdigit() or len(value) > 12:
            self.fail('expected a bounded unsigned decimal integer')
        return int(value)

    def bits(self, depth=0):
        if depth > 16:
            self.fail('excessive concatenation nesting')
        token = self.take()
        if token in ("1'b0", "1'b1", "1'bx"):
            return (token[-1],)
        if token == '{':
            parts = [self.bits(depth + 1)]
            while self.peek() == ',':
                self.take()
                parts.append(self.bits(depth + 1))
            self.expect('}')
            return tuple(bit for part in reversed(parts) for bit in part)
        if token != 'n':
            self.fail('expected a wire-bank reference or one-bit literal')
        self.expect('[')
        bank = self.uint()
        self.expect(']')
        if bank > self.last_bank:
            self.fail('wire-bank index exceeds its declaration')
        low, high = 0, 63
        if self.peek() == '[':
            self.take()
            high = self.uint()
            low = high
            if self.peek() == ':':
                self.take()
                low = self.uint()
            self.expect(']')
        if not 0 <= low <= high < 64:
            self.fail('invalid wire-bank bit range')
        return tuple(range(bank * 64 + low, bank * 64 + high + 1))

    def operand(self):
        signed = self.peek() == '$signed'
        if signed:
            self.take()
            self.expect('(')
        bits = self.bits()
        if signed:
            self.expect(')')
        return bits, signed

    def operation(self):
        if self.peek() in ('~', '!', '-'):
            operator = self.take()
            a, cast = self.operand()
            return operator, a, (), (), cast, False
        if self.peek() == '(':
            self.take()
            a, cast_a = self.operand()
            self.expect(')')
            operator = self.take()
            if operator not in _BINARY.values():
                self.fail('unsupported binary operator')
            self.expect('(')
            b, cast_b = self.operand()
            self.expect(')')
            return operator, a, b, (), cast_a, cast_b
        select = self.bits()
        self.expect('?')
        when_true = self.bits()
        self.expect(':')
        when_false = self.bits()
        return '?:', when_false, when_true, select, False, False


def verify_source(module: dict, source: str, top: str) -> dict:
    """Check the restricted source against one unmodified Yosys module.

    Raises CorrespondenceError on any unsupported cell, malformed graph,
    extra source, changed operation/connection, or read-before-write.
    Width and signedness conventions match the corresponding simlib cells.
    X literals are preserved; this is not a claim that original RTL or its
    frontend lowering is proved, nor that unknown simulation outputs pass.
    """
    _identifier(top)
    _require(isinstance(module, dict), 'module must be a dictionary')
    _require(set(module) <= {'attributes', 'ports', 'cells', 'netnames',
                             'parameter_default_values', 'memories', 'processes'}, 'unknown module field')
    attributes = module.get('attributes', {})
    _require(isinstance(attributes, dict) and isinstance(module.get('netnames', {}), dict), 'invalid module metadata')
    for attribute in ('blackbox', 'whitebox'):
        value = attributes.get(attribute, 0)
        _require(value == 0 or (isinstance(value, str) and bool(re.fullmatch('0+', value))),
                 'opaque module has no checked combinational meaning')
    _require(not module.get('memories') and not module.get('processes'), 'unlowered memory or process')
    _require(not module.get('parameter_default_values'), 'procedural module must have no external parameters')
    ports, raw_cells = module.get('ports'), module.get('cells')
    _require(isinstance(ports, dict) and isinstance(raw_cells, dict), 'missing ports or cells')
    port_records, inputs, outputs = [], [], []
    semantic_hash = hashlib.sha256()

    def digest(value):
        semantic_hash.update(json.dumps(value, separators=(',', ':'), ensure_ascii=True).encode() + b'\n')

    for name, port in ports.items():
        _identifier(name)
        _require(name != 'evaluate', 'port name collides with evaluation function')
        _require(isinstance(port, dict) and set(port) <= {'direction', 'bits', 'signed', 'offset', 'upto'}, 'unknown port field')
        _require(port.get('direction') in ('input', 'output'), 'unsupported port direction')
        _require(port.get('offset', 0) == 0 and not port.get('upto'), 'only descending zero-based ports are supported')
        signed = port.get('signed', 0)
        _require(type(signed) in (int, bool) and signed in (0, 1), 'invalid port signedness')
        record = (name, port['direction'], bool(signed), _bits(port.get('bits'), name))
        port_records.append(record)
        (inputs if record[1] == 'input' else outputs).append(record)
        digest(record)
    _require(inputs and outputs, 'at least one input and output required')
    owners = {}

    def drive(bits, owner):
        for bit in bits:
            _require(type(bit) is int and bit not in owners, f'non-wire or multiple driver at {bit!r}')
            owners[bit] = owner

    for name, _, _, bits in inputs:
        drive(bits, ('input', name))
    by_output = {}
    kinds, metadata = Counter(), 0
    for name, cell in raw_cells.items():
        _require(isinstance(name, str), 'invalid cell name')
        _require(isinstance(cell, dict) and set(cell) <= {'type', 'parameters', 'attributes', 'hide_name',
                                                        'port_directions', 'connections'}, f'unknown cell field at {name}')
        kind = cell.get('type')
        _require(isinstance(kind, str), f'invalid cell type at {name}')
        if kind == '$scopeinfo':
            _require(cell.get('connections') == {} and cell.get('port_directions') == {}, 'connected scope metadata')
            metadata += 1
            continue
        _require(kind in set(_BINARY) | _MUXES | set(_UNARY), f'unsupported cell {name}: {kind}')
        expected_ports = {'A': 'input', 'Y': 'output'}
        if kind not in _UNARY:
            expected_ports['B'] = 'input'
        if kind in _MUXES:
            expected_ports['S'] = 'input'
        connections = cell.get('connections')
        _require(cell.get('port_directions') == expected_ports and isinstance(connections, dict)
                 and set(connections) == set(expected_ports), f'cell ports disagree at {name}')
        connected = {port: _bits(bits, name + '.' + port) for port, bits in connections.items()}
        parameters = cell.get('parameters')
        _require(isinstance(parameters, dict), f'missing parameters at {name}')
        if kind == '$_MUX_':
            expected_parameters = set()
        elif kind == '$mux':
            expected_parameters = {'WIDTH'}
        elif kind in _UNARY:
            expected_parameters = {'A_WIDTH', 'Y_WIDTH', 'A_SIGNED'}
        else:
            expected_parameters = {'A_WIDTH', 'B_WIDTH', 'Y_WIDTH', 'A_SIGNED', 'B_SIGNED'}
        _require(set(parameters) == expected_parameters, f'unknown or missing parameters at {name}')
        values = {key: _parameter(value, name + '.' + key) for key, value in parameters.items()}
        cast_a = cast_b = False
        if kind in _MUXES:
            width = values.get('WIDTH', 1)
            _require(len(connected['S']) == 1 and all(len(connected[p]) == width for p in ('A', 'B', 'Y')),
                     f'mux width mismatch at {name}')
        else:
            for port in ('A', 'Y') + (() if kind in _UNARY else ('B',)):
                _require(values[port + '_WIDTH'] == len(connected[port]), f'width mismatch at {name}.{port}')
            _require(values['A_SIGNED'] in (0, 1), f'invalid signedness at {name}')
            if kind in _UNARY:
                cast_a = bool(values['A_SIGNED'])
            else:
                _require(values['B_SIGNED'] in (0, 1), f'invalid signedness at {name}')
                cast_a = cast_b = bool(values['A_SIGNED'] and values['B_SIGNED'])
        drive(connected['Y'], ('cell', name))
        model = _Cell(name, kind, connected['A'], connected.get('B', ()), connected.get('S', ()),
                      connected['Y'], cast_a, cast_b)
        by_output[model.y] = model
        kinds[kind] += 1
        digest((name, kind, values, connected))
    last_bank = max(owners) // 64
    _require(max(owners) < 64 * max(1024, len(owners)), 'excessively sparse bit IDs')
    for cell in by_output.values():
        for bit in cell.a + cell.b + cell.select:
            _require(type(bit) is str or bit in owners, f'undriven bit {bit!r} at {cell.name}')
    for _, _, _, bits in outputs:
        _require(all(type(bit) is str or bit in owners for bit in bits), 'undriven output')

    text = _Source(source, last_bank)
    text.expect('module')
    text.expect(top)
    text.expect('(')
    for index, (name, direction, signed, bits) in enumerate(port_records):
        if index:
            text.expect(',')
        text.expect(direction)
        text.expect('wire')
        if signed:
            text.expect('signed')
        text.expect('[')
        _require(text.uint() == len(bits) - 1, f'port width changed at {name}')
        text.expect(':')
        _require(text.uint() == 0, 'nonzero port lower bound')
        text.expect(']')
        text.expect(name)
    text.expect(')')
    text.expect(';')
    text.expect('function')
    text.expect('automatic')
    text.expect('[')
    output_bits = sum(len(p[3]) for p in outputs)
    _require(text.uint() == output_bits - 1, 'function result width changed')
    text.expect(':')
    _require(text.uint() == 0, 'nonzero function lower bound')
    text.expect(']')
    text.expect('evaluate')
    text.expect(';')
    for index, (_, _, _, bits) in enumerate(inputs):
        text.expect('input')
        text.expect('[')
        _require(text.uint() == len(bits) - 1, 'function input width changed')
        text.expect(':')
        _require(text.uint() == 0, 'nonzero function-input lower bound')
        text.expect(']')
        text.expect(f'i{index}')
        text.expect(';')
    for token in ('reg', '[', '63', ':', '0', ']', 'n', '[', '0', ':'):
        text.expect(token)
    _require(text.uint() == last_bank, 'wire-bank declaration changed')
    for token in (']', ';', 'begin'):
        text.expect(token)
    written = set()
    for index, (_, _, _, bits) in enumerate(inputs):
        _require(text.bits() == bits, 'input copy changed its wire order or width')
        text.expect('=')
        text.expect(f'i{index}')
        text.expect(';')
        written.update(bits)
    assigned = set()
    while text.peek() != 'evaluate':
        lhs = text.bits()
        cell = by_output.get(lhs)
        _require(cell is not None, 'assignment does not match one complete cell output')
        _require(lhs not in assigned, f'cell assigned twice: {cell.name}')
        text.expect('=')
        operation, a, b, select, cast_a, cast_b = text.operation()
        text.expect(';')
        expected_op = '?:' if cell.kind in _MUXES else _UNARY[cell.kind] if cell.kind in _UNARY else _BINARY[cell.kind]
        _require(operation == expected_op, f'operator changed at {cell.name}')
        _require((a, b, select) == (cell.a, cell.b, cell.select), f'wire order or operand width changed at {cell.name}')
        _require((cast_a, cast_b) == (cell.cast_a, cell.cast_b), f'signedness changed at {cell.name}')
        _require(all(type(bit) is str or bit in written for bit in a + b + select),
                 f'read-before-write or combinational cycle at {cell.name}')
        written.update(lhs)
        assigned.add(lhs)
    _require(len(assigned) == len(by_output), 'source omitted cells')
    text.expect('evaluate')
    text.expect('=')
    result_bits = text.bits()
    expected_result = tuple(bit for port in reversed(outputs) for bit in port[3])
    _require(result_bits == expected_result, 'function return changed output wire order or width')
    _require(all(type(bit) is str or bit in written for bit in result_bits), 'output read-before-write')
    for token in (';', 'end', 'endfunction', 'assign', '{'):
        text.expect(token)
    for index, port in enumerate(outputs):
        if index:
            text.expect(',')
        text.expect(port[0])
    for token in ('}', '=', 'evaluate', '('):
        text.expect(token)
    for index, port in enumerate(inputs):
        if index:
            text.expect(',')
        text.expect(port[0])
    for token in (')', ';', 'endmodule', ''):
        text.expect(token)
    return {'pass': True, 'checker': 'independent_restricted_sv_v1', 'top': top,
            'proof': 'input-copy base, complete per-cell induction in source order, exact output assembly',
            'scope': 'SV correspondence to elaborated JSON; original frontend and DUT correctness are separate',
            'constants': sorted(_CONSTANTS), 'cells': len(assigned), 'types': dict(kinds),
            'ignored_metadata_cells': metadata, 'input_bits': sum(len(p[3]) for p in inputs),
            'output_bits': output_bits, 'banks': last_bank + 1,
            'unique_drivers': True, 'read_before_write': True, 'restricted_grammar': True,
            'source_sha256': hashlib.sha256(source.encode('ascii')).hexdigest(),
            'checker_source_sha256_at_import': SOURCE_SHA256_AT_IMPORT,
            'semantic_sha256': semantic_hash.hexdigest()}
