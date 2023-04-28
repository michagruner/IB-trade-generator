from math import pi

import ib_insync
import pandas as pd
from bokeh.plotting import figure, show

# Connect to the IB API
ib = ib_insync.IB()
ib.connect()

# Define the contract for the E-mini future on S&P 500 for June 2023
contract = ib_insync.Future('ES', '202306', 'CME')

try:
    # Retrieve the historical price data for the last 24 hours
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr='2 D',
        barSizeSetting='5 mins',
        whatToShow='MIDPOINT',
        useRTH=False,
        formatDate=1
    )

    # Convert the price data to a Pandas DataFrame
    df = ib_insync.util.df(bars)
except Exception as e:
    print(f"Error retrieving historical data: {e}")
    ib.disconnect()
    exit()

inc = df.close > df.open
dec = df.open > df.close
w = 5*60*1000 # 5 minutes in ms

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

p = figure(x_axis_type="datetime", tools=TOOLS, width=1000, title = "ES")
p.xaxis.major_label_orientation = pi/4
p.grid.grid_line_alpha=0.3

p.segment(df.date, df.high, df.date, df.low, color="black")
p.vbar(df.date[inc], w, df.open[inc], df.close[inc], fill_color="#D5E1DD", line_color="black")
p.vbar(df.date[dec], w, df.open[dec], df.close[dec], fill_color="#F2583E", line_color="black")

# Show the chart
show(p)

