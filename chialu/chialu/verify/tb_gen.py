"""Interface-driven SV testbench emission (microarchitecture-blind).

The generator sees ports, an execution contract, and file names —
never the DUT's internals. Three timing protocols cover the unit
classes including iterative SFUs:

  comb            latency_cycles == 0: apply, settle, sample
  fixed latency   latency_cycles == L > 0: clocked, one vector at a
                  time, sampled L cycles after application (frozen
                  port convention: clk, rst_n)
  variable        variable_latency_max == V > 0: handshake convention
                  in_valid/out_valid; a response later than V cycles
                  is a protocol failure (line 'TIMEOUT' in the dump)

Vector file: one hex line per vector — the concatenation of INPUT
ports in declared order, first port in the most significant bits.
Dump file: one hex line per vector — OUTPUT ports concatenated the
same way. Self-check mode also reads expected.hex and counts
mismatches in simulation (usable only for bit-exact gates); dump mode
leaves all judgment to the host-side error model.
"""

from __future__ import annotations


def _cat(ports, kind):
    sel = [p for p in ports if p.direction == kind]
    return sel, sum(p.width for p in sel)


def _slice_decls(sel, bus):
    out, hi = [], sum(p.width for p in sel)
    for p in sel:
        out.append(f"  wire [{p.width - 1}:0] {p.name} = "
                   f"{bus}[{hi - 1}:{hi - p.width}];")
        hi -= p.width
    return out


def emit_tb(dut_name, ports, n_vectors, latency=0, var_latency=0,
            vectors_file="vectors.hex", dump_file="dump.hex",
            expected_file=None, timescale="1ns/1ps", tb_driven=(),
            preload=None):
    """tb_driven names input ports the testbench drives itself rather
    than from the vector file (a table-load interface: clk, tbl_we,
    tbl_addr, tbl_data); preload lists (we_mask, addr, data) writes
    applied on posedge clk before the vectors."""
    ins, in_w = _cat([p for p in ports if p.name not in tb_driven], "in")
    outs, out_w = _cat(ports, "out")
    driven = [p for p in ports if p.direction == "in" and p.name in tb_driven]
    clocked = latency > 0 or var_latency > 0
    sc = expected_file is not None
    L = []
    L.append(f"`timescale {timescale}")
    L.append("module tb;")
    L.append(f"  localparam N = {n_vectors};")
    L.append(f"  reg [{in_w - 1}:0] vec [0:N-1];")
    if sc:
        L.append(f"  reg [{out_w - 1}:0] exp [0:N-1];")
    L.append(f"  reg [{in_w - 1}:0] cur;")
    L += _slice_decls(ins, "cur")
    for p in driven:
        if p.name != "clk":
            L.append(f"  reg [{p.width - 1}:0] {p.name} = 0;")
    for p in outs:
        L.append(f"  wire [{p.width - 1}:0] {p.name};")
    tbl_clk = any(p.name == "clk" for p in driven)
    if clocked or tbl_clk:
        L.append("  reg clk = 0;" + (" reg rst_n = 0;" if clocked else ""))
        L.append("  always #5 clk = ~clk;")
    if var_latency:
        L.append("  reg in_valid = 0; wire out_valid;")
    conns = ", ".join(f".{p.name}({p.name})" for p in ports)
    extra = ""
    if clocked:
        extra += ", .clk(clk), .rst_n(rst_n)"
    if var_latency:
        extra += ", .in_valid(in_valid), .out_valid(out_valid)"
    L.append(f"  {dut_name} dut ({conns}{extra});")
    L.append("  integer i, fd, errors, waited;")
    L.append("  initial begin")
    L.append(f'    $readmemh("{vectors_file}", vec);')
    if sc:
        L.append(f'    $readmemh("{expected_file}", exp);')
    L.append(f'    fd = $fopen("{dump_file}", "w");')
    L.append("    errors = 0;")
    if clocked:
        L.append("    repeat (2) @(posedge clk); rst_n = 1;")
    for we, addr, data in (preload or []):
        L.append(f"    @(negedge clk); tbl_we = {we}; tbl_addr = {addr}; tbl_data = {data};")
    if preload:
        L.append("    @(negedge clk); tbl_we = 0;")
    L.append("    for (i = 0; i < N; i = i + 1) begin")
    L.append("      cur = vec[i];")
    if var_latency:
        L.append("      @(negedge clk); in_valid = 1;")
        L.append("      @(negedge clk); in_valid = 0;")
        L.append("      waited = 0;")
        L.append(f"      while (!out_valid && waited < {var_latency + 2}) "
                 "begin @(posedge clk); waited = waited + 1; end")
        L.append("      if (!out_valid) begin")
        L.append('        $fdisplay(fd, "TIMEOUT"); errors = errors + 1;')
        L.append("      end else begin")
        pad = "  "
    elif clocked:
        L.append("      @(negedge clk);")
        L.append(f"      repeat ({latency}) @(posedge clk);")
        L.append("      #1;")
        pad = ""
    else:
        L.append("      #1;")
        pad = ""
    cat_out = "{" + ", ".join(p.name for p in outs) + "}"
    L.append(f'      {pad}$fdisplay(fd, "%h", {cat_out});')
    if sc:
        L.append(f"      {pad}if ({cat_out} !== exp[i]) begin")
        L.append(f"        {pad}errors = errors + 1;")
        L.append(f'        {pad}if (errors <= 20) $display('
                 f'"MISMATCH i=%0d in=%h got=%h expect=%h", '
                 f"i, cur, {cat_out}, exp[i]);")
        L.append(f"      {pad}end")
    if var_latency:
        L.append("      end")
    L.append("    end")
    L.append("    $fclose(fd);")
    if sc:
        L.append('    if (errors == 0) $display("CONFORMANCE PASS %0d/%0d",'
                 " N, N);")
        L.append('    else $display("CONFORMANCE FAIL %0d of %0d", '
                 "errors, N);")
    else:
        L.append('    $display("DUMP DONE %0d", N);')
    L.append("    $finish;")
    L.append("  end")
    L.append("endmodule")
    return "\n".join(L) + "\n"


