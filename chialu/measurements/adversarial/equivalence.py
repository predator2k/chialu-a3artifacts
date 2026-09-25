"""Exhaustive SAT equivalence to behavioral multiplication at adversarial widths."""
import json
from pathlib import Path
from adir.registry import underlying
from chialu.eda import equiv_check
from chialu.targets.rtl.families import mul
from chialu.targets.rtl import families as FAM
rows=[]
for width in (3,5,7):
    name,rtl,_=mul.mul_sv(width,True,'direct_pp_parallel',{'group_bits':2},name='dut')
    rtl += FAM.library_closure(rtl)
    reference=f'module dut(input [{width-1}:0] a,b, output [{2*width-1}:0] p); assign p=$signed(a)*$signed(b); endmodule'
    result=underlying(equiv_check)(rtl,reference,'dut',60)
    rows.append(dict(width=width,family='direct_pp_parallel',pins={'group_bits':2},result=result))
    print(width,result,flush=True)
Path('measurements/adversarial/grouped_equivalence.json').write_text(json.dumps(rows,indent=2)+'\n')
