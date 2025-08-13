import backtrader as bt

class RsiTrendStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('trend_sma_period', 500),
    )

    def __init__(self):
        self.data_main = self.datas[0]  # 15m
        self.data_trend = self.datas[0]  # 1h

        self.rsi = bt.indicators.RSI(self.data_main.close, period=self.params.rsi_period)
        self.trend_sma = bt.indicators.SMA(self.data_trend.close, period=self.params.trend_sma_period)
        self.order = None

    def next(self):
        if self.order:
            return

        if len(self.data_trend) == 0:
            return  # wait until higher TF SMA is ready

        trend_up = self.data_main.close[0] > self.trend_sma[0]
        trend_down = self.data_main.close[0] < self.trend_sma[0]

        pos = self.position

        # Long only if in uptrend
        if not pos:
            if self.rsi < self.params.rsi_oversold and trend_up:
                self.order = self.buy()
            elif self.rsi > self.params.rsi_overbought and trend_down:
                self.order = self.sell()
        else:
            # Exit on RSI crossing back to neutral
            if pos.size > 0 and self.rsi > 50:
                self.order = self.close()
            elif pos.size < 0 and self.rsi < 50:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None