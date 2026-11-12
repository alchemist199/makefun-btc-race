# BTC race bot — TP variant (candidate resubmission, NOT yet submitted)

Variant of the submitted entry (dev +$7.85, official server grade
+$7.850560). The ONLY changes: a take-profit exit (+0.5%) and a longer
hold cap (180 -> 240 bars). Entry signals, sizing and protocol use are
identical. All code here was written from scratch; no other entrant's
code was read or copied (only the public leaderboard descriptions were
used as inspiration for which strategy families to test).

## Result (dev window, 24h, BTC -2.30%)

|                     | submitted entry | this variant |
|---|---|---|
| net PnL             | +$7.85          | **+$11.28**  |
| trades              | 5               | 9            |
| fees                | $2.42           | $4.03        |
| max drawdown        | -0.77%          | -0.73%       |
| H1 (first 12h)      | +$8.95          | +$13.19      |
| H2 (second 12h)     | +$0.11          | +$0.10       |

Trade log (simulator, fills at next bar's open):
- buy bar 55 @ $73,910.73 -> TP sell bar 57 @ $74,292.72, +$4.76
- buy bar 58 @ $74,119.84 -> TP sell bar 160 @ $74,595.67, +$6.04
- buy bar 161 @ $74,634.12 -> hold sell bar 401 @ $74,537.94, -$1.70
- buy bar 524 @ $73,582.33 -> TP sell bar 555 @ $73,910.53, +$4.09
- buy bar 1434 @ $71,922.51 -> flatten at close, +$0.10

## Perturbation (+-20% on every parameter, 16 variants)

All 16 stay positive. Worst: MOM_THR x1.2 -> +$5.24. Full table
(`perturb.py` output): TP x0.8 +$6.33, TP x1.2 +$6.42, DIP_N x0.8
+$7.60, DIP_TURN x1.2 +$7.89, HOLD x1.2 +$8.44, HOLD x0.8 +$9.31,
DIP_PCT x1.2 +$7.60, MOM_THR x1.2 +$5.24, everything else +$11.28
(unchanged trades) or +$11.29.

CAVEATS, stated plainly:
- TP is the most sensitive parameter: 0.5% gives $11.28, but 0.4% and
  0.6% both give ~$6.40. They stay clearly positive (never negative),
  so it passes the stated robustness rule, but the peak is not flat.
- H2 is +$0.10 from the final-bar flatten fluke (same as the submitted
  entry). Two perturbations give H2 exactly $0.00 (total PnL still
  positive). H2 cannot be genuinely improved on this window: the second
  half is a steady -2.33% grind with no bounce bigger than +0.13%/hour,
  below the ~26bp round-trip cost of any trade.
- Did NOT reach the $13.60 dev-top-10 threshold. This is the best found
  across ~14,000 configurations (see below); $11.28 is the ceiling of
  this strategy family on this window.

## Wire verification (`wiretest_v.py`)

- 1,440/1,440 replies, exit 0, stderr empty, ~0.3s total think time.
- All 5 buy notionals and 4 sell quantities match the simulator exactly.
- Two full wire runs byte-identical (deterministic).
- "final cash $0.00" in the wire log is the known driver artifact (it
  does not simulate the end flatten); the simulator's flatten gives
  final cash $1,011.28.

## What was searched (all in the local simulator, validated EXACT vs
## the official harness and vs the server's +$7.850560)

- sweep8 (9,072 runs): fixed-hold joint grid (hold 90-300, momentum
  0.4-0.6%, conf 0-0.3%, dip SMA 30/60/90, 0.3-0.7%, turn 5/10).
  Ceiling $8.49 -- the fixed-hold family is exhausted.
- sweep9 (600 runs): take-profit 0.5-1.5% / reversal exits on the hold.
  TP 0.5% + hold 240 -> $11.28. TP 0.8-1.0% is WORSE here ($9.12-9.77).
- sweep10 (3,456 runs): trend gates (EMA60, SMA240, SMA60), 40bp dip,
  TP 60/80/100bp, hold 120, 15bp stop-loss. Gates never help; the stop
  never triggers; best stays $11.28.
- sweep11 (392 runs): re-entry cooldowns (30/60/120 bars, after TP or
  any exit) + fine TP (30-60bp). Cooldowns HURT (they block the +$6.04
  immediate re-buy). Best stays $11.28.
- sweep12 (90 runs): momentum-only cooldown after TP exits. Also hurts.
- sweep13 (648 runs): don't-buy-the-top filter (60-bar high), faster
  momentum (5/8 bars), earlier dip turn (3/5), separate dip TP.
  Nothing beats $11.28.

Rejected earlier by the first builder (not repeated): 512 EMA-cross
configs, Donchian breakouts, trailing stops (knife-edge: 0.24% and
0.36% lose, only 0.30% wins), reversal exits, slow-EMA exits.

## Files

- `variant/main.py` (4,405 B) -- the candidate bot, stdlib only.
- `variant/vendor/makefun_bars.py` -- byte-identical kit shim copy.
- `variant/LICENSE` -- MIT.
- Sweep scripts + results: `sweep8.py` .. `sweep13.py`,
  `sweep8_results.json`, `sweep9_results.json`, `sweep10_results.json`,
  `sweep11_results.json`, `sweep12_results.json`, `sweep13_results.json`,
  `perturb.py`, `wiretest_v.py`, `wire-replies-variant.json`.

NOT touched: `../entry/` and the GitHub repo (the submitted +$7.85
entry is intact as the fallback). Nothing here is submitted.
