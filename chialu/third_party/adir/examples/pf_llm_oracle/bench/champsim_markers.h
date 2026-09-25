#ifndef CHAMPSIM_MARKERS_H
#define CHAMPSIM_MARKERS_H
/* Region of interest for the ChampSim pintool (-start_symbol / -stop_symbol). */
#ifdef __cplusplus
extern "C" {
#endif
__attribute__((noinline)) void __champsim_start_trace(void) { __asm__ volatile(""); }
__attribute__((noinline)) void __champsim_stop_trace(void) { __asm__ volatile(""); }
#ifdef __cplusplus
}
#endif
#endif
