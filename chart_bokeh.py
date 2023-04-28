import pandas as pd
import bokeh.plotting as plt
from bokeh.models import ColumnDataSource
from ib_insync import *

class CandlestickChart:
    def __init__(self, symbol, exchange, last_trade_date):
        self.symbol = symbol
        self.contract = Future(symbol=self.symbol, lastTradeDateOrContractMonth=last_trade_date, exchange=exchange)
        self.ib = IB()
        self.df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        self.source = ColumnDataSource(self.df)
        self.fig = plt.figure(x_axis_type="datetime")
        self.candlestick = self.fig.vbar(x="date", width=12*60*60*1000, top="high", bottom="low", fill_color="#D5E1DD", line_color="black", source=self.source)

    def connect(self):
        self.ib.connect("127.0.0.1", 7497, clientId=0)

    def disconnect(self):
        self.ib.disconnect()

    def retrieve_historical_data(self):
        bars = self.ib.reqHistoricalData(
            self.contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='5 mins',
            whatToShow='TRADES',
            useRTH=True
        )
        data = [[bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume] for bar in bars]
        columns = ["date", "open", "high", "low", "close", "volume"]
        self.df = pd.concat([self.df, pd.DataFrame(data, columns=columns)])
        self.source.data = self.df


    def update_real_time_data(self):
        self.ib.qualifyContracts(self.contract)
        self.ib.reqRealTimeBars(
            self.contract,
            5,
            "TRADES",
            True
        )

    def update_chart(self, bar):
        new_row = {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close, "volume": bar.volume}
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.source.data = self.df


    def start(self):
        self.ib.run()

symbol = 'ES'
exchange = 'CME'
last_trade_date = '202306'
chart = CandlestickChart(symbol, exchange, last_trade_date)
plt.show(chart.fig)
chart.connect()
chart.retrieve_historical_data()
chart.update_real_time_data()

