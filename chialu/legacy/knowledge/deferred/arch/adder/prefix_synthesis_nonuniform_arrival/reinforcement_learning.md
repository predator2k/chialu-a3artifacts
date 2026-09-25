---
family: prefix_synthesis_nonuniform_arrival
pin: {search_method: reinforcement_learning}
---
# reinforcement_learning

PrefixRL: the N-input prefix graph is an N x N grid on which an agent
adds or deletes nodes at non-input/output locations, a legalization
step inserts any missing lower-parent node after each action so every
visited graph stays legal, and scalarized Double-DQN agents learn
separate area and delay Q values. Physical synthesis at four timing
targets supplies the reward, and a sweep of scalarization weights
produces an area-delay Pareto frontier from ripple-carry or Sklansky
starting graphs.

Reinforcement learning is the pick when synthesis-in-the-loop compute
is available and the target flow is fixed: the learned adders
Pareto-dominate Sklansky, Kogge-Stone, Brent-Kung and the published
search-based adders, saving up to 16.0 percent area at 32 bits and
30.2 percent at 64 bits at equivalent delay in the Nangate45 flow,
and transferred designs beat the commercial tool's results in an
industrial 8 nm flow except at the lowest delay target. The costs are
the training run (about 5 days, 192 synthesis workers and 14 GPUs for
64 bits), the uniform arrival assumption, and no power objective;
graphs trained on analytical metrics degrade after physical
synthesis, so the dynamic program and compression/expansion siblings
remain the choice for a non-uniform profile or a small budget.

## references

roy2021 -> R. Roy, J. Raiman, N. Kant, I. Elkin, R. Kirby, M. Siu, S. Oberman, S. Godil, B. Catanzaro, "PrefixRL: Optimization of Parallel Prefix Circuits using Deep Reinforcement Learning", 58th ACM/IEEE Design Automation Conference (DAC), pp. 853-858, 2021.
