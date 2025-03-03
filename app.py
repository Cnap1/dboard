from dash import Dash, dash_table, html, dcc, Input, Output, State, callback
import pandas as pd
import dash.dash_table.FormatTemplate as FormatTemplate
import json
import plotly.express as px
from datetime import datetime, timedelta

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

# Load client data
try:
    df = pd.read_json('clients.json')
    df['address'] = df['address'].astype(str)
except Exception as e:
    print(f"Error reading JSON file: {e}")
    # Create empty DataFrame with expected columns
    df = pd.DataFrame(columns=['id', 'name', 'email', 'phone', 'company', 'paid', 'type', 'address'])

# Simple data for example tables
ssi_data = pd.DataFrame({
    'account_id': [1001, 1002, 1003],
    'account_name': ['Account A', 'Account B', 'Account C'],
    'status': ['Active', 'Pending', 'Inactive']
})

# Enhanced invoicing data with more rows and a follow-up action column
invoicing_data = pd.DataFrame({
    'invoice_id': [5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010],
    'client': ['Client X', 'Client Y', 'Client Z', 'Client A', 'Client B', 'Client C', 'Client D', 'Client E', 'Client F', 'Client G'],
    'amount': [1500, 2750, 900, 3200, 1800, 2450, 975, 5250, 1650, 3800],
    'status': ['Paid', 'Due', 'Overdue', 'Paid', 'Due', 'Overdue', 'Paid', 'Due', 'Overdue', 'Due'],
    'due_date': [(datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
                (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
                (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=25)).strftime('%Y-%m-%d'),
                (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'),
                (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')],
    'follow_up_action': ['None', 'Reminder', 'Call client', 'None', 'Email reminder', 'Legal notice', 'None', 'Check payment', 'Manager review', 'Reminder']
})

kyc_data = pd.DataFrame({
    'client_id': [101, 102, 103],
    'verification_status': ['Complete', 'Pending', 'Incomplete'],
    'risk_level': ['Low', 'Medium', 'High']
})

# Tab content functions
def create_client_content():
    return html.Div([
        html.Div([
            html.Button('Add Client', id='add-client-btn', n_clicks=0),
            html.Button('Save Changes', id='save-client-btn', n_clicks=0, style={'marginLeft': '10px'})
        ], style={'margin': '20px 0'}),
        
        html.Div(id='client-status-msg', style={'margin': '10px 0', 'color': 'green'}),
        
        dash_table.DataTable(
            id='client-table',
            columns=[{'name': col, 'id': col} for col in df.columns],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            selected_rows=[],
            page_action="native",
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ])

def create_wholesale_config_content():
    return html.Div([
        html.H3("Wholesale Configuration"),
        html.Div([
            html.Div([
                html.Label("Configuration Settings"),
                dcc.Dropdown(
                    id='wholesale-config-dropdown',
                    options=[
                        {'label': 'Pricing Model', 'value': 'pricing'},
                        {'label': 'Commission Rates', 'value': 'commission'},
                        {'label': 'Distribution Channels', 'value': 'distribution'}
                    ],
                    value='pricing'
                )
            ], style={'width': '50%', 'margin': '20px 0'})
        ]),
        html.Div(id='wholesale-config-content')
    ])

def create_ssi_content():
    return html.Div([
        html.H3("Standard Settlement Instructions"),
        dash_table.DataTable(
            id='ssi-table',
            columns=[{'name': col, 'id': col} for col in ssi_data.columns],
            data=ssi_data.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ])

def create_invoicing_content():
    # Calculate totals for each status for the pie chart
    status_totals = invoicing_data.groupby('status')['amount'].sum().reset_index()
    
    return html.Div([
        html.H3("Invoicing Dashboard"),
        
        # Action buttons
        html.Div([
            html.Button('Generate Invoices', id='generate-invoice-btn', n_clicks=0, 
                      style={'backgroundColor': '#2980b9', 'color': 'white', 'border': 'none', 'padding': '10px 15px', 'marginRight': '10px'}),
            html.Button('Send Reminders', id='send-reminder-btn', n_clicks=0, 
                      style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'padding': '10px 15px', 'marginRight': '10px'}),
            html.Button('Escalate Selected', id='escalate-invoice-btn', n_clicks=0, 
                      style={'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'padding': '10px 15px'})
        ], style={'margin': '20px 0'}),
        
        # Status message div
        html.Div(id='invoice-status-msg', style={'margin': '10px 0', 'color': 'green'}),
        
        # Layout with table and chart
        html.Div([
            # Left column - Table
            html.Div([
                dash_table.DataTable(
                    id='invoice-table',
                    columns=[
                        {'name': 'Invoice ID', 'id': 'invoice_id'},
                        {'name': 'Client', 'id': 'client'},
                        {'name': 'Amount', 'id': 'amount', 'type': 'numeric', 'format': FormatTemplate.money(0)},
                        {'name': 'Status', 'id': 'status'},
                        {'name': 'Due Date', 'id': 'due_date'},
                        {'name': 'Follow-up Action', 'id': 'follow_up_action', 'editable': True}
                    ],
                    data=invoicing_data.to_dict('records'),
                    editable=True,
                    filter_action="native",
                    sort_action="native",
                    row_selectable="multi",
                    selected_rows=[],
                    page_action="native",
                    page_size=6,
                    style_table={'overflowX': 'auto'},
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'status', 'filter_query': '{status} eq "Overdue"'},
                            'backgroundColor': '#FFCDD2',
                            'color': 'black'
                        },
                        {
                            'if': {'column_id': 'status', 'filter_query': '{status} eq "Paid"'},
                            'backgroundColor': '#C8E6C9',
                            'color': 'black'
                        },
                        {
                            'if': {'column_id': 'status', 'filter_query': '{status} eq "Due"'},
                            'backgroundColor': '#FFF9C4',
                            'color': 'black'
                        }
                    ]
                )
            ], style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Right column - Charts
            html.Div([
                dcc.Graph(
                    id='invoice-pie-chart',
                    figure=px.pie(
                        status_totals, 
                        values='amount', 
                        names='status',
                        title='Invoice Amounts by Status',
                        color='status',
                        color_discrete_map={
                            'Paid': '#66BB6A',
                            'Due': '#FFEE58',
                            'Overdue': '#EF5350'
                        }
                    ).update_layout(
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", y=-0.1)
                    )
                ),
                
                # Bar chart showing invoice amounts by client
                dcc.Graph(
                    id='invoice-bar-chart',
                    figure=px.bar(
                        invoicing_data, 
                        x='client', 
                        y='amount',
                        color='status',
                        title='Invoice Amounts by Client',
                        color_discrete_map={
                            'Paid': '#66BB6A',
                            'Due': '#FFEE58',
                            'Overdue': '#EF5350'
                        }
                    ).update_layout(
                        margin=dict(l=20, r=20, t=40, b=80),
                        xaxis_tickangle=-45
                    )
                )
            ], style={'width': '40%', 'display': 'inline-block', 'paddingLeft': '20px'})
        ]),
        
        # Summary statistics
        html.Div([
            html.H4("Invoice Summary"),
            html.Div([
                html.Div([
                    html.Div("Total Outstanding", style={'fontWeight': 'bold'}),
                    html.Div(f"${invoicing_data[invoicing_data['status'] != 'Paid']['amount'].sum():,.2f}")
                ], style={'width': '25%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '5px'}),
                
                html.Div([
                    html.Div("Overdue Amount", style={'fontWeight': 'bold'}),
                    html.Div(f"${invoicing_data[invoicing_data['status'] == 'Overdue']['amount'].sum():,.2f}")
                ], style={'width': '25%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#FFCDD2', 'padding': '15px', 'borderRadius': '5px', 'margin': '0 10px'}),
                
                html.Div([
                    html.Div("Due Soon", style={'fontWeight': 'bold'}),
                    html.Div(f"${invoicing_data[invoicing_data['status'] == 'Due']['amount'].sum():,.2f}")
                ], style={'width': '25%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#FFF9C4', 'padding': '15px', 'borderRadius': '5px'}),
                
                html.Div([
                    html.Div("% Collected", style={'fontWeight': 'bold'}),
                    html.Div(f"{(invoicing_data[invoicing_data['status'] == 'Paid']['amount'].sum() / invoicing_data['amount'].sum() * 100):.1f}%")
                ], style={'width': '21%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#C8E6C9', 'padding': '15px', 'borderRadius': '5px', 'margin': '0 0 0 10px'})
            ], style={'margin': '15px 0'})
        ], style={'marginTop': '30px'})
    ])

def create_kyc_content():
    return html.Div([
        html.H3("Know Your Customer"),
        html.Div([
            html.Button('Request Documents', id='request-docs-btn', n_clicks=0),
            html.Button('Verify Client', id='verify-client-btn', n_clicks=0, style={'marginLeft': '10px'})
        ], style={'margin': '20px 0'}),
        dash_table.DataTable(
            id='kyc-table',
            columns=[{'name': col.replace('_', ' ').title(), 'id': col} for col in kyc_data.columns],
            data=kyc_data.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'risk_level', 'filter_query': '{risk_level} eq "High"'},
                    'backgroundColor': '#FFCDD2',
                    'color': 'black'
                },
                {
                    'if': {'column_id': 'verification_status', 'filter_query': '{verification_status} eq "Complete"'},
                    'backgroundColor': '#C8E6C9',
                    'color': 'black'
                }
            ]
        )
    ])

# App Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Financial Management Dashboard", style={'textAlign': 'center'})
    ], style={'backgroundColor': '#2c3e50', 'color': 'white', 'padding': '20px', 'marginBottom': '20px'}),
    
    # Tabs Container
    html.Div([
        dcc.Tabs(id='tabs', value='tab-client', children=[
            dcc.Tab(label='Clients', value='tab-client'),
            dcc.Tab(label='Wholesale Config', value='tab-wholesale'),
            dcc.Tab(label='SSI', value='tab-ssi'),
            dcc.Tab(label='Invoicing', value='tab-invoicing'),
            dcc.Tab(label='KYC', value='tab-kyc'),
        ], style={
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '16px'
        }),
        
        # Tab content
        html.Div(id='tabs-content', style={'padding': '20px'})
    ], style={'maxWidth': '1200px', 'margin': '0 auto'}),
    
    # Status messages and hidden components
    html.Div(id='status-message', style={'display': 'none'}),
    dcc.Store(id='store-client-data'),
])