def emit_fault_tb(core_name, checker_name, ports, n_vectors, n_masks,
                  data_out="y", check_out="check_err",
                  vectors_file="vectors.hex", masks_file="masks.hex",
                  dump_file="fault_dump.hex", timescale="1ns/1ps",
                  core_ins=None, chk_ins=None, chk_outs=None):
    """Wrapper harness owning the core/checker seam: the core's data
    output is XORed with a mask before the checker observes it. The
    checker sees the module inputs plus the (possibly corrupted) data
    output — never core internals. Dump: one line per (mask, vector):
    {check_err, y_injected}. `ports` lists every input of the harness
    (the vector file's fields) and the core's outputs; core_ins /
    chk_ins name the inputs each module takes (default: all), chk_outs
    the core outputs the checker also reads (default: none but the data
    output), wired through uncorrupted."""
    ins, in_w = _cat(ports, "in")
    outs = [p for p in ports if p.direction == "out"
            and p.name not in (check_out,)]
    y = next(p for p in outs if p.name == data_out)
    core_ins = ins if core_ins is None else [p for p in ins if p.name in core_ins]
    chk_ins = ins if chk_ins is None else [p for p in ins if p.name in chk_ins]
    chk_outs = [p for p in outs if p.name in (chk_outs or ()) and p.name != data_out]
    L = [f"`timescale {timescale}", "module tb;"]
    L.append(f"  localparam N = {n_vectors};")
    L.append(f"  localparam M = {n_masks};")
    L.append(f"  reg [{in_w - 1}:0] vec [0:N-1];")
    L.append(f"  reg [{y.width - 1}:0] msk [0:M-1];")
    L.append(f"  reg [{in_w - 1}:0] cur;")
    L += _slice_decls(ins, "cur")
    L.append(f"  wire [{y.width - 1}:0] y_core;")
    L.append(f"  reg  [{y.width - 1}:0] mask;")
    L.append(f"  wire [{y.width - 1}:0] y_inj = y_core ^ mask;")
    for p in outs:
        if p.name != data_out:
            L.append(f"  wire [{p.width - 1}:0] {p.name}_core;")
    L.append("  wire alarm;")
    core_conns = ", ".join(f".{p.name}({p.name})" for p in core_ins)
    other = "".join(f", .{p.name}({p.name}_core)" for p in outs if p.name != data_out)
    L.append(f"  {core_name} core ({core_conns}, .{data_out}(y_core){other});")
    chk_conns = ", ".join(f".{p.name}({p.name})" for p in chk_ins)
    thru = "".join(f", .{p.name}({p.name}_core)" for p in chk_outs)
    L.append(f"  {checker_name} chk_i ({chk_conns}, "
             f".{data_out}(y_inj){thru}, .{check_out}(alarm));")
    L.append("  integer i, m, fd;")
    L.append("  initial begin")
    L.append(f'    $readmemh("{vectors_file}", vec);')
    L.append(f'    $readmemh("{masks_file}", msk);')
    L.append(f'    fd = $fopen("{dump_file}", "w");')
    L.append("    for (m = 0; m < M; m = m + 1) begin")
    L.append("      mask = msk[m];")
    L.append("      i = m % N; cur = vec[i]; #1;")
    L.append('      $fdisplay(fd, "%h", {alarm, y_inj});')
    L.append("    end")
    L.append("    $fclose(fd);")
    L.append('    $display("FAULT DUMP DONE %0d", M);')
    L.append("    $finish;")
    L.append("  end")
    L.append("endmodule")
    return "\n".join(L) + "\n"


