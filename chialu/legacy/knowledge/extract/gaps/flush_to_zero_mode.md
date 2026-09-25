# flush_to_zero_mode: proposed changes to the space

* runtime selection between IEEE handling and flush mode (optional_mode) [asprey_1993, eisen_2007]
* separate input flush (DAZ) and output flush (FTZ) enables [asprey_1993, kaul_2012]
* flag_policy — a flushed unit produces no underflow flags for the discarded values [langhammer_2015b]
* detection, prenormalization, result-generation and stall/trap policy choices shared with the sibling subnormal fillers [schwarz_2005]
