---
family: approximate_mac_nn
pin: {precision_scaling: dvafs}
---
# dvafs

Dynamic voltage-accuracy-frequency scaling: each CNN layer runs at a
separately profiled fixed-point precision for weights and input
feature maps, and the processor maps that precision onto subword
parallelism in the exact multiplier (up to 4 x 4 bit lanes per unit),
frequency and supply voltage, while also exploiting weight and input
sparsity. The multiplier stays exact; the approximation is the
per-layer word length.

It is the pick when the network must run unmodified, because 1 to 9
bit operation costs under 1% accuracy without retraining and the
selected settings keep 99% relative accuracy on LeNet-5 and AlexNet.
Its gain compounds three scalings: AlexNet reaches 1.8 TOPS/W on a
28 nm FDSOI processor against 0.16 TOPS/W for a non-scalable and 0.94
TOPS/W for a voltage-accuracy-only implementation. It loses to the
approximate-multiplier sources when the target precision is fixed
and the multiplier itself must shrink, since DVAFS keeps a full-width
exact unit.

## references

moons2017 -> B. Moons, R. Uytterhoeven, W. Dehaene, M. Verhelst, "DVAFS: Trading Computational Accuracy for Energy Through Dynamic-Voltage-Accuracy-Frequency-Scaling", Design, Automation and Test in Europe (DATE), pp. 488-493, 2017