def emit_fault_tb_sites(core_name, checker_name, ports, n_vectors, rows, sites,
                        data_out="y", check_out="check_err", vectors_file="vectors.hex",
                        plan_file="fault_plan.hex", dump_file="fault_sites_dump.hex",
                        timescale="1ns/1ps", core_ins=None, chk_ins=None, chk_outs=None):
    """The grouped fault harness (docs/checker-spec-plan.md): one row per
    fault names its vector and its site. Site 0 XORs the mask on the
    core's data output (the seam); site k forces the internal net
    sites[k] = (path under the core instance, width, bit) to its
    fault-free value with that bit flipped while the vector is applied,
    and releases it after the dump. The dump is {check_err, y} per row,
    y the corrupted data output the checker saw, so the host compares y
    with the golden word to tell a masked corruption from a fault."""
    ins, in_w = _cat(ports, "in")
    outs = [p for p in ports if p.direction == "out" and p.name not in (check_out,)]
    y = next(p for p in outs if p.name == data_out)
    core_ins = ins if core_ins is None else [p for p in ins if p.name in core_ins]
    chk_ins = ins if chk_ins is None else [p for p in ins if p.name in chk_ins]
    chk_outs = [p for p in outs if p.name in (chk_outs or ()) and p.name != data_out]
    n_sites = max(1, len(sites))
    sw = max(1, (n_sites - 1).bit_length())
    vw = max(1, (max(1, n_vectors) - 1).bit_length())
    pw = sw + vw + y.width
    wmax = max([w for _p, w, _b in sites[1:]] + [1])
    L = [f"`timescale {timescale}", "module tb;"]
    L.append(f"  localparam N = {n_vectors};")
    L.append(f"  localparam M = {len(rows)};")
    L.append(f"  reg [{in_w - 1}:0] vec [0:N-1];")
    L.append(f"  reg [{pw - 1}:0] pln [0:M-1];")
    L.append(f"  reg [{in_w - 1}:0] cur;")
    L += _slice_decls(ins, "cur")
    L.append(f"  wire [{y.width - 1}:0] y_core;")
    L.append(f"  reg  [{y.width - 1}:0] mask;")
    L.append(f"  reg  [{sw - 1}:0] site;")
    L.append(f"  reg  [{vw - 1}:0] vidx;")
    L.append(f"  reg  [{wmax - 1}:0] ftmp;")
    L.append(f"  wire [{y.width - 1}:0] y_inj = y_core ^ mask;")
    for p in outs:
        if p.name != data_out:
            L.append(f"  wire [{p.width - 1}:0] {p.name}_core;")
    L.append("  wire alarm;")
    core_conns = ", ".join(f".{p.name}({p.name})" for p in core_ins)
    other = "".join(f", .{p.name}({p.name}_core)" for p in outs if p.name != data_out)
    L.append(f"  {core_name} core ({core_conns}, .{data_out}(y_core){other});")
    chk_conns = ", ".join(f".{p.name}({p.name})" for p in chk_ins)
    thru = "".join(f", .{p.name}({p.name}_core)" for p in chk_outs)
    L.append(f"  {checker_name} chk_i ({chk_conns}, .{data_out}(y_inj){thru}, .{check_out}(alarm));")
    L.append("  task inject(input integer s);")
    L.append("    case (s)")
    for k, (path, w, bit) in enumerate(sites):
        if k == 0:
            continue
        L.append(f"      {k}: begin ftmp[{w - 1}:0] = {path}; force {path} = ftmp[{w - 1}:0] ^ {w}'h{1 << bit:x}; end")
    L.append("      default: ;")
    L.append("    endcase")
    L.append("  endtask")
    L.append("  task restore(input integer s);")
    L.append("    case (s)")
    for k, (path, w, bit) in enumerate(sites):
        if k == 0:
            continue
        L.append(f"      {k}: release {path};")
    L.append("      default: ;")
    L.append("    endcase")
    L.append("  endtask")
    L.append("  integer m, fd;")
    L.append("  initial begin")
    L.append(f'    $readmemh("{vectors_file}", vec);')
    L.append(f'    $readmemh("{plan_file}", pln);')
    L.append(f'    fd = $fopen("{dump_file}", "w");')
    L.append("    for (m = 0; m < M; m = m + 1) begin")
    L.append(f"      {{site, vidx, mask}} = pln[m];")
    L.append("      cur = vec[vidx]; #1;")
    L.append("      if (site != 0) begin inject(site); #1; end")
    L.append('      $fdisplay(fd, "%h", {alarm, y_inj});')
    L.append("      if (site != 0) begin restore(site); #1; end")
    L.append("    end")
    L.append("    $fclose(fd);")
    L.append('    $display("FAULT DUMP DONE %0d", M);')
    L.append("    $finish;")
    L.append("  end")
    L.append("endmodule")
    return "\n".join(L) + "\n"


