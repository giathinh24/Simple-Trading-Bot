import ccxt
from datetime import datetime
import numpy
import talib

# Operational parameters
symbol = 'BTC/USDT'
interval = '1m'
exchange = 'binance'

# Operational variables
close = []
run_once = 0
interval_second = {'1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '8h': 28800, '12h': 43200, '1d': 86400, '3d': 259200, '1w': 604800, '1M': 2592000}

# Exchange initialization
exchange = getattr(ccxt, exchange)({'enableRateLimit': True})

# Get historical klines closes
print('Running...')
ohlcvs = exchange.fetch_ohlcv(symbol, interval, limit = 400)
for ohlcv in ohlcvs[:-1]:
    close.append(ohlcv[4]) # Get historical close price and append to a list

# Main program loop
while 1:
    # Getting live close prices
    now = round(datetime.timestamp(datetime.now())-1)
    if now%interval_second[interval] == 0 and run_once == 0:
        last = exchange.fetch_ticker(symbol)
        close.append(last['last'])
        run_once = 1
        print(close)
        
        # Calculate indicators
        close = close[-500:]
        num_closes = numpy.array(close)
        EMA10 = talib.EMA(num_closes, timeperiod=10)
        EMA20 = talib.EMA(num_closes, timeperiod=20)
        MA50 = talib.SMA(num_closes, timeperiod=50)
        RSI = talib.RSI(num_closes, timeperiod=14)
        MACD, MACD_SIGNAL, MACD_HIST = talib.MACD(num_closes, fastperiod=12, slowperiod=26, signalperiod=9)
        print(EMA10[-1], EMA20[-1], MA50[-1], RSI[-1], MACD[-1], MACD_SIGNAL[-1], MACD_HIST[-1])
    elif now%interval_second[interval] != 0 and run_once == 1:
        run_once = 0