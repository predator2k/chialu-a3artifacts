# multiprecision_block_proposal: proposed changes to the space

* native-mode choice `{1x27, 2x18, 4x9, 8x4}` and a choice distinguishing fractured arrays from added standalone multipliers, plus a MAC result-grouping choice — the enhanced block selects among these to hold area and the 72 output ports [boutros_2018]
* `fracture_to` values 6, 12 and 24 with separate chopping factors and recursive decomposition depth — the PIR-DSP line partitions 27x18 into six 9x9 tiles and recurses to twelve 4x4 or twenty-four 2x2 lanes [rasoulinezhad_2019, dai_2021]
* `multiplier` slot value for a Baugh-Wooley array with a Dadda tree — no existing multiplier family names that combination [boutros_2018]
* choices for dedicated data reuse (FIFO/register file, chain forwarding distance of one or two blocks, semi-2D systolic interconnect) — the convolution-oriented proposals add local storage and inter-block paths [boutros_2021, rasoulinezhad_2019, dai_2021]
* per-operand runtime signedness control — each PIR-DSP operand can be signed or unsigned at run time [rasoulinezhad_2019]
* choice for exact versus approximate multiplier tiles — APIR-DSP replaces all six 9x9 tiles with approximate ones [dai_2021]
