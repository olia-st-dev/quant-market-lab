import backtrader as bt

class RsiMacdTrendStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('trend_sma_period', 200),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
    )

    def __init__(self):
        self.data_main = self.datas[0]  # 15m
        self.data_trend = self.datas[1]  # for trend filtering

        self.rsi = bt.indicators.RSI(self.data_main.close, period=self.params.rsi_period)

        self.macd = bt.indicators.MACD(
            self.data_main.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        self.macd_cross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        self.trend_sma = bt.indicators.SMA(self.data_trend.close, period=self.params.trend_sma_period)

        self.order = None

    def next(self):
        if self.order:
            return  # skip if order is pending

        if len(self.data_trend) < self.params.trend_sma_period:
            return  # trend filter not ready

        price = self.data_main.close[0]
        trend_up = price > self.trend_sma[0]
        trend_down = price < self.trend_sma[0]
        pos = self.position

        # Entry Logic
        if not pos:
            # Long condition
            if self.rsi < self.params.rsi_oversold and trend_up and self.macd_cross[0] > 0:
                self.order = self.buy()

            # Short condition
            elif self.rsi > self.params.rsi_overbought and trend_down and self.macd_cross[0] < 0:
                self.order = self.sell()

        # Exit Logic
        else:
            if pos.size > 0 and self.rsi > 50:
                self.order = self.close()
            elif pos.size < 0 and self.rsi < 50:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
