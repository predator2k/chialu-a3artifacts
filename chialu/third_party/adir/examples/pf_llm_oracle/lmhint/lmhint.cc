#include "lmhint.h"

#include "cache.h"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>

namespace
{
std::string env_or(const char* k, const std::string& d)
{
  const char* v = std::getenv(k);
  return (v && *v) ? std::string(v) : d;
}
} // namespace

int lmhint::member_index(const std::string& name) const
{
  for (std::size_t i = 0; i < ensemble.size(); ++i)
    if (name == ensemble[i]->name())
      return static_cast<int>(i);
  return 0; /* unknown name falls back to `none` */
}

/* The packed table: "LMHT1", three filter candidates, a count, then the
   PCs and their hint bytes. The packer (pfllm.pack_pht) writes it. */
void lmhint::load_table(const std::string& path)
{
  std::ifstream f(path, std::ios::binary);
  if (!f) {
    std::fprintf(stderr, "[lmhint] no hint table at %s; every load runs the default policy\n", path.c_str());
    return;
  }
  char magic[5] = {};
  f.read(magic, 5);
  if (std::memcmp(magic, "LMHT1", 5) != 0) {
    std::fprintf(stderr, "[lmhint] %s is not an LMHT1 table\n", path.c_str());
    return;
  }
  f.read(reinterpret_cast<char*>(filter_cand.data()), 3);
  uint32_t n = 0;
  f.read(reinterpret_cast<char*>(&n), 4);
  std::vector<uint64_t> pcs(n);
  std::vector<uint8_t> hints(n);
  f.read(reinterpret_cast<char*>(pcs.data()), static_cast<std::streamsize>(n) * 8);
  f.read(reinterpret_cast<char*>(hints.data()), static_cast<std::streamsize>(n));
  pht.reserve(n * 2);
  for (uint32_t i = 0; i < n; ++i)
    pht[pcs[i]] = hints[i];
  std::fprintf(stderr, "[lmhint] loaded %u hints from %s\n", n, path.c_str());
}

void lmhint::prefetcher_initialize()
{
  ensemble = lmh::make_ensemble();
  per_member.assign(ensemble.size(), 0);

  const std::string which = env_or("LMHINT_ENSEMBLE", "full");
  if (which == "reduced") {
    for (const auto& nm : lmh::reduced_members())
      active.push_back(member_index(nm));
  } else {
    for (std::size_t i = 0; i < ensemble.size(); ++i)
      active.push_back(static_cast<int>(i));
  }

  const std::string fields = env_or("LMHINT_FIELDS", "SDF");
  apply_degree = fields.find('D') != std::string::npos;
  apply_filter = fields.find('F') != std::string::npos;

  phb_entries = static_cast<std::size_t>(std::strtoul(env_or("LMHINT_PHB_ENTRIES", "256").c_str(), nullptr, 10));
  if (phb_entries == 0)
    phb_entries = 1;
  phb.assign(phb_entries, phb_entry{});

  default_select = static_cast<uint8_t>(member_index(env_or("LMHINT_DEFAULT", "none")));
  load_table(env_or("LMHINT_TABLE", ""));

  std::fprintf(stderr, "[lmhint] ensemble=%s fields=%s phb=%zu default=%s members=%zu\n", which.c_str(), fields.c_str(), phb_entries,
               ensemble[default_select]->name(), active.size());
}

/* The router: a hint reaches the rest of the design only through this
   buffer lookup. On a miss the reserved entry's policy is used while the
   table read is served. */
lmhint::hint lmhint::lookup(uint64_t pc)
{
  ++n_access;
  const std::size_t idx = (pc >> 2) % phb.size();
  auto& e = phb[idx];
  if (e.valid && e.pc == pc) {
    ++n_phb_hit;
  } else {
    ++n_phb_miss;
    auto it = pht.find(pc);
    e.pc = pc;
    e.raw = (it == pht.end()) ? 0 : it->second;
    e.valid = true;
    /* while the miss is served this access runs the reserved policy */
    hint d;
    d.select = default_select;
    d.degree = 2;
    d.filter = 0;
    d.valid = true;
    return d;
  }
  hint h;
  h.select = static_cast<uint8_t>((e.raw >> 4) & 0xF);
  h.degree = static_cast<uint8_t>((e.raw >> 2) & 0x3);
  h.filter = static_cast<uint8_t>(e.raw & 0x3);
  h.valid = e.raw != 0;
  if (!h.valid)
    ++n_no_hint;
  return h;
}

