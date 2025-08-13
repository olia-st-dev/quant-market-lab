import pandas as pd

pair = 'EURJPY'  # Currency pair to process
# Load M1 data
df = pd.read_csv(f"data/DAT_MT_{pair}_M1_2024.csv", header=None)
df.columns = ["date", "time", "open", "high", "low", "close", "volume"]

# Combine datetime
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
df.set_index('datetime', inplace=True)

# Resample to 1 minute
df_1m = df.resample('1min').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()
df_1m.to_csv(f"data/{pair}_1m.csv")
print(f"Saved {pair}_1m.csv")

# Resample to 15 minutes
df_15m = df.resample('15min').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()
df_15m.to_csv(f"data/{pair}_15m.csv")
print(f"Saved {pair}_15m.csv")

#print(df_15m.index.dtype)

# Resample to 1 hour
df_1h = df.resample('1h').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()
df_1h.to_csv(f"data/{pair}_1h.csv")
print(f"Saved {pair}_1h.csv")

# Resample to 4 hour
df_4h = df.resample('4h').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()
df_4h.to_csv(f"data/{pair}_4h.csv")
print(f"Saved {pair}_4h.csv")

# Resample to 1 day
df_1d = df.resample('1d').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()
df_1d.to_csv(f"data/{pair}_1d.csv")
print(f"Saved {pair}_1d.csv")
