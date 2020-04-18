from __future__ import print_function
from flask import Flask
import dash
import dash_table
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
from collections import deque, OrderedDict
import pandas as pd
import dash_daq as daq
import boto3
import json
import decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:8000")

table = dynamodb.Table('Elevator')
print(table)


#sample = pd.read_csv('Lift3_sample.csv')
#### Added a sample condition to simulate
#sample["label"] = sample['Zscale'].apply(lambda x: 1 if x > 8 else 0)
#sample["id"] = '1'
#print(sample.head())
init = table.query(
    KeyConditionExpression=Key('id').eq(1) & Key('index').eq(56) 
    )

X = deque(maxlen=500)
Y = deque(maxlen=500)
#X_f = sample["timestamp"][0]
#Y_f = sample["Zscale"][0]
for j in init['Items']:
	print(j["time"])
	X.append(j["time"])
	Y.append(0)


# =============================HTML Layout for Header=================================#
def build_header():
    return html.Div(
        id="header",
        className="header",
        children=[
            html.Div(
                id="header-text",
                children=[
                    html.H5("Deviation Finder"),
                    html.H6("Elevator Monitor and Exception Reporting"),
                ],
            ),
            html.Div(
                id="header-logo",
                children=[
                    html.Button(
                        id="learn-more-button", children="LEARN MORE", n_clicks=0
                    ),
                ],
            ),
        ],
    )


# =====================================HTML Layout for help data ================================#
def generate_help():
    return html.Div(
        id="knowmore",
        className="help",
        children=(
            html.Div(
                id="knowmore-container",
                className="knowmore-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="knowmore_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="knowmore-text",
                        children=dcc.Markdown(
                            children=(
                                """
                        What is this app about?
                        This is a dashboard for monitoring health conditions of different elevators.
                        """
                                """
                        What does this app shows?
                        The below real time graph show the measurements from an accelerator. Only vertical movements are captured here.
                        Any anomalies captured shall be reflected and highlighted

                        Operators may start the monitoring by pressing start butting and stop the same by clicking on 'Stop' button
                                """
                            )
                        ),
                    ),
                ],
            )
        ),
    )


# =====================================HTML Layout for creating tabs. We only have one tab for now ================================#
def build_tabs():
    return html.Div(
        id="tabs",
        className="tabs",
        children=[
            dcc.Tabs(
                id="app-tabs",
                value="tab2",
                className="custom-tabs",
                children=[
                    dcc.Tab(
                        id="graph-tab",
                        label="Elevator Dashboard",
                        value="tab2",
                        className="graph-tab",
                        selected_className="graph-tab--selected",
                    ),
                ],
            )
        ],
    )


# =====================================HTML Layout for Elevator id panel ================================#
def build_dropdown():
    return html.Div(
        id="lift-menu",
        children=[
            html.Label(id="lift-select-title", children="Select Elevator"),
            html.Br(),
            dcc.Dropdown(
                id='dropdown',
                options=[
                    {'label': 'Elevator 1', 'value': '001'},
                    {'label': 'Elevator 2', 'value': '002'},
                    {'label': 'Elevator 3', 'value': '003'},
                    {'label': 'Elevator 4', 'value': '004'},
                    {'label': 'Elevator 5', 'value': '005'},
                    {'label': 'Elevator 6', 'value': '006'},
                    {'label': 'Elevator 7', 'value': '007'},
                    {'label': 'Elevator 8', 'value': '008'},
                    {'label': 'Elevator 9', 'value': '009'},
                    {'label': 'Elevator 10', 'value': '010'},
                    {'label': 'Elevator 11', 'value': '011'},
                    {'label': 'Elevator 12', 'value': '012'},
                    {'label': 'Elevator 13', 'value': '013'},
                    {'label': 'Elevator 14', 'value': '014'},
                    {'label': 'Elevator 15', 'value': '015'},
                ],
                value='001',
                style={"backgroundColor": "darkgray", "color": "black"}
            ),
            html.Div(id='dd-output-container')
        ])


# =====================================HTML Layout for Elevator id panel ================================#
def build_quick_stats_panel():
    return html.Div(
        id="quick-stats",
        className="row",
        children=[
            html.Div(
                id="card-1",
                children=[
                    html.P("Elevator ID"),
                    daq.LEDDisplay(
                        id="elevator-id",
                        value="001",
                        color="#92e0d3",
                        backgroundColor="#1e2130",
                        size=50,
                    ),
                ],
            ),
            html.Div(
                id="power_button",
                children=[daq.StopButton(id="stop-button", size=160, n_clicks=0, buttonText="START")],
            ),
        ],
    )


# =================================HTML Layout Section banner =======================================#
def generate_section_banner(title):
    return html.Div(className="section-banner", children=title)


# =====================================HTML Layout for Streaming Graph ================================#
def build_graph_panel():
    return html.Div(
        id="graph-container",
        className="graph-show",
        children=[
            generate_section_banner("Live Accelerometer Data"),
            dcc.Graph(
                id='live-graph',
                animate=True,
                figure=go.Figure(
                    {
                        "data": [
                            plotly.graph_objs.Scatter(
                                x=list(X),
                                y=list(Y),
                                name='Scatter',
                                mode='lines+markers',
                                marker_color='gold',
                                line_color='gold',
                            )
                        ],
                        "layout": {
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                            "showlegend": True,
                            "xaxis": dict(
                                showline=True, showgrid=True, zeroline=True, range=[X[0], X[-1]], title='Timestamp',
                                color='gold'
                            ),
                            "yaxis": dict(
                                showgrid=True, showline=True, zeroline=True, range=[-10, 10], title='Vertical value',
                                color='gold'
                            ),
                            "autosize": True,
                        },
                    }
                ),
            ),
        ],
    )


