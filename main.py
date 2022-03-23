from trader import trader

bot = trader('BTC/USDT', '1m', 'binanceusdm', 0.001, True, True, 'your api key', 'your api secret', ['5086658827'])
bot.run()