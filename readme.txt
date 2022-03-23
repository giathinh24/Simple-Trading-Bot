-The strategy is as follow:
    +Open long/buy position when: EMA10>EMA20>MA50 and RSI<70 and MACD>0
    +Open short/sell order when: EMA10<EMA20<MA50 and RSI>30 and MACD<0
-Initial parameters can be changed in line 98=106 of main.py
-If you want to run live, fill your API keys in and remove the comments of line 118-119
-Dry run will be running at default. If you choose to run live, dry run features will double as a logging method
-Dry run/logging result will be stored in a CSV file named dryRunResult.csv

22/03/2022:
-Move main to trader.py. Change its structure to OOP.
-To set parameters, change line 3 in main. The order is: [symbol, timeframe, exchange, trade quantity, is future, live trade mode, api key, api secret, [telegram is]]