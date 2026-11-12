# Param-only variant: HOLD_BARS 180 -> 177 (dev +$9.27)

Candidate for resubmission as round 4 of btc-race-24h-20261112-1439.
ONE constant changed from the submitted original entry — everything else
(byte-for-byte the same code path, same signals, same sizing): only
`HOLD_BARS` in `main.py` goes from 180 to 177.

## Result (local simulator, validated code path)

| | Original (submitted, official +$7.850560) | This variant |
|---|---|---|
| Net PnL dev window | +$7.85 | **+$9.27** |
| H1 / H2 (gross attribution) | +$8.95 / +$0.11 | **+$10.37 / +$0.11** |
| Trades / fees | 5 / $2.42 | 5 / $2.42 |
| Max drawdown | -0.77% | -0.77% |
| Worst perturbation (±20%) | +$2.90 | **+$4.33** |
| Flat-peak ±10% neighbours > $7.85 | 9 / 16 | 11 / 16 |

Trade log (sim): buy bar 55 @ $73,910.73 → sell bar 232 @ $74,392.72
(+$6.12); buy bar 524 @ $73,582.20 → sell bar 701 @ $73,923.54
(+$4.26); buy bar 1434 @ $71,922.36 → flatten at last close (+$0.11).

## Why HOLD=177 wins on this window

Trade 2's exit lands on bar 701, whose open gapped up to $73,992.03
(prior close $73,886.46) — the best exit in the 698-706 stretch.
Trade 1 exits at bar 232 (+$6.12, slightly worse than the original's
bar-235 exit, +$6.83). Net: +$4.26 − $2.12 (trade 2) − $0.13 (trade 1)
+ $0.05 (flatten) ≈ +$1.42 over the original.

## Validation (all done)

- **Perturbation ±20%** (every parameter, one at a time): all 16
  positive, worst **+$4.33** (DIP_N×1.2 and DIP_PCT×0.8). Passes the
  > +$2.00 requirement — and it is the best worst-case of every
  candidate tested (original $2.90, HOLD=190 $2.01, HOLD=178 $3.77).
- **Wire test** (`wiretest_p.py`, real `main.py` driven with
  hello + 1,440 batches from the dataset): 1,440/1,440 replies, exit 0,
  stderr empty; all 5 orders identical to the simulator (same seqs,
  notionals, quantities, fill bars/prices). **Determinism: 2 full wire
  runs byte-identical.** Final equity $1,010.88 mark-to-market vs
  $1,009.27 after the sim's end-of-window flatten — the $1.61 gap is
  exactly the flatten fee/slippage the harness charges, same as the
  original entry whose official grade matched the sim exactly twice.
- **Flat-peak ±10% neighbours: 11/16 above $7.85 — requirement NOT
  fully met.** The 5 fails: DIP_N×0.9 ($5.43), DIP_PCT×1.1 ($5.43),
  DIP_TURN×1.1 ($7.79), HOLD×0.9 ($2.15), HOLD×1.1 ($7.21).

## Honest caveat — requirement 4 is unachievable in this family

The flat-peak test fails for EVERY config tested, including the
currently submitted +$7.85 entry itself (6-7 of 16 neighbours fail)
and every HOLD value on three backbones (a fine HOLD scan 100-300
found NO value whose ±10% neighbours are all > $7.85). The PnL is a
step function of its parameters: entry/exit bars are discrete, and a
fixed-hold exit fills at a single bar's open, so ±10% on HOLD always
moves exits to different prices. The $9.27 edge is therefore partly
exit-bar luck on this one window (trade 2's gap-up open at bar 701),
and it is NOT guaranteed to beat $7.85 on the unseen race window.
What IS solid: same deterministic code path as the twice-verified
original, so the $9.27 should reproduce on the server dev grade; and
the best worst-case perturbation profile (+$4.33) of any candidate.

## Runner-ups (same validation, all fail flat-peak too)

- HOLD=190 (also 1 constant): $9.01, worst-pert $2.01, flat 9/16.
- HOLD=189: $9.06, worst-pert $2.12.
- HOLD=178: $8.78, worst-pert $3.77, flat 10/16.
- HOLD=188: $8.49, worst-pert $2.06.
- Original HOLD=180: $7.85, worst-pert $2.90.

## Search history

~10,800-config joint grid (DIP_TURN × HOLD × DIP_N × DIP_PCT ×
CONF_N × MOM_N × MOM_THR) + OAT sweeps + HOLD fine scan 170-200
(step 1). Prior work already covered 9,072 fixed-hold configs
(sweep8, ceiling $8.49 — it never varied CONF_N and used coarse HOLD
steps, which is why HOLD=177/189/190 were missed). No new mechanisms
were tried or added (no TP/SL/trailing-stop/gate/cooldown) — the TP
variant's lesson (+$11.28 predicted vs +$3.98 official) is exactly
why this task was param-only.

## Files

- `main.py` — the variant (diff vs entry/main.py: ONE line, HOLD_BARS).
- `vendor/makefun_bars.py` — kit shim, byte-identical to entry's.
- `README.md` — this file.
- `sweep_oat.py`, `grid1.py`, `grid1_results.json`, `validate.py`,
  `wiretest_p.py`, `wire-replies-hold177.json` — search + validation.

## Recommendation to parent

Resubmit this as round 4 (bundle the original builder session only —
the code lineage is unchanged; the one-line edit needs no new
authorship session) IF the flat-peak caveat is accepted: dev $9.27
with the best worst-case profile, same verified code path. If the
flat-peak requirement is treated as hard, keep the +$7.85 entry —
but note it fails that requirement too, so the requirement cannot be
the deciding factor either way.
