import backtrader as bt

class EquityTracker(bt.Analyzer):
    def __init__(self):
        self.values = []
        self.datetimes = []

    def next(self):
        self.values.append(self.strategy.broker.getvalue())
        self.datetimes.append(self.strategy.datas[0].datetime.datetime(0))