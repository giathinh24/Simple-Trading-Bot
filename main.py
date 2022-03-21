import ccxt
from datetime import datetime
import numpy
import pandas as pd

def computeSMA(array, timeperiod):
    ma = []
    for i in range(timeperiod-1):
        ma.append(0) 
    for i in range(timeperiod, len(array)+1):
        ma.append(sum(array[i-timeperiod:i])/timeperiod)
    return ma

def computeEMA(array, timeperiod):
    ema = []
    sum = 0
    smooth = 2/(timeperiod+1)
    for i in range(timeperiod-1):
        ema.append(0)
        sum += array[i]
    ema.append((sum+array[timeperiod-1])/timeperiod)
    for i in range(timeperiod, len(array)):
        ema.append(array[i]*smooth + ema[i-1]*(1-smooth))
    return ema

def computeRSI (data, timeperiod): # Reference: https://tcoil.info/compute-rsi-for-stocks-with-python-relative-strength-index/
    diff = numpy.diff(data)
    diff = diff[2:]

    #this preservers dimensions off diff values
    up_chg = 0 * diff
    down_chg = 0 * diff
    
    # up change is equal to the positive difference, otherwise equal to zero
    up_chg[diff > 0] = diff[ diff>0 ]
    
    # down change is equal to negative deifference, otherwise equal to zero
    down_chg[diff < 0] = diff[ diff < 0 ]
    
    # check pandas documentation for ewm
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.ewm.html
    # values are related to exponential decay
    # we set com=time_window-1 so we get decay alpha=1/time_window
    up_chg = pd.DataFrame(up_chg)
    down_chg = pd.DataFrame(down_chg)

    up_chg_avg   = up_chg.ewm(com=timeperiod-1 , min_periods=timeperiod).mean()
    down_chg_avg = down_chg.ewm(com=timeperiod-1 , min_periods=timeperiod).mean()
    
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    rsi = rsi.values.tolist()
    rsi_list = [item for sublist in rsi for item in sublist]
    return rsi_list

def computeMACD(array, fastperiod=12, slowperiod=26, signalperiod=9):
    ema_fast = computeEMA(array, fastperiod)
    ema_slow = computeEMA(array, slowperiod)
    MACD = []
    for i in range(len(ema_fast)):
        MACD.append(ema_fast[i]-ema_slow[i])
    MACD_SIGNAL = computeEMA(MACD, signalperiod)
    MACD_HIST = []
    for i in range(len(MACD)):
        MACD_HIST.append(MACD[i]-MACD_SIGNAL[i])
    return MACD, MACD_SIGNAL, MACD_HIST


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
        EMA10 = computeEMA(close, timeperiod=10)
        EMA20 = computeEMA(close, timeperiod=20)
        MA50 = computeSMA(close, timeperiod=50)
        RSI = computeRSI(close, timeperiod=14)
        MACD, MACD_SIGNAL, MACD_HIST = computeMACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        print(EMA10, EMA20, MA50, RSI, MACD, MACD_SIGNAL, MACD_HIST)
    elif now%interval_second[interval] != 0 and run_once == 1:
        run_once = 0