# ============================================Setting Flask server and dash ========================#
server = Flask(__name__)
app = dash.Dash(__name__, server=server)
app.config.suppress_callback_exceptions = True

# ============================================Setting page layout =================================#
app.layout = html.Div(
    id="app-container",
    children=[
        html.Div(id='intermediate-value', style={'display': 'none'}),
        build_header(),
        dcc.Interval(
            id='graph-update',
            interval=1 * 1000,
            n_intervals=0,
            disabled=True,
        ),
        html.Div(
            id="app-tab",
            children=[
                build_tabs(),
                # Main app
                html.Div(id="app-content"),
            ],
        ),
        generate_help(),
    ]
)


###############Call backs start here ##########################
# ======= Callbacks for modal popup =======
@app.callback(
    Output("knowmore", "style"),
    [Input("learn-more-button", "n_clicks"), Input("knowmore_close", "n_clicks")],
)
def update_click_output(button_click, close_click):
    ctx = dash.callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "learn-more-button":
            return {"display": "block"}

    return {"display": "none"}


# =============Call back for tab rendering =======================#
@app.callback(
    [Output("app-content", "children")],
    [Input("app-tabs", "value")],
)
def render_tab_content(tab_switch):
    return (
        html.Div(
            id="status-container",
            children=[
                build_dropdown(),
                build_quick_stats_panel(),
                html.Div(
                    id="graphs-container",
                    children=[build_graph_panel()],
                ),
            ],
        ),
    )

# =============Call back for Start stop of elevator =======================#
@app.callback(
    [Output("stop-button", "buttonText"), Output("graph-update", "disabled")],
    [Input("stop-button", "n_clicks")],
    [State("graph-update", "disabled")],
)
def update_start_stream(n_clicks, status):
    print("came once")
    print("clicks is", n_clicks)
    if n_clicks > 0:
        if int(n_clicks) % 2 == 0:
            return "start", True
        else:
            return "stop", not True
    return "start", True

# ========================== Call back for elevator dataload and  ===================#
#Output('intermediate-value', 'children')
#sample_filt.to_json(date_format='iso', orient='split'
@app.callback(
    [Output('dd-output-container', 'children'), Output('elevator-id', 'value')],
    [Input('dropdown', 'value')])
def update_output(value):
    #if value > 0
    print("value is",value)
    #sample_filt = sample[sample['id'] == str(int(value))]
    #print(sample_filt.head())
    return 'You have selected Elevator {}'.format(int(value)), value


# ==========================Call back for graph update===================#
# LSTM based modification. Here.
idx = 6
previd = 1
ooc_trace = {
    "x": [],
    "y": [],
    "name": "Out of Control",
    "mode": "markers",
    "marker": dict(color="rgba(210, 77, 87, 0.7)", symbol="square", size=11),

}
trace = plotly.graph_objs.Scatter(
    x=[],
    y=[],
    name='Scatter',
    mode='lines+markers',
)
start = 0
end = 0
#sample = []

@app.callback(Output('live-graph', 'figure'),
              [Input('graph-update', 'n_intervals'), Input("stop-button", "n_clicks"),Input('dropdown', 'value')],
              [State("graph-update", "disabled")],
              )
def update_graph_scatter(n, clicks,value ,status):
    global idx, ooc_trace, trace, start, end,previd

    print("Value is", value)
    print("Previd is", previd)
    if value != previd:
      idx = 6 
      print("came inside change",idx, int(value))		
      init = table.query(
        KeyConditionExpression=Key('id').eq(int(value)) & Key('index').eq(idx) 
        )
      X.clear()
      Y.clear()
      for k in init['Items']:
        print(k["time"])
        X.append(k["time"])
        Y.append(0)

    response = table.query(
    KeyConditionExpression=Key('id').eq(int(value)) & Key('index').between(idx,idx+26) 
    )
        
    if not status:
        for i in response['Items']:
           print(i["index"],i['accel'],i["time"])
           X.append(i["time"])
           Y.append(i["accel"])
           if i['label'] > 0:
                ooc_trace["x"].append(i["time"])
                ooc_trace["y"].append(i["accel"])
           idx += 1

        trace = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode='lines+markers',
            marker_color='gold',
            line_color='gold',
        )
        start = X[0]
        end = X[-1]
        previd = value
        #print("prev id is", previd)

    return {
        'data': [trace, ooc_trace],
        'layout': go.Layout(
            legend={"font": {"color": "darkgray"}, "orientation": "h", "x": 0, "y": 1.1},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            xaxis=dict(showline=True, showgrid=True, zeroline=True, range=[start, end], title='Timestamp',
                       color='gold'),
            yaxis=dict(showgrid=True, showline=True, zeroline=True, range=[-10, 10], title='Vertical value',
                       color='gold'),
        )
    }



if __name__ == '__main__':
    app.run(debug=true)
