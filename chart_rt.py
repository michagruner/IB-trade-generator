import ib_insync
import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource
from datetime import datetime
from math import pi

# Connect to the IB API
ib = ib_insync.IB()
ib.connectAsync()

# Define the contract for the E-mini future on S&P 500 for June 2023
contract = ib_insync.Future('ES', '202306', 'GLOBEX')

# Define the plot
p = figure(x_axis_type="datetime", width=1000, title="ES Real-Time")
p.xaxis.major_label_orientation = pi/4
p.grid.grid_line_alpha = 0.3

# Define the data source
source = ColumnDataSource(data=dict(date=[], open=[], high=[], low=[], close=[], volume=[]))

# Add the candlesticks
inc = source.data['close'] > source.data['open']
dec = source.data['open'] > source.data['close']
w = 5*60*1000 # 5 minutes in ms

p.segment(x0='date', y0='high', x1='date', y1='low', color="black", source=source)
p.vbar(x='date', width=w, top='open', bottom='close', fill_color="#D5E1DD", line_color="black", source=source, selection_color="blue", nonselection_color="#D5E1DD", selection_alpha=1, nonselection_alpha=0.2)
p.vbar(x='date', width=w, top='open', bottom='close', fill_color="#F2583E", line_color="black", source=source, selection_color="blue", nonselection_color="#F2583E", selection_alpha=1, nonselection_alpha=0.2)

# Define the callback function to update the data source
def update_data():
    bars = ib.reqRealTimeBars(contract, 5, 'MIDPOINT', True)
    for bar in bars:
        date = datetime.fromtimestamp(bar.time)
        source.stream(dict(date=[date], open=[bar.open], high=[bar.high], low=[bar.low], close=[bar.close], volume=[bar.volume]))

# Add the callback function to the document
curdoc().add_periodic_callback(update_data, 500)

# Show the chart
curdoc().title = "ES Real-Time"
curdoc().add_root(p)

