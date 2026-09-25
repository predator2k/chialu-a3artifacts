# mx_microscaling_dot

A block of k elements shares one scale factor, so each value is X times
a narrow element P_i in fp8, fp6, fp4 or int8, and the dot product
multiplies element mantissas, reduces each block in its own tree,
normalizes the block results to the largest block exponent,
accumulates them in fixed point, converts to fp32 and accumulates in
fp32. The OCP form fixes k = 32 with an 8-bit power-of-two scale
(E8M0); the two-level form uses blocks of 16 under an 8-bit exponent
and two-element sub-blocks under a 1-bit microexponent that
conditionally right-shifts the pair inside the adder tree. Inputs are
quantized along the reduction dimension, and outputs and vector
operations stay scalar bf16 or fp32.

The block size and scale encoding set fidelity per stored bit: the
proven bound is QSNR >= 6.02m + 10 log(2^(2 beta)/(min(N, k1) +
(2^(2 beta) - 1) k2)) for beta = 2^d2 - 1, so shrinking the sub-block
to two elements under a single microexponent bit buys most of the
fidelity at a few percent of cost, whereas a second microexponent bit
buys little for a large cost increase. The element type is the
accuracy/area knob: the 9-bit two-level format sits about 16 dB above
an FP8 E4M3 dot product in QSNR and trains a 1.5B-parameter model to
the FP32 loss, the 6-bit format costs about 2x and the 4-bit format 4x
less area-memory than a configurable FP8 E4M3/E5M2 dot product on a
leading-edge node, and MXFP6 with 6-bit weights, activations and
gradients trains GPT models with FP32 hyperparameters unchanged
(2.75 against 2.74 loss at 1.5B parameters). MXINT8 direct-cast
inference matches FP32 within the reported deviation, and MXFP6 may
need quantization-aware fine-tuning. The accumulate precision decides
whether dot-product outputs return in bf16 or fp32; the multiplier and
reduction slots are the element multiplier and the per-block tree.

The accuracy contract is model-level rather than a ulp bound: no
arithmetic error bound and no checker are reported, and the QSNR bound
is the only analytical guarantee. Conversion to MX rounds half to
nearest even for inference and half away from zero for training, the
conversion recipe may be implementation-defined, and quantization does
not commute with transposition, so a weight and its transpose need
separate MX tensors. Execution is feed-forward.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: for a block format_ab mode, the element products under the block's scale into the wide sum through the `reduction` tree (the scale encoding and element type are the mode's format); a scalar mode keeps the behavioral path). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## references

rouhani_2023a -> B. Darvish Rouhani, R. Zhao, V. Elango, et al., "With Shared Microexponents, A Little Shifting Goes a Long Way", ISCA, 2023
rouhani_2023b -> B. Darvish Rouhani, R. Zhao, A. More, M. Hall, et al., "Microscaling Data Formats for Deep Learning", arXiv:2310.10537, 2023
