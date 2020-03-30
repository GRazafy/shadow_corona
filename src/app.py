import datetime
import os
import yaml

import numpy as np
import pandas as pd

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output


# Lecture du fichier d'environnement
ENV_FILE = '../env.yaml'
with open(ENV_FILE) as f:
    params = yaml.load(f, Loader=yaml.FullLoader)

# Initialisation des chemins vers les fichiers
ROOT_DIR = os.path.dirname(os.path.abspath(ENV_FILE))
DATA_FILE = os.path.join(ROOT_DIR,
                         params['directories']['processed'],
                         params['files']['all_data'])

# Lecture du fichier de données
epidemie_df = (pd.read_csv(DATA_FILE, parse_dates=['Last Update'])
               .assign(day=lambda _df: _df['Last Update'].dt.date)
               .drop_duplicates(subset=['Country/Region', 'Province/State', 'day'])
               [lambda df: df['day'] <= datetime.date(2020, 3, 24)]
              )

countries = [{'label': c, 'value': c} for c in sorted(epidemie_df['Country/Region'].unique())]

app = dash.Dash('Corona Virus Explorer',external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    dcc.Interval(id='refresh', interval=200),
    html.H2(['Corona Virus Explorer'], style={'textAlign': 'center'}),
    html.Div([
        html.Div([
            html.Div([
                html.H4(
                    "Today Total: ",
                ),
                html.P(
                    id="Counter",
                ),
            ],
            className="count_container"
            ),
            html.Div([
                html.P(
                    "Filter by construction date (or select range in histogram):",
                    className="control_label",
                    ),
                dcc.DatePickerRange(
                    id = 'datepicker-input',
                    display_format='DD/MM/YYYY',
                ),
                dbc.RadioItems(
                    id='radioitems-input',
                    options=[
                            {'label': 'Confirmed', 'value': 'Confirmed'},
                            {'label': 'Deaths', 'value': 'Deaths'},
                            {'label': 'Recovered', 'value': 'Recovered'},
                            {'label': 'Active', 'value': 'Active'}
                        ],
                    value='Confirmed',
                ),
                html.P("Filter by countries :"),
                dcc.Dropdown(
                    id="countries",
                    options=countries,
                    multi=True,
                    className="dcc_control",
                ),
            ],
            className="option_container"
            ),
        ],
        className="side_container four columns",
        ),
        html.Div([
            dcc.Tabs([
                dcc.Tab(label='Time', children=[
                    html.Div([
                        dcc.Graph(id='graph1')
                    ]),   
                ]),
                dcc.Tab(label='Map', children=[
                    dcc.Graph(id='map1'),
                    dcc.Slider(
                        id='map_day',
                        min=0,
                        max=(epidemie_df['day'].max() - epidemie_df['day'].min()).days,
                        value=0,
                        updatemode='drag',
                        tooltip = { 
                            'always_visible': True
                        }
                    ),
                ]),
                #TODO change Dropdown to current countries
                dcc.Tab(label='Model',children=[
           		  html.H6(['The model']),
           		  dcc.Graph(id='graph2'),
          		  dcc.Dropdown(id='country3',options=countries)
                ]),
            ]),
        ],
        className="main_container eight columns",
        ),
    ],
    className="MainLayout",
    ),
])
@app.callback(Output("Counter", "children"),    
    [
        Input('radioitems-input', 'value'),
    ]
)
def update_statusBar(variable):
    return epidemie_df.groupby('day').agg({variable: 'sum'}).max()
@app.callback(
    Output('graph1', 'figure'),
    [
        Input('countries','value'),
        Input('radioitems-input', 'value'),        
    ]
)
def update_graph(countries, variable):
    graphs_df = []
    if countries != [] and type(countries) is list:
        for e_country in countries:
                graphs_df.append(epidemie_df[epidemie_df['Country/Region'] == e_country]
                    .groupby(['Country/Region', 'day'])
                    .agg({variable: 'sum'})
                    .reset_index()
                )
                print(graphs_df)
                   
    graph_df = epidemie_df.groupby('day').agg({variable: 'sum'}).reset_index()
    traces = []
    count = 0
    if countries != [] and type(countries) is list:
        for graph in graphs_df:
           traces.append(dict(
                x=graph['day'],
                y=graph[variable],
                type='line',
                name=countries[count]
           ))
           count = count+1
    else:
        traces.append(dict(
            x=graph_df['day'],
            y=graph_df[variable],
            type='line',
            name='Total'
        ))
    return {
        'data':traces
    }    


@app.callback(
    Output('map1', 'figure'),
    [
        Input('map_day', 'value'),
        Input('radioitems-input', 'value'),
    ]
)
def update_map(map_day,variable):
    day = epidemie_df['day'].unique()[map_day]
    map_df = (epidemie_df[epidemie_df['day'] == day]
              .groupby(['Combined_Key'])
              .agg({variable: 'sum', 'Latitude': 'mean', 'Longitude': 'mean'})
              .reset_index()
             )
    print(epidemie_df['Combined_Key'])
    return {
        'data': [
            dict(
                type='scattergeo',
                lon=map_df['Longitude'],
                lat=map_df['Latitude'],
                text=map_df.apply(lambda r: r['Combined_Key'] + ' (' + str(r[variable]) + ')', axis=1),
                mode='markers',
                marker=dict(
                    size=np.maximum(2*np.log(map_df[variable]), 5)
                )
            )
        ],
        'layout': dict(
            title=str(day),
            autosize=True,
            automargin=True,
            margin=dict(l=30, r=30, b=20, t=40),
            hovermode="closest",
            plot_bgcolor="#F9F9F9",
            paper_bgcolor="#F9F9F9",
            geo=dict(
                    showland = True,
                    landcolor = "rgb(212, 212, 212)",
                    subunitcolor = "rgb(255, 255, 255)",
                    countrycolor = "rgb(255, 255, 255)",
                    showlakes = True,
                    lakecolor = "rgb(255, 255, 255)",
                    showsubunits = True,
                    showcountries = True,
                    resolution = 50,
                    # lonaxis = dict(
                    #     showgrid = False,
                    #     gridwidth = 0.5,
                    #     range= [ -140.0, -55.0 ],
                    #     dtick = 5
                    # ),
                    # lataxis = dict (
                    #     showgrid = False,
                    #     gridwidth = 0.5,
                    #     range= [ 20.0, 60.0 ],
                    #     dtick = 5
                    # )
            )
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)