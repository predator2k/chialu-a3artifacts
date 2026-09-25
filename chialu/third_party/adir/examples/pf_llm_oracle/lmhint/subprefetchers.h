/* The sub-prefetcher ensemble: the fixed part of the LMHint design.
 *
 * Every member exposes the same two operations, and the split between
 * them is what makes the hint's filter field mean anything:
 *
 *   train(addr, ip, hit)   update the member's internal tables
 *   issue(addr, ip, d, out) propose prefetches at degree d
 *
 * A load whose hint filters a member is withheld from that member's
 * train() -- it never pollutes its tables -- while still being served
 * by whichever member the hint selected.
 *
 * degrees() returns the first quartile, the median and the third
 * quartile of the member's own native degree range, which is what the
 * hint's 2-bit degree field selects between.
 *
 * These are compact reimplementations, faithful in mechanism but not
 * line-for-line with any published source. To run the paper's Table 2
 * ensemble, drop in CMU-SAFARI/Pythia's prefetcher/ implementations
 * (MIT) behind this same interface and extend ENSEMBLE below.
 */
#ifndef LMHINT_SUBPREFETCHERS_H
#define LMHINT_SUBPREFETCHERS_H

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace lmh
{
using blk = uint64_t; /* block number: address >> LOG2_BLOCK_SIZE */

constexpr int BLOCKS_PER_PAGE = 64; /* 4 KB page / 64 B line */

struct SubPF {
  virtual ~SubPF() = default;
  virtual const char* name() const = 0;
  virtual void train(blk /*addr*/, uint64_t /*ip*/, bool /*hit*/) {}
  virtual void issue(blk /*addr*/, uint64_t /*ip*/, int /*degree*/, std::vector<blk>& /*out*/) {}
  /* Q1, median, Q3 of this member's native degree range. */
  virtual std::array<int, 3> degrees() const { return {1, 2, 4}; }
};

/* ---------------------------------------------------------------- none */
struct NoPF : SubPF {
  const char* name() const override { return "none"; }
  std::array<int, 3> degrees() const override { return {0, 0, 0}; }
};

/* ----------------------------------------------------------- next_line */
struct NextLine : SubPF {
  const char* name() const override { return "next_line"; }
  std::array<int, 3> degrees() const override { return {1, 2, 4}; }
  void issue(blk addr, uint64_t, int degree, std::vector<blk>& out) override
  {
    for (int k = 1; k <= degree; ++k)
      out.push_back(addr + static_cast<blk>(k));
  }
};

/* ------------------------------------------------------------ ip_stride */
struct IPStride : SubPF {
  struct entry {
    blk last{};
    int64_t stride{};
    int conf{};
  };
  std::unordered_map<uint64_t, entry> tbl;
  static constexpr std::size_t CAP = 1024;

  const char* name() const override { return "ip_stride"; }
  std::array<int, 3> degrees() const override { return {1, 3, 6}; }

  void train(blk addr, uint64_t ip, bool) override
  {
    if (tbl.size() > CAP && tbl.find(ip) == tbl.end())
      tbl.clear(); /* a crude capacity bound, in place of an LRU table */
    auto& e = tbl[ip];
    int64_t d = static_cast<int64_t>(addr) - static_cast<int64_t>(e.last);
    if (d != 0 && d == e.stride)
      e.conf = std::min(e.conf + 1, 3);
    else if (d != 0) {
      e.stride = d;
      e.conf = 0;
    }
    e.last = addr;
  }

  void issue(blk addr, uint64_t ip, int degree, std::vector<blk>& out) override
  {
    auto it = tbl.find(ip);
    if (it == tbl.end() || it->second.conf < 1 || it->second.stride == 0)
      return;
    for (int k = 1; k <= degree; ++k)
      out.push_back(static_cast<blk>(static_cast<int64_t>(addr) + it->second.stride * k));
  }
};

/* ------------------------------------------------------------- streamer */
struct Streamer : SubPF {
  struct stream {
    blk last{};
    int dir{0};
    int conf{0};
  };
  std::unordered_map<uint64_t, stream> pages; /* keyed by page number */
  static constexpr std::size_t CAP = 256;

  const char* name() const override { return "streamer"; }
  std::array<int, 3> degrees() const override { return {2, 4, 8}; }

  void train(blk addr, uint64_t, bool) override
  {
    uint64_t pg = addr / BLOCKS_PER_PAGE;
    if (pages.size() > CAP && pages.find(pg) == pages.end())
      pages.clear();
    auto& s = pages[pg];
    if (s.conf == 0 && s.last == 0) {
      s.last = addr;
      s.conf = 1;
      return;
    }
    int d = (addr > s.last) ? 1 : (addr < s.last ? -1 : 0);
    if (d != 0 && d == s.dir)
      s.conf = std::min(s.conf + 1, 4);
    else if (d != 0) {
      s.dir = d;
      s.conf = 1;
    }
    s.last = addr;
  }

  void issue(blk addr, uint64_t, int degree, std::vector<blk>& out) override
  {
    uint64_t pg = addr / BLOCKS_PER_PAGE;
    auto it = pages.find(pg);
    if (it == pages.end() || it->second.conf < 2 || it->second.dir == 0)
      return;
    for (int k = 1; k <= degree; ++k) {
      blk cand = static_cast<blk>(static_cast<int64_t>(addr) + it->second.dir * k);
      if (cand / BLOCKS_PER_PAGE == pg) /* streamers do not cross a page */
        out.push_back(cand);
    }
  }
};

/* ----------------------------------------------------------------- ampm */
struct AMPM : SubPF {
  struct region {
    std::array<bool, BLOCKS_PER_PAGE> seen{};
  };
  std::unordered_map<uint64_t, region> regions;
  static constexpr std::size_t CAP = 128;

  const char* name() const override { return "ampm"; }
  std::array<int, 3> degrees() const override { return {1, 2, 4}; }

  void train(blk addr, uint64_t, bool) override
  {
    uint64_t pg = addr / BLOCKS_PER_PAGE;
    if (regions.size() > CAP && regions.find(pg) == regions.end())
      regions.clear();
    regions[pg].seen[addr % BLOCKS_PER_PAGE] = true;
  }

  /* A delta is credible when the two previous positions at that delta
     were both accessed; then the next one at that delta is prefetched. */
  void issue(blk addr, uint64_t, int degree, std::vector<blk>& out) override
  {
    uint64_t pg = addr / BLOCKS_PER_PAGE;
    auto it = regions.find(pg);
    if (it == regions.end())
      return;
    const auto& seen = it->second.seen;
    int off = static_cast<int>(addr % BLOCKS_PER_PAGE);
    int issued = 0;
    for (int delta = 1; delta < BLOCKS_PER_PAGE / 2 && issued < degree; ++delta) {
      int a = off - delta, b = off - 2 * delta, n = off + delta;
      if (a >= 0 && b >= 0 && n < BLOCKS_PER_PAGE && seen[a] && seen[b] && !seen[n]) {
        out.push_back(pg * BLOCKS_PER_PAGE + static_cast<blk>(n));
        ++issued;
      }
    }
  }
};

/* -------------------------------------------------------------- sandbox */
struct Sandbox : SubPF {
  static constexpr std::array<int, 8> CAND{1, 2, 3, 4, 8, 16, -1, -2};
  std::array<int, 8> score{};
  std::vector<blk> recent; /* the sandbox: what a candidate offset would have fetched */
  std::size_t cursor{0};
  int epoch{0};
  int best{0};

  const char* name() const override { return "sandbox"; }
  std::array<int, 3> degrees() const override { return {1, 2, 4}; }

  Sandbox() : recent(512, 0) {}

  void train(blk addr, uint64_t, bool) override
  {
    /* score a candidate when this access hits what it would have fetched */
    for (std::size_t i = 0; i < CAND.size(); ++i) {
      blk want = static_cast<blk>(static_cast<int64_t>(addr) - CAND[i]);
      for (blk r : recent)
        if (r == want) {
          ++score[i];
          break;
        }
    }
    recent[cursor] = addr;
    cursor = (cursor + 1) % recent.size();
    if (++epoch >= 256) { /* end of evaluation period: adopt the winner */
      best = static_cast<int>(std::distance(score.begin(), std::max_element(score.begin(), score.end())));
      score.fill(0);
      epoch = 0;
    }
  }

  void issue(blk addr, uint64_t, int degree, std::vector<blk>& out) override
  {
    int off = CAND[static_cast<std::size_t>(best)];
    for (int k = 1; k <= degree; ++k)
      out.push_back(static_cast<blk>(static_cast<int64_t>(addr) + static_cast<int64_t>(off) * k));
  }
};

/* ------------------------------------------------------------------ sms */
struct SMS : SubPF {
  struct fp {
    std::array<bool, BLOCKS_PER_PAGE> bits{};
  };
  std::unordered_map<uint64_t, fp> pattern;  /* signature -> footprint */
  std::unordered_map<uint64_t, uint64_t> active; /* page -> signature */
  static constexpr std::size_t CAP = 512;

  const char* name() const override { return "sms"; }
  std::array<int, 3> degrees() const override { return {2, 4, 8}; }

  static uint64_t sig(uint64_t ip, int off) { return (ip << 6) ^ static_cast<uint64_t>(off); }

  void train(blk addr, uint64_t ip, bool) override
  {
    uint64_t pg = addr / BLOCKS_PER_PAGE;
    int off = static_cast<int>(addr % BLOCKS_PER_PAGE);
    auto it = active.find(pg);
    if (it == active.end()) {
      if (active.size() > CAP)
        active.clear();
      active[pg] = sig(ip, off); /* the trigger access names the region */
      it = active.find(pg);
    }
    if (pattern.size() > CAP && pattern.find(it->second) == pattern.end())
      pattern.clear();
    pattern[it->second].bits[off] = true;
  }

  void issue(blk addr, uint64_t ip, int degree, std::vector<blk>& out) override
  {
    uint64_t pg = addr / BLOCKS_PER_PAGE;
    int off = static_cast<int>(addr % BLOCKS_PER_PAGE);
    auto p = pattern.find(sig(ip, off));
    if (p == pattern.end())
      return;
    int issued = 0;
    for (int i = 0; i < BLOCKS_PER_PAGE && issued < degree; ++i)
      if (p->second.bits[i] && i != off) {
        out.push_back(pg * BLOCKS_PER_PAGE + static_cast<blk>(i));
        ++issued;
      }
  }
};

/* The ensemble, in selection-field order. Index 0 must be `none`, so a
   zeroed hint means "do not prefetch for this load". The 4-bit field
   admits sixteen; the paper's Table 2 uses twelve. */
inline std::vector<std::unique_ptr<SubPF>> make_ensemble()
{
  std::vector<std::unique_ptr<SubPF>> v;
  v.emplace_back(new NoPF());
  v.emplace_back(new NextLine());
  v.emplace_back(new IPStride());
  v.emplace_back(new Streamer());
  v.emplace_back(new AMPM());
  v.emplace_back(new Sandbox());
  v.emplace_back(new SMS());
  return v;
}

/* LMHint-SDFR: the members the hint generator selects most often. The
   run file's `ensemble: reduced` compiles the hardware down to these. */
inline std::vector<std::string> reduced_members() { return {"none", "next_line", "ip_stride", "streamer"}; }

} // namespace lmh
#endif
