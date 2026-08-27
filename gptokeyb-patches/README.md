# Patched gptokeyb source record

The input helper is based on PortsMaster gptokeyb commit
`5b1284e1502548d476aa38e5979b0a8f48cb7b94`. Apply
`01-immediate-start-back-kill-chord.patch` at that commit. The new option is
default-off; no other port changes behaviour unless it explicitly passes
`-immediate-start-back`.

The RG353VS candidate is AArch64 and dynamically uses the console's SDL2. It is
rebuilt with `harness/build_gptokeyb_mgs2.sh`; target headers and extracted
target libraries are machine-local inputs configured in `.env`. The exact
compiler, strip tool, target SDL2/libstdc++ inputs and candidate hash are pinned
in `device/FOLLOWUP_CANDIDATE.lock`. The candidate hash is:

```text
49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a
```

The binary is deliberately not tracked. Its corresponding source is the pinned
upstream tree plus this patch, under GPL-2.0; see `THIRD_PARTY_NOTICES.md`.
