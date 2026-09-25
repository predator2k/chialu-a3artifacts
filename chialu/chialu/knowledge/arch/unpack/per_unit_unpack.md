# per_unit_unpack

Every arithmetic structure decodes its own operands: field split, exponent bias, hidden bit, zero, denormal, infinity and NaN detection. The generated seed's shape; the copies are identical logic on identical inputs, so synthesis merges what it can see.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the fields split, the specials decoded, the hidden one restored; denormal_handling in_unpack normalizes a subnormal).
The choice denormal_handling and the component families (lzc, shifter) select its sub-structures
from the library.

## design choices

### denormal_handling

| member | what it selects |
| --- | --- |
| `in_unpack` | a subnormal significand is normalized in the unpacker, through its leading-zero counter and shifter slots. |
| `in_datapath` | a subnormal significand is left as stored, so the datapath carries the unnormalized value. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the unpacker splits the fields, decodes the specials and restores the hidden one | - | `the fields split, the specials decoded, the hidden one restored` |

## references
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
