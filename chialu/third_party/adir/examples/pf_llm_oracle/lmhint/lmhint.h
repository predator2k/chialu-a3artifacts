/* LMHint: the L1D prefetcher ensemble steered by a per-load-PC hint.
 *
 * The hint table (PHT) lives in main memory and is produced offline --
 * in PF-LLM by a fine-tuned model, here by a program the search writes.
 * A small on-chip buffer (PHB) caches it. A reserved entry holds the
 * policy used while a buffer miss is served.
 *
 * Hint layout, 8 bits per PC, as in the paper:
 *     [7:4] selection  index into the ensemble; 0 = do not prefetch
 *     [3:2] degree     0 = unused, 1/2/3 = Q1 / median / Q3 of the
 *                      selected member's native degree range
 *     [1:0] filter     0 = none, 1..3 = index into the table's
 *                      three-entry filter-candidate list (two bits
 *                      cannot name one of twelve members, so the
 *                      packer emits the three most-filtered members
 *                      as a global side table)
 *
 * Everything here is configured at run time from the environment, so a
 * change of buffer size, ensemble or applied fields costs no rebuild:
 *     LMHINT_TABLE        path to the packed table
 *     LMHINT_ENSEMBLE     full | reduced
 *     LMHINT_FIELDS       SDF | SD | S
 *     LMHINT_PHB_ENTRIES  entries in the buffer
 *     LMHINT_DEFAULT      member name used while a buffer miss is served
 *     LMHINT_STATS        path for the json stats sidecar
 */
#ifndef PREFETCHER_LMHINT_H
#define PREFETCHER_LMHINT_H

#include <array>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

#include "address.h"
#include "champsim.h"
#include "modules.h"
#include "subprefetchers.h"

struct lmhint : public champsim::modules::prefetcher {
  using prefetcher::prefetcher;

  /* ---- the candidate's territory: router, multiplexer, orchestrator ---- */
  struct hint {
    uint8_t select{0};
    uint8_t degree{0};
    uint8_t filter{0};
    bool valid{false};
  };

  struct phb_entry {
    uint64_t pc{0};
    uint8_t raw{0};
    bool valid{false};
  };

  /* ---- fixed: the ensemble, the table and the buffer storage ---- */
  std::vector<std::unique_ptr<lmh::SubPF>> ensemble;
  std::vector<int> active;                     /* ensemble indices this build may select */
  std::unordered_map<uint64_t, uint8_t> pht;   /* the table, in main memory */
  std::vector<phb_entry> phb;                  /* the on-chip buffer */
  std::array<uint8_t, 3> filter_cand{{0, 0, 0}};
  std::size_t phb_entries{256};
  uint8_t default_select{0};                   /* the reserved entry */
  bool apply_degree{true};
  bool apply_filter{true};

  /* counters */
  uint64_t n_access{0}, n_phb_hit{0}, n_phb_miss{0}, n_no_hint{0}, n_issued{0}, n_filtered{0};
  std::vector<uint64_t> per_member;

  /* Per-PC demand accesses and L1D demand misses, counted over the
     region of interest only. The sweep ranks each load PC by its misses
     under every (member, degree) pair, and the least-missing pair is
     that PC's oracle choice -- the place where the paper measured the
     average memory access time instead. An L1D prefetcher module cannot
     observe the latency below it, so the miss count is what we rank on;
     it is the quantity this prefetcher directly controls. */
  std::unordered_map<uint64_t, std::array<uint64_t, 2>> per_pc;

  void prefetcher_initialize();
  uint32_t prefetcher_cache_operate(champsim::address addr, champsim::address ip, uint8_t cache_hit, bool useful_prefetch, access_type type,
                                    uint32_t metadata_in);
  uint32_t prefetcher_cache_fill(champsim::address addr, long set, long way, uint8_t prefetch, champsim::address evicted_addr, uint32_t metadata_in);
  void prefetcher_final_stats();

  hint lookup(uint64_t pc);
  int member_index(const std::string& name) const;
  void load_table(const std::string& path);
};

#endif
