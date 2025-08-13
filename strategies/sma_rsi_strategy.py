import backtrader as bt

class SmaRsiStrategy(bt.Strategy):
    params = dict(
        sma_short=5,
        sma_long=20,
        rsi_period=14,
        rsi_overbought=70,
        take_profit=0.005,  # 0.5%
        stop_loss=0.003    # 0.3%
    )

    def __init__(self):
        self.sma1 = bt.ind.SMA(period=self.p.sma_short)
        self.sma2 = bt.ind.SMA(period=self.p.sma_long)
        self.rsi = bt.ind.RSI(period=self.p.rsi_period)
        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return

        # Check for open position
        if self.position:
            # Take Profit / Stop Loss
            if self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):
                self.order = self.close()
            elif self.data.close[0] <= self.entry_price * (1 - self.p.stop_loss):
                self.order = self.close()

        else:
            # Entry logic
            if self.sma1[0] > self.sma2[0] and self.rsi[0] < self.p.rsi_overbought:
                self.order = self.buy()
                self.entry_price = self.data.close[0]

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None