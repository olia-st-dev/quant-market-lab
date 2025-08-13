import backtrader as bt

class RsiMacdStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('macd1', 12),     # Fast EMA
        ('macd2', 26),     # Slow EMA
        ('macdsig', 9),    # Signal line
    )

    def __init__(self):
        self.data_main = self.datas[0]

        self.rsi = bt.indicators.RSI(self.data_main.close, period=self.p.rsi_period)

        self.macd = bt.indicators.MACD(
            self.data_main.close,
            period_me1=self.p.macd1,
            period_me2=self.p.macd2,
            period_signal=self.p.macdsig
        )
        self.cross = bt.ind.CrossOver(self.macd.macd, self.macd.signal)

        self.order = None

    def next(self):
        if self.order:
            return

        pos = self.position

        # Entry conditions
        if not pos:
            if self.rsi < self.p.rsi_oversold and self.cross > 0:
                self.order = self.buy()
            elif self.rsi > self.p.rsi_overbought and self.cross < 0:
                self.order = self.sell()

        else:
            # Exit on RSI reverting to neutral zone
            if pos.size > 0 and self.rsi > 50:
                self.order = self.close()
            elif pos.size < 0 and self.rsi < 50:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