def plan_words(rows, sites, n_vectors, y_width) -> tuple:
    """(words, width) of fault_plan.hex: {site, vector, mask} per row."""
    n_sites = max(1, len(sites))
    sw = max(1, (n_sites - 1).bit_length())
    vw = max(1, (max(1, n_vectors) - 1).bit_length())
    words = [(r["site"] << (vw + y_width)) | (r["vector"] << y_width) | r["mask"] for r in rows]
    return words, sw + vw + y_width


CAMPAIGNS = {"conformance": 0, "seam": 1, "sites": 2}


def emit_tb_universal(core_name, ports, max_vectors, checker_name=None, max_rows=0, nets=(),
                      data_out="y", check_out="check_err", core_ins=None, chk_ins=None, chk_outs=None,
                      timescale="1ns/1ps"):
    """One testbench per candidate design, built once and run per
    campaign (docs/checker-spec-plan.md, "The fault campaign"): the
    plusargs select the campaign and name its files, so the compiled
    model serves the conformance vectors, the seam fault masks and the
    grouped internal-fault plan without a rebuild.

      +campaign=0 +vectors=F [+expected=F] +n=N +dump=F      the conformance run of emit_tb
      +campaign=1 +vectors=F +masks=F +n=N +m=M +dump=F      the seam masks of emit_fault_tb (mask k on vector k mod N)
      +campaign=2 +vectors=F +plan=F +n=N +m=M +dump=F       the grouped plan: rows {net, bit, vector, mask}

    `nets` lists (path under the core instance, width) of the internal
    sites; a plan row's `net` indexes it (0 is the seam) and `bit` the
    flipped bit, so the site table is fixed at build time and the plan
    chooses among its nets at run time. The dump formats are emit_tb's
    and emit_fault_tb's."""
    ins, _all_w = _cat(ports, "in")
    outs = [p for p in ports if p.direction == "out" and p.name != check_out]
    out_w = sum(p.width for p in outs)
    y = next((p for p in outs if p.name == data_out), None)
    checked = checker_name is not None and y is not None
    core_ins = ins if core_ins is None else [p for p in ins if p.name in core_ins]
    chk_ins = ins if chk_ins is None else [p for p in ins if p.name in chk_ins]
    chk_outs = [p for p in outs if p.name in (chk_outs or ()) and p.name != data_out]
    # the vector word packs the core's inputs (vectors.hex is the conformance packing); an input only the
    # checker reads (check_sr_sel) is held at zero
    fed = core_ins
    in_w = sum(p.width for p in fed)
    extra_ins = [p for p in ins if p not in fed]
    nets = list(nets)
    nw = max(1, len(nets).bit_length())
    bw = max(1, (max([w for _p, w in nets] + [1]) - 1).bit_length())
    vw = max(1, (max(1, max_vectors) - 1).bit_length())
    y_w = y.width if y is not None else 1
    pw = nw + bw + vw + y_w
    wmax = max([w for _p, w in nets] + [1])
    L = [f"`timescale {timescale}", "module tb;"]
    L.append(f"  localparam MAXN = {max(1, max_vectors)};")
    L.append(f"  localparam MAXM = {max(1, max_rows)};")
    L.append(f"  reg [{in_w - 1}:0] vec [0:MAXN-1];")
    L.append(f"  reg [{out_w - 1}:0] exp [0:MAXN-1];")
    L.append(f"  reg [{in_w - 1}:0] cur;")
    L += _slice_decls(fed, "cur")
    for p in extra_ins:
        L.append(f"  reg [{p.width - 1}:0] {p.name} = 0;")
    for p in outs:
        L.append(f"  wire [{p.width - 1}:0] {p.name}_core;")
    L.append(f"  reg  [{y_w - 1}:0] mask;")
    if checked:
        L.append(f"  reg [{y_w - 1}:0] msk [0:MAXM-1];")
        L.append(f"  reg [{pw - 1}:0] pln [0:MAXM-1];")
        L.append(f"  wire [{y_w - 1}:0] y_inj = {data_out}_core ^ mask;")
        L.append(f"  reg  [{wmax - 1}:0] ftmp;")
        L.append(f"  reg  [{nw - 1}:0] net;")
        L.append(f"  reg  [{bw - 1}:0] fbit;")
        L.append(f"  reg  [{vw - 1}:0] vidx;")
        L.append("  wire alarm;")
    core_conns = ", ".join(f".{p.name}({p.name})" for p in core_ins)
    core_outs = "".join(f", .{p.name}({p.name}_core)" for p in outs)
    L.append(f"  {core_name} core ({core_conns}{core_outs});")
    if checked:
        chk_conns = ", ".join(f".{p.name}({p.name})" for p in chk_ins)
        thru = "".join(f", .{p.name}({p.name}_core)" for p in chk_outs)
        L.append(f"  {checker_name} chk_i ({chk_conns}, .{data_out}(y_inj){thru}, .{check_out}(alarm));")
        L.append("  task inject(input integer s, input integer b);")
        L.append("    case (s)")
        for k, (path, w) in enumerate(nets, 1):
            L.append(f"      {k}: begin ftmp[{w - 1}:0] = {path}; force {path} = ftmp[{w - 1}:0] ^ ({w}'d1 << b); end")
        L.append("      default: ;")
        L.append("    endcase")
        L.append("  endtask")
        L.append("  task restore(input integer s);")
        L.append("    case (s)")
        for k, (path, _w) in enumerate(nets, 1):
            L.append(f"      {k}: release {path};")
        L.append("      default: ;")
        L.append("    endcase")
        L.append("  endtask")
    L.append("  integer i, k, n, m, fd, errors, campaign, sc;")
    L.append("  string vfile, efile, mfile, pfile, dfile;")
    cat_out = "{" + ", ".join(f"{p.name}_core" for p in outs) + "}"
    L.append("  initial begin")
    L.append('    if (!$value$plusargs("campaign=%d", campaign)) campaign = 0;')
    L.append('    if (!$value$plusargs("vectors=%s", vfile)) vfile = "vectors.hex";')
    L.append('    if (!$value$plusargs("n=%d", n)) n = MAXN;')
    L.append('    if (!$value$plusargs("m=%d", m)) m = MAXM;')
    L.append('    sc = $value$plusargs("expected=%s", efile);')
    L.append('    if (!$value$plusargs("masks=%s", mfile)) mfile = "masks.hex";')
    L.append('    if (!$value$plusargs("plan=%s", pfile)) pfile = "fault_plan.hex";')
    L.append('    if (!$value$plusargs("dump=%s", dfile)) dfile = (campaign == 0) ? "dump.hex" : (campaign == 1) ? "fault_dump.hex" : "fault_sites_dump.hex";')
    L.append("    $readmemh(vfile, vec);")
    L.append("    if (sc) $readmemh(efile, exp);")
    L.append('    fd = $fopen(dfile, "w");')
    L.append("    errors = 0; mask = 0;")
    L.append("    if (campaign == 0) begin")
    L.append("      for (i = 0; i < n; i = i + 1) begin")
    L.append("        cur = vec[i]; #1;")
    L.append(f'        $fdisplay(fd, "%h", {cat_out});')
    L.append(f"        if (sc && {cat_out} !== exp[i]) begin")
    L.append("          errors = errors + 1;")
    L.append(f'          if (errors <= 20) $display("MISMATCH i=%0d in=%h got=%h expect=%h", i, cur, {cat_out}, exp[i]);')
    L.append("        end")
    L.append("      end")
    L.append("      $fclose(fd);")
    L.append('      if (sc && errors == 0) $display("CONFORMANCE PASS %0d/%0d", n, n);')
    L.append('      else if (sc) $display("CONFORMANCE FAIL %0d of %0d", errors, n);')
    L.append('      else $display("DUMP DONE %0d", n);')
    L.append("    end")
    if checked:
        L.append("    else if (campaign == 1) begin")
        L.append("      $readmemh(mfile, msk);")
        L.append("      for (k = 0; k < m; k = k + 1) begin")
        L.append("        mask = msk[k]; i = k % n; cur = vec[i]; #1;")
        L.append('        $fdisplay(fd, "%h", {alarm, y_inj});')
        L.append("      end")
        L.append("      $fclose(fd);")
        L.append('      $display("FAULT DUMP DONE %0d", m);')
        L.append("    end")
        L.append("    else begin")
        L.append("      $readmemh(pfile, pln);")
        L.append("      for (k = 0; k < m; k = k + 1) begin")
        L.append("        {net, fbit, vidx, mask} = pln[k];")
        L.append("        cur = vec[vidx]; #1;")
        L.append("        if (net != 0) begin inject(net, fbit); #1; end")
        L.append('        $fdisplay(fd, "%h", {alarm, y_inj});')
        L.append("        if (net != 0) begin restore(net); #1; end")
        L.append("      end")
        L.append("      $fclose(fd);")
        L.append('      $display("FAULT DUMP DONE %0d", m);')
        L.append("    end")
    else:
        L.append('    else begin $fclose(fd); $display("NO CHECKER for campaign %0d", campaign); end')
    L.append("    $finish;")
    L.append("  end")
    L.append("endmodule")
    return "\n".join(L) + "\n"


