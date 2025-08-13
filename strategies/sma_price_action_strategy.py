import backtrader as bt

class SMAPriceActionStrategy(bt.Strategy):
    params = dict(
        sma_fast=24,
        sma_trend=200,
        atr_period=14,
        adx_period=14,
        atr_dist_factor=0.3,
        rr_ratio=2.0
    )

    def __init__(self):
        self.sma_fast = bt.ind.SMA(period=self.p.sma_fast)
        self.sma_trend = bt.ind.SMA(period=self.p.sma_trend)
        self.atr = bt.ind.ATR(period=self.p.atr_period)
        self.adx = bt.ind.ADX(period=self.p.adx_period)

    def next(self):
        if self.position:
            return  # Already in a trade

        price = self.data.close[0]
        candle_open = self.data.open[0]
        candle_close = self.data.close[0]
        candle_high = self.data.high[0]
        candle_low = self.data.low[0]

        # Filter 1: Trend (on current TF)
        if price > self.sma_trend:
            direction = 'long'
        elif price < self.sma_trend:
            direction = 'short'
        else:
            return

        # Filter 2: Price relative to SMA24
        above_sma_fast = candle_close > self.sma_fast[0]
        below_sma_fast = candle_close < self.sma_fast[0]
        dist_from_sma = abs(candle_close - self.sma_fast[0])
        if dist_from_sma < self.p.atr_dist_factor * self.atr[0]:
            return  # Too close to SMA

        # Filter 3: Price action pattern
        is_bullish_engulfing = (
            candle_close > candle_open and
            self.data.open[-1] > self.data.close[-1] and
            candle_open < self.data.close[-1] and
            candle_close > self.data.open[-1]
        )
        is_bearish_engulfing = (
            candle_close < candle_open and
            self.data.open[-1] < self.data.close[-1] and
            candle_open > self.data.close[-1] and
            candle_close < self.data.open[-1]
        )

        is_bullish_pinbar = (
            (candle_high - max(candle_open, candle_close)) > 2 * abs(candle_open - candle_close) and
            candle_close > candle_open
        )
        is_bearish_pinbar = (
            (min(candle_open, candle_close) - candle_low) > 2 * abs(candle_open - candle_close) and
            candle_close < candle_open
        )
        if direction == 'long' and above_sma_fast and (is_bullish_engulfing): #or (is_bullish_pinbar)
            self.buy_signal(price, 'long')
        elif direction == 'short' and below_sma_fast and (is_bearish_pinbar): #or (is_bearish_engulfing)
            self.sell_signal(price, 'short')


    def buy_signal(self, price, direction):
        stop_loss = self.data.low[0] - 1.5 * self.atr[0]
        take_profit = price + self.p.rr_ratio * (price - stop_loss)
        self.buy_bracket(
            price=price,
            stopprice=stop_loss,
            limitprice=take_profit,
            size=self.broker.getvalue() * 0.001 / (price - stop_loss)
        )

    def sell_signal(self, price, direction):
        atr = self.atr[0]
        stop_loss = self.data.high[0] + 1.5 * atr
        take_profit = price - self.p.rr_ratio * (stop_loss - price)
        self.sell_bracket(
            price=price,
            stopprice=stop_loss,
            limitprice=take_profit,
            size=self.broker.getvalue() * 0.001 / (stop_loss - price)
        )