uint32_t lmhint::prefetcher_cache_operate(champsim::address addr, champsim::address ip, uint8_t cache_hit, bool /*useful_prefetch*/, access_type /*type*/,
                                          uint32_t metadata_in)
{
  const uint64_t pc = ip.to<uint64_t>();
  const lmh::blk b = champsim::block_number{addr}.to<uint64_t>();
  if (!intern_->warmup) {
    auto& s = per_pc[pc];
    ++s[0];
    if (cache_hit == 0)
      ++s[1];
  }
  hint h = lookup(pc);

  /* the multiplexer: the hint names at most one member of the ensemble */
  int sel = h.select;
  if (sel >= static_cast<int>(ensemble.size()) || std::find(active.begin(), active.end(), sel) == active.end())
    sel = 0;

  /* the filter: the named member does not see this demand request */
  int filtered = -1;
  if (apply_filter && h.filter != 0) {
    int cand = filter_cand[h.filter - 1];
    if (cand < static_cast<int>(ensemble.size()))
      filtered = cand;
  }

  /* every member trains on every access unless the hint withholds it */
  for (int i : active) {
    if (i == filtered) {
      ++n_filtered;
      continue;
    }
    ensemble[static_cast<std::size_t>(i)]->train(b, pc, cache_hit != 0);
  }

  if (sel == 0)
    return metadata_in;

  /* the orchestrator: the degree field picks a quartile of the member's
     own native range; without the D field the median is used */
  auto& m = *ensemble[static_cast<std::size_t>(sel)];
  const auto q = m.degrees();
  int degree = q[1];
  if (apply_degree && h.degree >= 1 && h.degree <= 3)
    degree = q[h.degree - 1];
  if (degree <= 0)
    return metadata_in;

  std::vector<lmh::blk> out;
  m.issue(b, pc, degree, out);
  for (lmh::blk t : out) {
    prefetch_line(champsim::address{champsim::block_number{t}}, true, metadata_in);
    ++n_issued;
  }
  per_member[static_cast<std::size_t>(sel)] += out.size();
  return metadata_in;
}

uint32_t lmhint::prefetcher_cache_fill(champsim::address, long, long, uint8_t, champsim::address, uint32_t metadata_in) { return metadata_in; }

void lmhint::prefetcher_final_stats()
{
  const std::string path = env_or("LMHINT_STATS", "");
  if (path.empty())
    return;
  std::ofstream f(path);
  if (!f)
    return;
  f << "{\n";
  f << "  \"accesses\": " << n_access << ",\n";
  f << "  \"phb_hit\": " << n_phb_hit << ",\n";
  f << "  \"phb_miss\": " << n_phb_miss << ",\n";
  f << "  \"no_hint\": " << n_no_hint << ",\n";
  f << "  \"issued\": " << n_issued << ",\n";
  f << "  \"filtered\": " << n_filtered << ",\n";
  f << "  \"pht_entries\": " << pht.size() << ",\n";
  f << "  \"per_member\": {";
  for (std::size_t i = 0; i < ensemble.size(); ++i)
    f << (i ? ", " : "") << "\"" << ensemble[i]->name() << "\": " << per_member[i];
  f << "},\n";
  /* {pc: [demand accesses, demand misses]} over the region of interest */
  f << "  \"per_pc\": {";
  bool first = true;
  for (const auto& [pc, s] : per_pc) {
    f << (first ? "" : ", ") << "\"" << pc << "\": [" << s[0] << ", " << s[1] << "]";
    first = false;
  }
  f << "}\n}\n";
}
