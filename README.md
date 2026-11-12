# BTC race bot — robust long-only trend + dip, fixed-hold exits

Bot for the make.fun bounty `btc-race-24h-20261112-1439` ("Race a BTC trading
bot live for 24 hours"). Python 3.13, standard library only. Entry point is
`main.py`; it talks the `agent-fun/bars-replay/v1` protocol through the kit
Python shim, copied byte-for-byte into `vendor/makefun_bars.py` (the shim is
vendored so it does not count toward authorship).

## Strategy

All decisions use 1-minute closes of CBBTC. Long only, one position, every
buy spends all cash. 7 parameters total, no lookup tables, no clock, no
randomness, no network — two runs on the same bars give the same orders.

**Entry (when flat) — either signal fires:**

- **Momentum:** 10-bar return > 0.5% **and** 30-bar return > 0.3%. The
  30-bar confirmation is the key filter: the 10-bar trigger alone fires on
  short-lived bounces inside a downtrend and loses money on the dev window
  (−$12.48 at a 0.45% threshold); with confirmation the same trigger makes
  +$6.43.
- **Dip:** close > 0.5% below its 60-bar simple average **and** turning up
  (close above the close 10 bars ago). Buys pullbacks and local bottoms,
  not falling knives.

**Exit (when holding):** sell the whole position 180 bars after entry. A
fixed hold rides multi-hour trends and the chop after them. A trailing stop
was tested and rejected: its width is knife-edge on the dev window — 0.24%
and 0.36% both lose money while 0.30% wins — so it cannot be trusted on
unseen prices. A fixed hold of 120–300 bars is positive across the whole
range.

Orders cap slippage at 100 bps from the latest close, as the kit baselines
do.

## What the dev window looked like

1,439 bars, first close $73,739.38 → last $72,044.01, **−2.30%** for the
window. First half (12h): +0.09%, choppy, peaked near $74,689. Second half:
**−2.33%**, a steady grind down with no sustained bounce (best 10-bar
return in the half only +0.47%). 1-minute return stdev 0.05%; 237 flat bars;
buy-and-hold max drawdown −3.94%; pool depth median ~$1.3M USDC. The best
single long trade in the window was buying the bar-45 dip at $73,369 and
selling near $74,689 (+1.80% gross, ~+$15.40 net).

## Dev-window results (kit harness fill model, verified exact)

| bot | net PnL | trades | fees | max DD |
|-----|--------:|-------:|-----:|-------:|
| **this bot** | **+$7.85** | 5 | $2.42 | **−0.77%** |
| buy-and-hold | −$25.97 | 1 | $0.79 | −3.94% |
| momentum | −$23.31 | 1 | $0.68 | −2.33% |
| ema-cross | −$95.88 | 68 | $26.07 | −10.00% |
| rsi-bollinger | −$46.52 | 19 | $7.06 | −3.94% |
| adx-momentum | −$53.35 | 34 | $11.90 | −3.94% |
| hold-cash | $0.00 | 0 | $0.00 | 0.00% |

Every kit baseline loses on the dev window. This bot is the only one that
clears the dev gate (net PnL > $0).

**Trades (decision bar → fill next bar's open):**

1. Buy bar 54 @ $73,910.73 → sell bar 234 @ $74,445.73, **+$6.83** — the
   momentum entry, held 180 bars through the rise and the chop.
2. Buy bar 523 @ $73,582.24 → sell bar 703 @ $73,766.55, **+$2.12** — dip
   entry.
3. Buy bar 1434 @ $71,922.26 → flattened at window end, **+$0.11** — dip
   entry on the final bounce.

**Halves:** first half +$8.95 (gross attribution), second half +$0.11. The
bot sat in cash through the steady second-half decline instead of holding
through it — exactly the behaviour the gate wants.

**Perturbation test (±20% on every parameter, one at a time):** all 14
perturbations stay positive. Worst case +$2.78 (hold 144→216 bars range
+$2.78…+$6.09 without dip; with dip worst +$2.90). Momentum threshold
0.4% / 0.5% / 0.6% → +$6.43 / +$7.85 / +$6.12; confirmation 0.24% / 0.36%
→ unchanged; momentum window 8 / 12 bars → unchanged; dip depth 0.4% /
0.6% → +$8.09 / +$6.14; dip window 48 / 72 → +$6.14 / +$8.09; turn-up
window 8 / 12 → +$8.84 / +$6.43.

**What did not work (tried and discarded):** EMA crosses (512 configs
searched, best −$2.59 — every one loses; gap-confirmation at the cross bar
is impossible because the gap is ~0 at a cross), Donchian breakouts (best
−$2.88), trailing stops (knife-edge, see above), reversal exits (10-bar
return < −0.15% as exit: −$7.78), no-confirmation momentum (−$12.48 at
0.45%), slow-EMA exits (only +$4.69 at best, and the 60/75-bar EMAs go
negative).

## Verification

- **Local grade:** `grade-local --driver process` refuses Python bots on
  this machine (the process sandbox runs node22 only; Python 3.13 runs
  only inside Docker, which is not installed here). Instead the bot was
  verified two independent ways:
  1. A local simulator that replicates the harness fill model exactly
     (integer math; 4 bps fee, 2 bps slippage, 1 + spend/depth impact)
     was validated against the harness on buy-and-hold (**−$25.97, 1
     trade, fees $0.79, maxDD −3.94% — exact match**) and ema-cross
     (**−$95.88, 68 trades, fees $26.07, maxDD −10.00% — exact match**).
     On that simulator this bot scores **+$7.85, 5 trades, maxDD
     −0.77%**.
  2. A wire-level driver fed the real `main.py` the exact hello and all
     1,440 batches (built from the dataset, account/fills from the
     validated simulator): the bot answered all 1,440 batches with the
     correct seq, sent exactly the 5 orders the simulator predicted at
     the same decision points, and exited 0 with empty stderr.
- **Determinism:** two full wire runs produce byte-identical output.
- **Think time:** 1,440 batches in ~0.5 s total including startup — far
  inside the per-batch budget.
- **Protocol:** one reply per batch, seq echoed, ≤16 orders per reply
  (at most 1 ever sent), no order after the final batch.
- **Race-window risk:** the strategy is deliberately low-frequency (5
  trades / 24h) and sits in cash in a downtrend, so the worst realistic
  race outcome is a small loss from 1–2 mistimed entries, not a
  blow-up. The main risk is the opposite: a flat/quiet race window with
  no 0.5% momentum and no 0.5% dip gives 0 trades and a $0.00 PnL,
  which fails the ≥1-trade guardrail. The momentum threshold was kept
  at 0.5% (not raised) partly for that reason.

## Files

- `main.py` — the bot (stdlib only).
- `vendor/makefun_bars.py` — kit Python shim, byte-for-byte copy.
- `README.md` — this file.
- `LICENSE` — MIT.
