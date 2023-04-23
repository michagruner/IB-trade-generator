import ib_insync
import pandas as pd
import plotly.graph_objects as go

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

# Create a candlestick chart using Plotly
fig = go.Figure(data=[go.Candlestick(x=df['date'],
                                      open=df['open'],
                                      high=df['high'],
                                      low=df['low'],
                                      close=df['close'])])

# Add rectangles and lines to the figure
for line in open('zones.csv'):
    line = line.encode('ascii','ignore').decode('ascii')
    line = line.strip().split(',')
    low, high, zone_type, strength = line
    if zone_type == 'R':
        fig.add_shape(
            type="rect",
            xref="x",
            yref="y",
            x0=df['date'].iloc[0],
            y0=float(low),
            x1=df['date'].iloc[-1],
            y1=float(high),
            fillcolor="red",
            opacity=0.2,
            line_color="red",
            line_width=1,
        )
    elif zone_type == 'S':
        fig.add_shape(
            type="rect",
            xref="x",
            yref="y",
            x0=df['date'].iloc[0],
            y0=float(low),
            x1=df['date'].iloc[-1],
            y1=float(high),
            fillcolor="green",
            opacity=0.2,
            line_color="green",
            line_width=1,
        )
    elif zone_type == 'L':
        fig.add_shape(
            type="line",
            xref="x",
            yref="y",
            x0=df['date'].iloc[0],
            y0=float(low),
            x1=df['date'].iloc[-1],
            y1=float(high),
            line_color="blue",
            line_width=1,
        )

# Update the layout
fig.update_layout(
    title=" ES  Historical Data",
    yaxis_title="Price",
    xaxis_title="Time",
    font=dict(
        family="Arial",
        size=12,
        color="#7f7f7f"
    )
)
# get the y-axis range of the current chart
min_y, max_y = (4000,4200)

fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            buttons=[
                dict(
                    label="Expand Y-Axis",
                    method="relayout",
                    args=[{"yaxis.range": [min_y - 0.1 * (max_y - min_y), max_y + 0.1 * (max_y - min_y)]}],
                ),
                dict(
                    label="Contract Y-Axis",
                    method="relayout",
                    args=[{"yaxis.range": [min_y + 0.1 * (max_y - min_y), max_y - 0.1 * (max_y - min_y)]}],
                ),
            ],
            pad={"r": 10, "t": 10},
            showactive=False,
            x=0,
            xanchor="left",
            y=1.1,
            yanchor="top",
        ),
    ]
)

# Show the plotly figure
fig.show()
"""
# Subscribe to real-time price updates for the E-mini future on S&P 500 for June 2023
ib.qualifyContracts(contract)
ticker = ib_insync.Ticker(contract)
ib_insync.ib.sleep(1)

# Continuously update the chart with real-time data
while True:
    ib.sleep(1)
    ticker.updateEvent += lambda ticker: fig.update_traces(
        x=[df['date'] + ticker.time],
        open=[df['open'] + ticker.bid],
        high=[df['high'] + ticker.bid],
        low=[df['low'] + ticker.bid],
        close=[df['close'] + ticker.bid]
    )
"""
