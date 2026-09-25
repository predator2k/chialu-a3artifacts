"""A compilation error must never execute a stale passing simulation."""
from pathlib import Path
import json
import subprocess
import tempfile
from unittest.mock import patch

from chialu.targets.rtl.families import selftest as native
from chialu.verify import combinational_sim as checked
from chialu.verify.combinational_sim_check_selftest import network
from chialu import eda


def native_cases(root):
    """`run_case` compiles through `chialu.verify.simulate`, so the fake
    stands in for its `run_group`: Verilator's own exit status and the
    compiled model under the case's work directory `t`."""
    from chialu.verify import simulate as SIM
    cases = [('missing',False),('exit',False),('errors',False),('simulation_exit',False),
             ('no_output',False),('misleading_pass',False),('success',True),('warning',True),
             ('conformance',True),('incomplete_conformance',False),('empty_conformance',False)]
    for label, expected in cases:
        directory = root/label/'dut'
        directory.mkdir(parents=True)
        artifact = directory/'t'/'sim'
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text('stale passing simulation')
        simulated = []
        def run(argv, **kwargs):
            if argv[0] == 'verilator':
                assert not artifact.exists(), 'old compiled artifact survived'
                if label != 'missing':
                    artifact.parent.mkdir(parents=True, exist_ok=True)
                    artifact.write_text('fresh compilation')
                errors = '%Error: dut.sv:1: missing wire\n%Error: Exiting due to 1024 error(s)\n' if label == 'errors' else ''
                if label == 'warning':
                    errors = '%Warning-UNOPTFLAT: dut.sv:1: Signal unoptimizable\n'
                return subprocess.CompletedProcess(argv,int(label in ('exit','errors')),'',errors)
            assert argv[0].endswith('sim')
            assert artifact.read_text() == 'fresh compilation'
            simulated.append(True)
            output={'misleading_pass':'NOT A PASS','conformance':'CONFORMANCE PASS 6848/6848','no_output':'',
                    'incomplete_conformance':'CONFORMANCE PASS 2/3','empty_conformance':'CONFORMANCE PASS 0/0'}.get(label,'PASS')
            return subprocess.CompletedProcess(argv,int(label == 'simulation_exit'),output+'\n' if output else '','')
        with patch.object(SIM,'run_group',side_effect=run):
            result = native.run_case('','dut','module tb; endmodule\n',directory.parent)
        assert result.endswith(': PASS') == expected,(label,result)
        if label in ('missing','exit','errors'):
            assert not simulated,label
    return len(cases)


def seed_cases():
    from chialu.verify import simulate as SIM
    for label in ('missing','errors','simulation_exit'):
        simulated = []
        def run(argv, **kwargs):
            artifact = Path(kwargs['cwd'])/'obj_sim'/'sim'
            if argv[0] == 'verilator':
                assert not artifact.exists()
                if label != 'missing':
                    artifact.parent.mkdir(parents=True, exist_ok=True)
                    artifact.write_text('fresh')
                return subprocess.CompletedProcess(argv,int(label=='errors'),'','%Error: 1024 errors\n' if label=='errors' else '')
            simulated.append(True)
            return subprocess.CompletedProcess(argv,1,'CONFORMANCE PASS 1/1\n','fatal after output')
        with patch.object(SIM,'run_group',side_effect=run):
            error,stdout,dump = eda._sim_bundle('',{'tb.sv':'module tb; endmodule'},'tb.sv','',30)
        assert error and error['pass'] is False
        assert error['phase'] == ('sim' if label=='simulation_exit' else 'compile')
        assert bool(simulated) == (label=='simulation_exit')
    return 3


def checked_cases(root):
    for label in ('missing','errors'):
        directory = root/label
        directory.mkdir(parents=True)
        (directory/'obj_sim').mkdir(parents=True, exist_ok=True)
        (directory/'obj_sim'/'sim').write_text('stale')
        (directory/'expected.hex').write_text('0\n')
        (directory/'vectors.hex').write_text('0\n')
        simulated = []
        def run(argv, **kwargs):
            if argv[0] == 'yosys':
                (directory/'network.json').write_text(json.dumps({'modules':{'dut':network('$and',1,1,1)}}))
            if argv[0] == 'verilator' and '--version' not in argv:   # the tool probe precedes the compile
                assert not (directory/'obj_sim'/'sim').exists()
                if label == 'errors':
                    (directory/'obj_sim').mkdir(parents=True, exist_ok=True)
                    (directory/'obj_sim'/'sim').write_text('fresh but errored')
                    kwargs['stderr'].write('%Error: 1024 errors\n')
                    return subprocess.CompletedProcess(argv,1)
            if str(argv[0]).endswith('sim'):
                simulated.append(True)
            return subprocess.CompletedProcess(argv,0)
        with patch.object(checked.subprocess,'run',side_effect=run):
            try:
                checked.simulate('module dut; endmodule\n','dut','module tb; endmodule\n',directory)
            except (ValueError, subprocess.CalledProcessError):   # a check that refuses, or a tool's own exit status
                pass
            else:
                raise AssertionError('failed checked compilation accepted')
        assert not simulated
        record=json.loads((directory/'procedural-result.json').read_text())
        assert record['pass'] is False and 'failure' in record
    return 2


def main():
    with tempfile.TemporaryDirectory(prefix='chialu-sim-artifact-') as directory:
        root=Path(directory)
        count=native_cases(root/'native')+seed_cases()+checked_cases(root/'checked')
        # Real tools retain the normal passing route after the new gate.
        result=native.run_case('','real','module tb; initial begin $display("PASS"); $finish; end endmodule\n',root)
        assert result.endswith(': PASS'),result
    print(f'PASS {count} compilation/simulation artifact cases and a real Verilator smoke')


if __name__ == '__main__':
    main()