# Callback to render tab content
@callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_tab_content(tab):
    if tab == 'tab-client':
        return create_client_content()
    elif tab == 'tab-wholesale':
        return create_wholesale_config_content()
    elif tab == 'tab-ssi':
        return create_ssi_content()
    elif tab == 'tab-invoicing':
        return create_invoicing_content()
    elif tab == 'tab-kyc':
        return create_kyc_content()
    return html.Div([
        html.H3("Content not found!")
    ])

# Callback for client management
@callback(
    Output('client-status-msg', 'children'),
    Input('save-client-btn', 'n_clicks'),
    State('client-table', 'data'),
    prevent_initial_call=True
)
def save_client_data(n_clicks, data):
    if n_clicks > 0:
        try:
            with open('clients.json', 'w') as f:
                json.dump(data, f, indent=2)
            return f"Client data saved successfully at {datetime.now().strftime('%H:%M:%S')}"
        except Exception as e:
            return f"Error saving client data: {str(e)}"
    return ""

@callback(
    Output('client-table', 'data'),
    Input('add-client-btn', 'n_clicks'),
    State('client-table', 'data'),
    State('client-table', 'columns'),
    prevent_initial_call=True
)
def add_client(n_clicks, rows, columns):
    if n_clicks > 0:
        # Create a new empty row
        new_row = {c['id']: '' for c in columns}
        
        # If the table has ID column, add a new ID
        if 'id' in new_row:
            # Find max ID and increment, or start at 1
            try:
                max_id = max([int(row.get('id', 0)) for row in rows if row.get('id', '')], default=0)
                new_row['id'] = max_id + 1
            except:
                new_row['id'] = 1
                
        rows.append(new_row)
    return rows

# Callback for invoice escalation
@callback(
    Output('invoice-status-msg', 'children'),
    Input('escalate-invoice-btn', 'n_clicks'),
    State('invoice-table', 'selected_rows'),
    State('invoice-table', 'data'),
    prevent_initial_call=True
)
def escalate_invoices(n_clicks, selected_rows, data):
    if n_clicks > 0 and selected_rows:
        # Get the selected invoices
        selected_invoices = [data[i]['invoice_id'] for i in selected_rows]
        
        # In a real application, this would trigger an escalation process
        # For this mockup, we'll just update the message
        return f"Escalated {len(selected_invoices)} invoices: {', '.join(map(str, selected_invoices))} at {datetime.now().strftime('%H:%M:%S')}"
    elif n_clicks > 0:
        return "No invoices selected for escalation"
    return ""

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
