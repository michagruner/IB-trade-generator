import ib_insync
import pandas as pd
import altair as alt

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

# Define the Vega-Lite chart using Altair
chart = alt.Chart(df).mark_rule().encode(
    x=alt.X('date:T', title='Time'),
    y=alt.Y('low:Q', title='Price'),
    y2=alt.Y2('high:Q'),
    color=alt.condition(
        'datum.open <= datum.close',
        alt.value('#06982d'),
        alt.value('#ae1325')
    )
).properties(
    title={
        'text': "ES Historical Data",
        'subtitle': f"{contract.localSymbol}"
    },
    width=800,
    height=500
)

# Show the chart
chart

