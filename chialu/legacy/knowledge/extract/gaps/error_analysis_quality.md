# error_analysis_quality: proposed changes to the space

* `metric` values `ned`/`nmed` selectable alongside `mred` and `er`, plus `ed`, `red` and a multi-metric selection, since the origin work and the surveys establish ED, MED, NED and RED jointly rather than one at a time [liang2013, ansari2018, zervakis2016, hashemi2016]
* `metric` values for the squared/spectral family `mse`, `rmse`, `snr`, `psnr`, `es` and `ares`, which the composition and application evaluations report separately [chan2013, jiang2020, mazahir2017a, mazahir2017b, scarabottolo2020]
* `metric` value `error_bias` (signed mean of M' - M, also called average error), which predicts accumulative-application quality [jiang2017, jiang2020, saadat2019]
* `metric` values `hd`, `ep`, `mae`, `mre` and `wcre` from the EvoApprox evaluation set, and `noeb` and `pred` (probability that RED stays below a threshold) from the compressor comparisons [mrazek2017, strollo2020, leon2018b]
* `metric` values `pass_rate`, `accamp` and `accinf` with a `data_semantics: {amplitude, information}` choice, and `oe`/`acc`/`ap` with an `acceptance_threshold` (minimum acceptance accuracy) [kahng_kang2012, lin2013, kyaw2010, zhu2010]
* `metric` value `wmed` (application-PMF-weighted mean error distance) and accuracy-power products `power_ned`, `npp` and `power_saving_per_ned` [mrazek2019, liang2013, chen2018]
* `model` values `sat_miter` (formal worst-case bound), `bdd` (exact distribution), `pseudo_boolean_sat` (worst-case optimization) and `sptm` (sequential probability-transition matrices) [ceska2017, venkatesan2011, liang2013]
* `model` values `statistical_hypothesis_testing`, `change_propagation_matrix`, `node_significance_propagation` and `partition_and_propagate` as scalable estimation methods, and `ann` for learned DFG error models [scarabottolo2020, zervakis2019]
* choice `input_distribution: {uniform, geometric, gaussian, arbitrary_pmf, application_trace}` and a `distribution_characterization` choice for standard-deviation-indexed lookup tables [mazahir2017b, chan2013, kahng_kang2012]
* choice `block_error_model: {single_error_value, conditional_error_pmf}` for the building-block abstraction in PMF composition [mazahir2017b]
* choice `timing_model_conversion: equivalent_untimed_circuit` so voltage-overscaled timing failures can be analyzed as Boolean error circuits, tied to the `add_voltage_overscaling_axis` mutation [venkatesan2011, zervakis2019]
* choices `normalization_reference: maximum_output_value`, `optimization_criterion: pairwise_fidelity`, `application_metric: {ssim, psnr, false_edges}` and `reference_evaluation: spice_accurate` for the exploration frameworks [vasicek2015, mrazek2019, leon2018b, zervakis2019]
