import ib_insync
import pandas as pd
import plotly.graph_objects as go

# Connect to the IB API
ib = ib_insync.IB()
ib.connect()

# Define the contract for the E-mini future on S&P 500 for June 2023
contract = ib_insync.Future('ES', '202306', 'CME')

# Retrieve the historical price data for the last 24 hours
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='5 mins',
    whatToShow='MIDPOINT',
    useRTH=False,
    keepUpToDate=True,
    formatDate=1
)

# Convert the price data to a Pandas DataFrame
df = ib_insync.util.df(bars)

# Create a candlestick chart using Plotly
fig = go.Figure(data=[go.Candlestick(x=df['date'],
                                      open=df['open'],
                                      high=df['high'],
                                      low=df['low'],
                                      close=df['close'])])

# Display the chart
fig.show()

# Define a function to update the chart
def update_chart(ticker):
    fig.update_traces(
        x=[df['date'] + ticker.time],
        open=[df['open'] + ticker.bid],
        high=[df['high'] + ticker.bid],
        low=[df['low'] + ticker.bid],
        close=[df['close'] + ticker.bid]
    )

# Subscribe to real-time price updates for the E-mini future on S&P 500 for June 2023
ib.qualifyContracts(contract)
ticker = ib_insync.Ticker(contract)

# Attach the update_chart function to the updateEvent
ticker.updateEvent += update_chart

# Start the event loop
ib.run()

