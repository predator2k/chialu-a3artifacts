---
family: posit_adder_multiplier
pin: {internal_representation: sign_magnitude}
---
# sign_magnitude

The sign is split off and the datapath works on magnitudes: the
decoder either converts a negative input to its absolute value by
two's complement and processes the sign separately, or bypasses the
conversion altogether by decoding the negative pattern's fields
directly with the sign held aside, and the encoder applies the
matching sign-separated conversion. Addition then orders the two
magnitudes, aligns the smaller and adds or subtracts.

Sign-magnitude is the pick for a multiplier-heavy datapath, where the
sign is one XOR and only the magnitudes enter the fraction
multiplier, and for a low-latency decoder, where dropping the
conversion shortens the path into an 8-bit training datapath. The
FloPoCo posit operators built this way cut area by up to 36 percent
and energy by up to 31 percent against the earlier generators in 65
nm. It costs a magnitude comparison and a subtract-then-negate in
the adder that a two's-complement intermediate avoids.

The library realizes this variant as the decoder that negates a negative pattern first (an incrementer over the inverted pattern) and decodes the magnitude with the sign carried separately, and as the encoder that rounds the magnitude to nearest even and negates the pattern last (`posit.decode_sv` and `posit.encode_sv`, `internal_representation: sign_magnitude`).

## references

jaiswal_2018 -> M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
murillo_2020 -> R. Murillo, A. A. Del Barrio, G. Botella, "Customized Posit Adders and Multipliers Using the FloPoCo Core Generator", IEEE International Symposium on Circuits and Systems (ISCAS), 2020
lu_2021 -> J. Lu, C. Fang, M. Xu, J. Lin, Z. Wang, "Evaluations on Deep Neural Networks Training Using Posit Number System", IEEE Transactions on Computers, 2021