def plan_words_universal(rows, nets, sites, n_vectors, y_width) -> tuple:
    """(words, width) of a grouped plan for emit_tb_universal: each row's
    site (an index into `sites` = (path, width, bit)) becomes the index of
    its net in `nets` and the bit; site 0 is the seam."""
    index = {path: k for k, (path, _w) in enumerate(nets, 1)}
    nw = max(1, len(nets).bit_length())
    bw = max(1, (max([w for _p, w in nets] + [1]) - 1).bit_length())
    vw = max(1, (max(1, n_vectors) - 1).bit_length())
    words = []
    for r in rows:
        if r["site"] == 0:
            net, bit = 0, 0
        else:
            path, _w, bit = sites[r["site"]]
            net = index[path]
        words.append((((net << bw | bit) << vw | r["vector"]) << y_width) | r["mask"])
    return words, nw + bw + vw + y_width


def emit_stub(dut_name, ports, assigns=None, clocked=False,
              var_latency=False):
    """Behavioral stub for harness smoke tests: outputs default to 0,
    `assigns` overrides per port name with an SV expression."""
    ins = [p for p in ports if p.direction == "in"]
    outs = [p for p in ports if p.direction == "out"]
    decl = [f"  input wire [{p.width - 1}:0] {p.name}" for p in ins]
    decl += [f"  output wire [{p.width - 1}:0] {p.name}" for p in outs]
    if clocked:
        decl = ["  input wire clk", "  input wire rst_n"] + decl
    if var_latency:
        decl += ["  input wire in_valid", "  output wire out_valid"]
    L = [f"module {dut_name} (", ",\n".join(decl), ");"]
    for p in outs:
        expr = (assigns or {}).get(p.name, f"{p.width}'d0")
        L.append(f"  assign {p.name} = {expr};")
    if var_latency:
        L.append("  reg [3:0] cnt = 0;")
        L.append("  always @(posedge clk) if (!rst_n) cnt <= 0;")
        L.append("    else if (in_valid) cnt <= 1;")
        L.append("    else if (cnt != 0 && cnt < 3) cnt <= cnt + 1;")
        L.append("    else cnt <= 0;")
        L.append("  assign out_valid = (cnt == 3);")
    L.append("endmodule")
    return "\n".join(L) + "\n"


def write_hex(path, values, width):
    digits = (width + 3) // 4
    with open(path, "w") as f:
        for v in values:
            f.write(f"{v & ((1 << width) - 1):0{digits}x}\n")
