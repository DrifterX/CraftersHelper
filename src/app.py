from gevent import monkey
monkey.patch_all()
from dash import html, dcc ,Dash, ctx
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from dash import dash_table as dt

import environment
import functions as f
itemsDataLocation = environment.itemsDataLocation

app = Dash(title= "Crafter\'s Helper")

servers = f.getServerList(keys=False)
datacenters = []

for x in servers.keys():
    datacenters.append(x)
    
allItems = f.getDataFrameCsv(itemsDataLocation)
allItemNames = allItems['Name']

app.layout = html.Div([

    html.Title(['Crafter\'s toolbox']),

    html.Colgroup([
        html.Div([
            html.H4("Select Data Center and Server"),
            dcc.Dropdown(datacenters, 'Aether', id="dataCenterSelected"),
            dcc.Dropdown(id="serverList", placeholder="Select server")
        ], style={"width": "75%"}),
        html.Div([
            html.H3("Enter item names here."),
            dcc.Dropdown(allItemNames, id="itemList", placeholder= "Enter items you wish to search", value="", multi=True),
        ], style={"width": "75%"}),
        html.Div([
            html.H3("Hours per data segment"),
            dcc.Input(id="numOfHours", type="number", value=12),
            html.H3("Show material costs"),
            dcc.RadioItems(
                ["Yes", "No"],
                "Yes",
                id="includeMats",
                inline=True
            ),
            html.H3("Show sales volume"),
            dcc.RadioItems(
                ["Yes", "No"],
                "Yes",
                id="includeSales",
                inline=True
            ),
            html.H3("Show only HQ sales"),
            dcc.RadioItems(
                ["Yes", "No"],
                "Yes",
                id="onlyHQ",
                inline=True
            )
        ]),
        html.Div([
            html.Br(),
            html.Button("Display Results", id = 'displayButton')
        ])
    ], style={'width' : '20%', 'display' : 'inline-block', 'valign' : 'top','span' : 1}),

    html.Colgroup(children=[
        dcc.Graph(
            id='outputGraph'
        ),
        html.H2("Number of days to retrieve:"),
        dcc.Slider(
                1,
                42,
                step=1,
                marks={7:"7",14:"14",21:"21",28:"28", 35: "35", 42: "42"},
                value=7,
                id="daysSlider"
        )
    ], style={'width' : '75%', 'display' : 'inline-block', 'span' : 1, 'padding' : '2px'}),

    html.Div([
        html.Br(),
        html.Div([
            dt.DataTable(id="infoTable"),
            html.Br(),
            dt.DataTable(id="recipeTableRaw", 
                         style_data_conditional=[{
                            'if' : {
                                'filter_query' : '{numNeeded} = 0'
                            },
                            'backgroundColor' : 'darkblue',
                            'color' : 'white'
                         }]),
            html.Br(),
            dt.DataTable(id="recipeTable",
                         style_data_conditional=[{
                            'if' : {
                                'filter_query' : '{numNeeded} = 0'
                            },
                            'backgroundColor' : 'darkblue',
                            'color' : 'white'
                         }])

        ], style={'width' : '100%'})
    ])
 
], style={'padding': '2px 2px'})

@app.callback(
    Output('outputGraph', 'figure'),
    Output('displayButton', 'n_clicks'),
    Output('infoTable', 'data'),
    Output('recipeTableRaw', 'data'),
    Output('recipeTable', 'data'),
    Input('itemList', 'value'),
    Input('numOfHours', 'value'),
    Input('daysSlider', 'value'),
    Input('includeMats', 'value'),
    Input('includeSales', 'value'),
    Input('onlyHQ', 'value'),
    Input('displayButton', 'n_clicks'),
    Input('dataCenterSelected', 'value'),
    Input('serverList', 'value')
)

def uponClick(itemList, numOfHours, daysSlider, includeMats, includeSales, onlyHQ, n_clicks, dataCenterSelected, serverList):
    if n_clicks is None: raise PreventUpdate
    

    if includeMats == "Yes": showMaterials = True
    else: showMaterials = False
    if includeSales == "Yes": showSales = True
    else: showSales = False
    if onlyHQ == "Yes": onlyReturnHQ = True
    else: onlyReturnHQ = False
    if serverList is None: returnServer = dataCenterSelected
    else: returnServer = serverList
    
    matDFListRaw = []
    matDFList = []
    itemDFList = []
    totalResults = []
    weeksSlider = daysSlider / 7
    i = 1
    for name in itemList:
        thisListDF = f.fetchSalesData(name, hqOnly= onlyReturnHQ, numOfWeeks= weeksSlider, datacenter = returnServer)
        totalResults.append(len(thisListDF))
        itemDFList.append(thisListDF)
        if thisListDF['isCrafted'][0] == 1 and showMaterials == True:
            thisListMatDFRaw = f.fetchSalesDataRecipe(name, numOfWeeks=weeksSlider, datacenter = returnServer)
            matDFListRaw.append(thisListMatDFRaw)
            thisListMatDF = f.fetchSalesDataRecipe(name, numOfWeeks= weeksSlider, datacenter= returnServer, rawMatsOnly= False)
            matDFList.append(thisListMatDF)
        i = i + 1
    
    fig = f.buildLineGraph(itemDFList, matDFListRaw, matDFList, numOfHours, weeksSlider, showMaterials, showSales)
    infoTable = f.updateInfoTable(itemDFList, totalResults)
    recipeTableRaw = f.updateRecipeTable(matDFListRaw, itemList)
    recipeTable = f.updateRecipeTable(matDFList, itemList)
    
    return fig, None, infoTable, recipeTableRaw, recipeTable

@app.callback(
    Output('serverList', 'options'),
    Input('dataCenterSelected', 'value')
)

def populateServers(dataCenterSelected):

    if dataCenterSelected != None:
        return servers[dataCenterSelected]

app.run(host="0.0.0.0", port=8050)