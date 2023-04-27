import plotly.graph_objs as go

# Create a sample chart
fig = go.Figure(data=go.Scatter(y=[1, 2, 3]))

fig.update_layout(
    yaxis=dict(range=[0, 4])
)

# Define the buttons
buttons = [
    dict(
        type="buttons",
        showactive=False,
        buttons=[
            dict(
                label="+",
                method="relayout",
                args=[
                    {"yaxis.range": [fig.layout.yaxis.range[0]/1.5, fig.layout.yaxis.range[1]*1.1]},
                    {"xaxis.autorange": True},
                ],
            ),
            dict(
                label="-",
                method="relayout",
                args=[
                    {"yaxis.range": [fig.layout.yaxis.range[0]*1.5, fig.layout.yaxis.range[1]/1.1]},
                    {"xaxis.autorange": True},
                ],
            ),
        ],
        x=0.02,
        y=0.5,
        direction="up",
    )
]

# Update the layout with the buttons
fig.update_layout(
    dragmode="pan",
    updatemenus=buttons,
)

fig.show()

