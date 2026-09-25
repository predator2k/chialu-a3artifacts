"""Full Kulisch width Range with exact, active accumulator geometries."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import re
import tempfile
import time

from chialu.modules.common import FLAGS
from chialu.spaces.fma_dot_spaces import dot_acc_space
from chialu.targets.derive import seed_for
from chialu.targets.rtl.families.dot import geom_of
from chialu.targets.rtl.families.fidelity import Audit
from chialu.targets.rtl.families.selftest import run_case
from chialu.variants import Axis
from chialu.verify import dot_ref as D,tb_gen
from chialu.verify.elaboration import hierarchy_of_files
from chialu.verify.family_tb import pack_ports
from chialu.verify.formats import FloatFormat,Special,_floor_log2,parse_format

FAMILY='kulisch_long_accumulator'
CHILDREN={'align.family':'full_align','align.shifter.family':'barrel_mux_tree','align.shifter.stage_radix':4,
          'cpa.family':'parallel_prefix','cpa.topology':'brent_kung',
          'lza.family':'lzc_after_add','lza.counter.family':'lzd_cell_tree',
          'lza.counter.block_primitive':'nibble_cell','lza.counter.output_form':'binary_count',
          'lza.counter.valid_flag_propagation':True,
          'norm_shifter.family':'barrel_mux_tree','norm_shifter.stage_radix':4}


def widths():
    family=next(f for f in dot_acc_space(4).families if f.name==FAMILY)
    axis=Axis('accumulator_width_bits',family.design_choices['accumulator_width_bits'])
    values=[axis.at(i) for i in range(axis.count)]
    assert values==list(range(64,4289,32)) and len(values)==133
    return values


def geometry(width):
    """Small scalar-float fixture with a nonconstant product and no spare sign padding.

    Two products are the minimum for a real 3:2 carry-save reduction with
    C. AB stays four bits. C's exponent span provides the wide frame;
    its fraction adjusts that frame by one bit per fraction bit.
    """
    if width not in widths():raise ValueError('width is outside the declared Kulisch Range')
    ab=parse_format('fp4e2m1');ec=width.bit_length()-1;base=1<<ec
    names=[f'fps1e{ec}m0N'] if width==base else [f'fps1e{ec}m{m}NI' for m in range(max(1,width-base-2),width-base+4)]
    candidates=[]
    for name in names:
        c=parse_format(name)
        low=min(-2,-c.bias if c.exp_only else 1-c.bias-c.man_bits)
        bound=2*ab.max_finite()**2+c.max_finite()
        units=bound/Fraction(2)**low
        if units.denominator==1 and int(units).bit_length()+1==width:candidates.append((c.width,name,c,low,bound))
    if not candidates:raise ValueError(f'no exact-width scalar fixture for {width}')
    _,_,c,low,bound=min(candidates,key=lambda x:x[:2])
    # Keep zero/subnormal encodings in the destination, and choose the
    # smallest exponent field at one explicit fraction bit that represents
    # both endpoint powers. All IEEE/SR controls then use an ordinary
    # floating rounder; the accumulator's high bit cannot hide in saturation.
    for ed in range(2,16):
        d=FloatFormat(f'fps1e{ed}m1NI',ed,1)
        if d.max_finite()>=bound and d.min_positive()<=Fraction(2)**low:break
    else:raise ValueError(f'no destination spans the {width}-bit fixture')
    g=geom_of(ab,c,d,2,sr_bits=2,sr=True)
    if g.numeric_width!=width or g.lo!=low:raise ValueError('fixture would count unused accumulator padding')
    assert g.g.XW<width
    return dict(format_ab=ab.name,format_c=c.name,format_d=d.name,elements=2,
                width=width,numeric_width=g.numeric_width,frame_lsb=g.lo,behavioral_frame_width=g.AW,
                xw=g.g.XW,ew=g.g.EW,input_payload_bits=4*ab.width+c.width,
                output_bits=d.width,c_mantissa=c.man_bits,c_exponent=c.exp_bits)


# the widths a default run binds: the declared Range's two ends (64 and 4288, the exact accumulator of a
# binary64 dot product), the first step, and the frames of the evaluation's fp32 targets (about 281 bits)
# and of a binary32-exact accumulator (about 1024); --full walks all 133 widths of the Range
REPRESENTATIVE_WIDTHS = (64, 96, 288, 1024, 4288)


def cases(full=False):
    assert set(REPRESENTATIVE_WIDTHS) <= set(widths())
    for width in (widths() if full else REPRESENTATIVE_WIDTHS):
        for organization,carry in product(('monolithic','segmented_lazy_carry','banked_sub_adders','two_speed'),
                                           ('immediate','carry_save_deferred')):
            yield FAMILY,dict(accumulator_width_bits=width,organization=organization,carry_resolution=carry)


def fixture(width):
    g=geometry(width)
    spec=D.normalize_dot_spec(dict(unit='vec_dot_acc',dut_name='dot_core',check_en=False,
        modes=[{k:g[k] for k in ('format_ab','format_c','format_d','elements')}],
        rounding=['RNE','RTZ','RDN','RUP','SR'],sr_bits=2,daz_in=[False,True],ftz_out=[False,True],flags=list(FLAGS)))
    return spec,g


def vectors(spec,g,n_random):
    ab=parse_format(g['format_ab']);c=parse_format(g['format_c'])
    amin,amax=ab.min_positive(),ab.max_finite();cmin,cmax=c.min_positive(),c.max_finite()
    chigh=Fraction(2)**_floor_log2(cmax)
    # Four positive exact words cover every magnitude position. The first
    # two fill the gap between C's tiny quantum and its high exponent with
    # real borrow propagation, not negative sign extension.
    rows=[((amin,0),(amin,0),-cmin),((-amin,0),(amin,0),chigh),
          ((0,0),(0,0),cmax),((amax,amax),(amax,amax),cmax),
          ((0,0),(0,0),cmin),((amin,amin),(amin,amin),amin*amin),
          ((-amin,-amin),(amin,amin),chigh),((1,0),(1,0),-Fraction(1)),
          ((Fraction(3,2),0),(1,0),-Fraction(1)),((1,1),(1,1),Fraction(1)),
          ((amax,-amax),(amax,amax),cmin)]
    rows += [(tuple(-x for x in a),b,-cc) for a,b,cc in list(rows)]
    encode_a=lambda values:sum(ab.encode(value)<<(i*ab.width) for i,value in enumerate(values))
    operands=[dict(a=encode_a(a),b=encode_a(b),c=c.encode(cc)) for a,b,cc in rows]
    for code in c.corners():operands.append(dict(a=encode_a((1,0)),b=encode_a((1,0)),c=code))
    rng=random.Random(947)
    operands += [dict(a=rng.randrange(1<<(2*ab.width)),b=rng.randrange(1<<(2*ab.width)),c=rng.randrange(1<<c.width)) for _ in range(n_random)]
    result=[]
    for rnd,rounding in enumerate(spec['rounding']):
        for daz,ftz,word in product((0,1),(0,1),range(4) if rounding=='SR' else (0,)):
            result += [dict(row,rounding_sel=rnd,daz_in_sel=daz,ftz_out_sel=ftz,sr_rnd=word) for row in operands]
    return result


def references(spec,g,rows):
    ab,c=parse_format(g['format_ab']),parse_format(g['format_c'])
    layout=D.dot_layout(spec);outputs=layout['core_out'];unit=Fraction(2)**g['frame_lsb'];mask=(1<<g['width'])-1
    expected=[];acc=[];valid=[];shifts=[];positive_or=0
    for row in rows:
        ctrl={key:spec[key][row[key+'_sel']] for key in D.DOT_RUNTIME}
        expected.append(pack_ports(D.dot_outputs(spec,layout,0,row['a'],row['b'],row['c'],ctrl,[row['sr_rnd']]),outputs))
        a=[v for v,_,_ in D._values_of(ab,row['a'],2,ctrl['daz_in'])]
        b=[v for v,_,_ in D._values_of(ab,row['b'],2,ctrl['daz_in'])]
        cc=D._decode(c,row['c'],ctrl['daz_in'])[0]
        finite=all(not isinstance(v,Special) for v in a+b+[cc]);valid.append(int(finite))
        if not finite:acc.append(0);shifts.append(0);continue
        value=(sum(x*y for x,y in zip(a,b))+cc)/unit
        assert value.denominator==1 and -(1<<(g['width']-1))<=value<(1<<(g['width']-1))
        value=int(value);acc.append(value&mask);shifts.append(g['width']-abs(value).bit_length() if value else 0)
        if value>0:positive_or|=value
    assert positive_or==(1<<(g['width']-1))-1,'geometry only exercises padding or sign extension'
    assert g['width']-1 in shifts and 1 in shifts,'word endpoints never reach the normalizer'
    return expected,acc,valid,shifts


def bench(spec,g,own,rows,directory):
    directory.mkdir(parents=True,exist_ok=True);layout=D.dot_layout(spec);ins,outs=layout['core_in'],layout['core_out']
    expected,acc,valid,shifts=references(spec,g,rows);width=g['width']
    tb_gen.write_hex(directory/'vectors.hex',[pack_ports(row,ins) for row in rows],sum(p.width for p in ins))
    tb_gen.write_hex(directory/'expected.hex',expected,sum(p.width for p in outs))
    tb_gen.write_hex(directory/'acc_expected.hex',acc,width);tb_gen.write_hex(directory/'acc_valid.hex',valid,1)
    tb_gen.write_hex(directory/'shift_expected.hex',shifts,width.bit_length()+1)
    text=tb_gen.emit_tb('dot_core',ins+outs,len(rows),expected_file='expected.hex')
    word='sumk' if own['organization']!='monolithic' else 'sum_sum' if own['carry_resolution']=='carry_save_deferred' else 'sum_c1'
    scope='dut.u_m0_dot0'
    decl=f'  integer accumulator_fd, shift_fd;\n  reg [{width-1}:0] expected_acc [0:N-1];\n  reg valid_acc [0:N-1];\n  integer expected_shift [0:N-1];\n'
    text=text.replace('  initial begin',decl+'  initial begin',1)
    text=text.replace('    errors = 0;','    errors = 0;\n    accumulator_fd=$fopen("acc_actual.hex","w"); shift_fd=$fopen("shifts.txt","w");\n'
                      '    $readmemh("acc_expected.hex",expected_acc); $readmemh("acc_valid.hex",valid_acc); $readmemh("shift_expected.hex",expected_shift);',1)
    probe=f'''      $fdisplay(accumulator_fd,"%h",{scope}.{word});
      $fdisplay(shift_fd,"%0d",{scope}.o_lz);
      if (valid_acc[i] && {scope}.{word} !== expected_acc[i]) begin errors=errors+1; if(errors<8) $display("ACCUMULATOR MISMATCH %0d",i); end
      if (valid_acc[i] && {scope}.o_lz !== expected_shift[i]) begin errors=errors+1; if(errors<8) $display("NORMALIZER MISMATCH %0d",i); end
'''
    text=text.replace('      #1;','      #1;\n'+probe,1)
    text=text.replace('    $fclose(fd);','    $fclose(fd); $fclose(accumulator_fd); $fclose(shift_fd);',1)
    return text,word


def check(root,index,own,n_random):
    spec,g=fixture(own['accumulator_width_bits']);rows=vectors(spec,g,n_random);d=root/str(index);tb,word=bench(spec,g,own,rows,d)
    with Audit() as audit:source=seed_for(spec,family=(FAMILY,dict(own,**CHILDREN)))
    text=str(source);(d/'seed.sv').write_text(text);(d/'freeze.json').write_text(json.dumps(dict(spec=spec,geometry=g,n_vectors=len(rows)),indent=2)+'\n')
    start=time.monotonic();status=run_case('',d.name,tb,root,text);elapsed=time.monotonic()-start
    result=dict(index=index,family=FAMILY,pins=own,child_pins=CHILDREN,geometry=g,vectors=len(rows),pass_=status.endswith(': PASS'),
                detail=status,elapsed=elapsed,source_bytes=len(text),source_sha256=hashlib.sha256(text.encode()).hexdigest(),fidelity=audit.report())
    (d/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['pass_'] and (d/'lib.sv').exists(),result
    assert re.search(rf'logic \[{g["width"]-1}:0\] {word};',text)
    instances=hierarchy_of_files(['tb.sv','lib.sv'],d,'tb')
    normal=[r for r in instances if r['module']=='fam_shift_barrel_mux_tree' and r['parameters'].get('W')==g['width']]
    assert normal and all(r['parameters']['RADIX_LOG2']==2 for r in normal)
    actual=[int(x,16) for x in (d/'acc_actual.hex').read_text().split()];expect=[int(x,16) for x in (d/'acc_expected.hex').read_text().split()];valid=[int(x,16) for x in (d/'acc_valid.hex').read_text().split()]
    assert len(actual)==len(expect)==len(rows) and all(a==e for a,e,v in zip(actual,expect,valid) if v)
    covered=0
    for a,v in zip(actual,valid):
        if v and a<(1<<(g['width']-1)):covered|=a
    assert covered==(1<<(g['width']-1))-1
    result['positive_magnitude_bits_exercised']=g['width']-1
    result['normalization_shifts']=sorted({int(s) for s,v in zip((d/'shifts.txt').read_text().split(),valid) if v})
    result['actual_word']=word
    result['artifacts']={name:hashlib.sha256((d/name).read_bytes()).hexdigest() for name in ('seed.sv','lib.sv','tb.sv','vectors.hex','expected.hex','dump.hex','acc_expected.hex','acc_actual.hex','acc_valid.hex','shift_expected.hex','shifts.txt')}
    (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out');p.add_argument('--width',type=int)
    p.add_argument('--organization');p.add_argument('--carry');p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int)
    p.add_argument('--vectors',type=int,default=96)
    p.add_argument('--full',action='store_true',help='every width of the declared Range (1064 cases), not the representative ones')
    args=p.parse_args();root=Path(args.out or tempfile.mkdtemp(prefix='chialu-dot-kulisch-'));root.mkdir(parents=True,exist_ok=True)
    result=[]
    for index,(_,own) in enumerate(cases(args.full)):
        if index<args.start or args.stop is not None and index>=args.stop:continue
        if args.width and own['accumulator_width_bits']!=args.width:continue
        if args.organization and own['organization']!=args.organization:continue
        if args.carry and own['carry_resolution']!=args.carry:continue
        row=check(root,index,own,args.vectors);result.append(row);(root/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(index,own,'PASS',row['vectors'],round(row['elapsed'],2),row['source_bytes'],flush=True)
    print('PASS',len(result),'cases',sum(r['vectors'] for r in result),'vectors',flush=True)


if __name__=='__main__':main()
