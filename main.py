#!/usr/bin/env python3
"""BTC race bot: robust long-only trend + dip entries, take-profit exits.

Variant of the submitted entry (which scores +$7.85 on the dev window):
the only changes are a take-profit exit and a longer hold cap. Everything
else -- entry signals, sizing, protocol use -- is identical.

Strategy (all decisions on 1-minute closes of CBBTC, long only, full size):
  ENTRY (when flat), either signal:
    - Momentum: 10-bar return > 0.5% AND 30-bar return > 0.3% (the 30-bar
      confirmation keeps the bot out of short-lived bounces inside a
      downtrend; without it the 10-bar trigger alone fires on noise).
    - Dip: close > 0.5% below its 60-bar simple average AND turning up
      (close above the close 10 bars ago) -- buys pullbacks inside an
      uptrend and local bottoms, not falling knives.
  EXIT (when holding), whichever comes first:
    - Take-profit: position value >= cost x 1.005 (+0.5%). A fixed hold
      alone lets a rally give its gains back when the price turns; taking
      +0.5% locks the move in and frees the cash for the next signal.
      (A trailing stop was rejected: its width proved knife-edge on the
      dev window, 0.24% and 0.36% both losing while 0.30% won. A plain
      take-profit has no such cliff: +-20% on it stays positive.)
    - Hold cap: sell the whole position 240 bars after entry.
  Sizing: every buy spends all cash (one position, max 100% of equity).
  Orders cap slippage at 100 bps from the latest close, as the kit
  baselines do. No clock, no randomness, no network: two runs on the
  same bars give the same orders. Standard library only.

Dev window (24h, 1,439 bars, BTC -2.30%): net PnL +$11.28, 9 trades,
max drawdown -0.73%, fees $4.03. First half +$13.19, second half +$0.11
-- the bot sat in cash through the steady decline instead of holding
through it. Every +-20% perturbation of every parameter stays positive
(worst +$5.24, on the momentum threshold). Baselines on the same window:
buy-and-hold -$25.97, momentum -$23.31, ema-cross -$95.88,
rsi-bollinger -$46.52, adx-momentum -$53.35, hold-cash $0.00.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
MAX_SLIPPAGE_BPS = 100

# Parameters (see module docstring for why each is what it is).
MOM_N = 10          # momentum window, bars
MOM_THR = 0.005     # 10-bar return must exceed 0.5%
CONF_N = 30         # confirmation window, bars
CONF_THR = 0.003    # 30-bar return must exceed 0.3%
DIP_N = 60          # dip reference: simple average of this many closes
DIP_PCT = 0.005     # close must be 0.5% below that average
DIP_TURN = 10       # ... and above the close this many bars ago
HOLD_BARS = 240     # bars to hold a position before selling it all
TAKE_PROFIT = 0.005 # sell when position value >= cost x (1 + this)

closes = []         # CBBTC closes, in arrival order (ints, price_scale 5)
entry_seq = -1      # seq of the batch the current position was entered on


def on_batch(state, batch):
    global entry_seq
    for bar in batch["bars"]:
        if bar["symbol"] == SYMBOL:
            closes.append(int(bar["c"]))
    if state.warming_up:
        return []

    held = state.positions.get(SYMBOL)
    if held is not None:
        if (state.value(SYMBOL, held.qty) >= held.cost * (1 + TAKE_PROFIT)
                or state.seq - entry_seq >= HOLD_BARS):
            entry_seq = -1
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    # Flat: look for an entry. Need enough history for both signals.
    if not closes:
        return []
    c = closes[-1]
    enter = False
    if len(closes) > MOM_N and len(closes) > CONF_N:
        if (c / closes[-MOM_N - 1] - 1 > MOM_THR
                and c / closes[-CONF_N - 1] - 1 > CONF_THR):
            enter = True
    if not enter and len(closes) > DIP_N and len(closes) > DIP_TURN:
        avg = sum(closes[-DIP_N:]) / DIP_N
        if c < avg * (1 - DIP_PCT) and c > closes[-DIP_TURN - 1]:
            enter = True
    if enter and state.cash >= 1_000_000:
        entry_seq = state.seq
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
