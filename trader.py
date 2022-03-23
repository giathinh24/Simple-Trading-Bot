import ccxt
from datetime import datetime
import numpy
import pandas as pd
import csv
import requests

class trader:
    def __init__(self, _symbol, _interval, _exchange_name, _trade_amount, _is_futures, _live_trade, _apiKey, _apiSecret, _userId):
        self.symbol = _symbol
        self.interval = _interval
        self.exchange_name = _exchange_name
        self.trade_amount = _trade_amount
        self.is_futures = _is_futures
        self.live_trade = _live_trade
        self.apiKey = _apiKey
        self.apiSecret = _apiSecret
        self.userids = []
        for id in _userId:
            self.userids.append(id)

    def computeSMA(self, array, timeperiod):
        ma = []
        for i in range(timeperiod-1):
            ma.append(0) 
        for i in range(timeperiod, len(array)+1):
            ma.append(sum(array[i-timeperiod:i])/timeperiod)
        return ma

    def computeEMA(self, array, timeperiod):
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

    def computeRSI(self, data, timeperiod): # Reference: https://tcoil.info/compute-rsi-for-stocks-with-python-relative-strength-index/
        diff = numpy.diff(data)
        diff = diff[2:]

        #this preservers dimensions off diff values
        up_chg = 0 * diff
        down_chg = 0 * diff
        
        # up change is equal to the positive difference, otherwise equal to zero
        up_chg[diff > 0] = diff[ diff>0 ]
        
        # down change is equal to negative deifference, otherwise equal to zero
        down_chg[diff < 0] = diff[ diff < 0 ]
        
        up_chg = pd.DataFrame(up_chg)
        down_chg = pd.DataFrame(down_chg)

        up_chg_avg   = up_chg.ewm(com=timeperiod-1 , min_periods=timeperiod).mean()
        down_chg_avg = down_chg.ewm(com=timeperiod-1 , min_periods=timeperiod).mean()
        
        rs = abs(up_chg_avg/down_chg_avg)
        rsi = 100 - 100/(1+rs)
        rsi = rsi.values.tolist()
        rsi_list = [item for sublist in rsi for item in sublist]
        return rsi_list

    def computeMACD(self, array, fastperiod=12, slowperiod=26, signalperiod=9):
        ema_fast = self.computeEMA(array, fastperiod)
        ema_slow = self.computeEMA(array, slowperiod)
        MACD = []
        for i in range(len(ema_fast)):
            MACD.append(ema_fast[i]-ema_slow[i])
        MACD_SIGNAL = self.computeEMA(MACD, signalperiod)
        MACD_HIST = []
        for i in range(len(MACD)):
            MACD_HIST.append(MACD[i]-MACD_SIGNAL[i])
        return MACD, MACD_SIGNAL, MACD_HIST

    def writeCSV(self, data, filename = 'dryRunResult.csv'):
        # Create the file if doesn't exist
        try:
            with open(filename, 'r'):
                pass
        except:
            with open(filename, 'w'):
                pass

        with open(filename, 'r') as f:
            content = f.readlines()
            try:
                last_price = float(content[-1].split(',')[-2])
                if data[2] == 'buy':
                    data.append(f'{round(((last_price/float(data[4]))-1)*100,2)}%')
                elif data[2] == 'sell':
                    data.append(f'{round(((float(data[4])/last_price)-1)*100,2)}%')
            except:
                data.append('0%')
            if len(content) == 0:
                    with open(filename, 'w', newline = '') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Time', 'Symbol', 'Side', 'Size', 'Price', 'Profit from last trade'])

        with open(filename, 'a', newline = '') as f:
            writer = csv.writer(f)
            writer.writerow(data)

    def teleSend(self, text):
        token = '5246438844:AAFPeNBBXZ2l7c2fFMat4Uaesw3_yc0CL24' # The token of the bot
        for userid in self.userids:
            params = {'chat_id': userid, 'text': text, 'parse_mode': 'HTML'}
            resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(token), params)
            resp.raise_for_status()

    def run(self):
        # Operational variables
        shorting = False
        longing = False
        close = []
        run_once = 0
        interval_second = {'1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '8h': 28800, '12h': 43200, '1d': 86400, '3d': 259200, '1w': 604800, '1M': 2592000}

        # Exchange initialization
        exchange = getattr(ccxt, self.exchange_name)({
            'enableRateLimit': True,
            'apiKey': self.apiKey,
            'secret': self.apiSecret
            })

        # Get historical klines closes
        print('Running...')
        ohlcvs = exchange.fetch_ohlcv(self.symbol, self.interval, limit = 400)
        for ohlcv in ohlcvs[:-1]:
            close.append(ohlcv[4]) # Get historical close price and append to a list

        # Main program loop
        while 1:
            # Getting live close prices
            now = round(datetime.timestamp(datetime.now())-1)
            if now%interval_second[self.interval] == 0 and run_once == 0:
                last = exchange.fetch_ticker(self.symbol)
                close.append(last['last'])
                run_once = 1
                print(close)
                
                # Calculate indicators
                close = close[-500:]
                EMA10 = self.computeEMA(close, timeperiod=10)
                EMA20 = self.computeEMA(close, timeperiod=20)
                MA50 = self.computeSMA(close, timeperiod=50)
                RSI = self.computeRSI(close, timeperiod=14)
                MACD, MACD_SIGNAL, MACD_HIST = self.computeMACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

                # Long condition
                if (EMA10[-1] > EMA20[-1] > MA50[-1]) and RSI[-1] < 70 and MACD_HIST[-1] > 0 and not longing:
                    print('Long')
                    shorting = False
                    longing = True
                    if self.live_trade:
                        if self.is_futures:
                            try:
                                exchange.create_order(self.symbol, 'market', 'buy', self.trade_amount, params = {"reduceOnly": True})
                            except:
                                pass
                        exchange.create_order(self.symbol, 'market', 'buy', self.trade_amount)
                    # Logging
                    data = [datetime.now().strftime("%m/%d/%Y-%H:%M:%S"), self.symbol, 'buy', self.trade_amount, close[-1]]
                    self.writeCSV(data)
                    # Sending Telegram notification
                    self.teleSend(f'Opening long position of {self.trade_amount} {self.symbol} at {datetime.now().strftime("%m/%d/%Y-%H:%M:%S")} at the price of {close[-1]}')
                
                # Short condition
                elif (EMA10[-1] < EMA20[-1] < MA50[-1]) and RSI[-1] > 30 and MACD_HIST[-1] < 0 and not shorting:
                    print('Short')
                    shorting = True
                    longing = False
                    if self.live_trade:
                        if self.is_futures:
                            try:
                                exchange.create_order(self.symbol, 'market' 'sell', self.trade_amount, params = {'reduceOnly': True})
                            except:
                                pass
                        exchange.create_order(self.symbol, 'market', 'sell', self.trade_amount)
                    # Logging
                    data = [datetime.now().strftime("%m/%d/%Y-%H:%M:%S"), self.symbol, 'sell', self.trade_amount, close[-1]]
                    self.writeCSV(data)
                    # Sending Telegram notification
                    self.teleSend(f'Opening short position of {self.trade_amount} {self.symbol} at {datetime.now().strftime("%m/%d/%Y-%H:%M:%S")} at the price of {close[-1]}')
            elif now%interval_second[self.interval] != 0 and run_once == 1:
                run_once = 0