import backtrader as bt

class RsiTrendWithTPSLStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('trend_sma_period', 500),
        ('take_profit',0.005),  # 0.5%
        ('stop_loss',0.003),   # 0.3%
    )

    def __init__(self):
        self.data_main = self.datas[0]  # 15m
        self.data_trend = self.datas[0]  # 1h

        self.rsi = bt.indicators.RSI(self.data_main.close, period=self.params.rsi_period)
        self.trend_sma = bt.indicators.SMA(self.data_trend.close, period=self.params.trend_sma_period)
        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return 

        if len(self.data_trend) == 0:
            return  # wait until higher TF SMA is ready

        trend_up = self.data_main.close[0] > self.trend_sma[0]
        trend_down = self.data_main.close[0] < self.trend_sma[0]

        pos = self.position

        close = self.data_main.close[0]
        if pos:
            if pos.size > 0:  # Long position
                if close >= self.entry_price * (1 + self.params.take_profit):
                    self.order = self.close()
                elif close <= self.entry_price * (1 - self.params.stop_loss):
                    self.order = self.close()

            elif pos.size < 0:  # Short position
                if close <= self.entry_price * (1 - self.params.take_profit):
                    self.order = self.close()
                elif close >= self.entry_price * (1 + self.params.stop_loss):
                    self.order = self.close()

        # Entry logic
        elif not pos:
            if self.rsi < self.params.rsi_oversold and trend_up:
                self.order = self.buy()
                self.entry_price = close
            elif self.rsi > self.params.rsi_overbought and trend_down:
                self.order = self.sell()
                self.entry_price = close

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None