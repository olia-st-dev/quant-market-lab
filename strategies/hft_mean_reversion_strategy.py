import backtrader as bt

class HFTMeanReversionStrategy(bt.Strategy):
    params = dict(
        lookback=20,
        z_thresh=0.5,
        exit_bars=5,
        stake=10000,
    )

    def __init__(self):
        self.sma = bt.ind.SMA(self.data.close, period=self.p.lookback)
        self.std = bt.ind.StandardDeviation(self.data.close, period=self.p.lookback)
        self.order = None
        self.bar_executed = None

    def next(self):
        if len(self.data) < self.p.lookback + 5:
            return

        z = (self.data.close[0] - self.sma[0]) / (self.std[0] + 1e-6)
        #print(f"{self.data.datetime.datetime(0)} | Z-score: {z:.2f} | Close={self.data.close[0]}")

        if self.order:
            return

        if not self.position:
            if z < -self.p.z_thresh:
                self.order = self.buy(size=self.p.stake)
                self.bar_executed = len(self)
            elif z > self.p.z_thresh:
                self.order = self.sell(size=self.p.stake)
                self.bar_executed = len(self)
        else:
            if len(self) - self.bar_executed >= self.p.exit_bars:
                self.order = self.close()
