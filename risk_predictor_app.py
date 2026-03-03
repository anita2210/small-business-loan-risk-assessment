import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pickle
import pandas as pd
import numpy as np

# Load model
with open('models/trained_model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('models/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)
with open('models/feature_list.pkl', 'rb') as f:
    feature_list = pickle.load(f)

app = dash.Dash(__name__)
app.title = "SBA Loan Risk Predictor"

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .custom-input {
                width: 100% !important;
                padding: 0px 20px !important;
                font-size: 22px !important;
                font-weight: 700 !important;
                border: 3px solid #d1d5db !important;
                border-radius: 10px !important;
                box-sizing: border-box !important;
                font-family: 'Courier New', monospace !important;
                color: #1f2937 !important;
                letter-spacing: 1px !important;
            }
            .custom-input:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15) !important;
            }
            input[type=number]::-webkit-inner-spin-button,
            input[type=number]::-webkit-outer-spin-button {
                display: none !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

sectors = {
    '52': 'Finance & Insurance', '53': 'Real Estate', '48': 'Transportation',
    '72': 'Food Services', '44': 'Retail', '23': 'Construction',
    '54': 'Professional Services', '62': 'Healthcare',
    '31': 'Manufacturing', '81': 'Other Services'
}

states = ['CA', 'TX', 'FL', 'NY', 'IL', 'GA', 'DC', 'MD', 'VA', 'NJ', 
          'PA', 'OH', 'MI', 'NC', 'WA', 'AZ', 'MA', 'TN', 'CO', 'MO']

app.layout = html.Div(style={
    'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'minHeight': '100vh',
    'padding': '40px'
}, children=[
    
    html.Div(style={
        'maxWidth': '1000px',
        'margin': '0 auto',
        'backgroundColor': 'white',
        'borderRadius': '20px',
        'padding': '60px',
        'boxShadow': '0 20px 60px rgba(0,0,0,0.4)'
    }, children=[
        
        html.Div(style={'textAlign': 'center', 'marginBottom': '50px'}, children=[
            html.H1('🏦 SBA Loan Risk Predictor',
                    style={'fontSize': '46px', 'color': '#1f2937', 'marginBottom': '12px', 'fontWeight': 'bold'}),
            html.P('Machine Learning Model | 86.82% Accuracy | 94.79% ROC AUC',
                   style={'fontSize': '18px', 'color': '#6b7280', 'margin': '0'}),
            html.P('Enter loan details for instant risk assessment',
                   style={'fontSize': '15px', 'color': '#9ca3af', 'marginTop': '8px'})
        ]),
        
        html.Div(style={
            'backgroundColor': '#f9fafb',
            'padding': '45px',
            'borderRadius': '18px',
            'marginBottom': '40px',
            'border': '3px solid #e5e7eb'
        }, children=[
            
            html.H3('📋 Loan Information', style={'marginBottom': '35px', 'color': '#374151', 'fontSize': '24px'}),
            
            html.Div(style={'marginBottom': '30px'}, children=[
                html.Label('💰 Loan Amount ($)', 
                          style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                dcc.Input(id='loan-amount', type='number', value=150000, min=1000, step=1000, className='custom-input')
            ]),
            
            html.Div(style={'marginBottom': '30px'}, children=[
                html.Label('📅 Loan Term (months)', 
                          style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                dcc.Input(id='loan-term', type='number', value=120, min=12, max=360, step=12, className='custom-input')
            ]),
            
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '25px', 'marginBottom': '30px'}, children=[
                html.Div(children=[
                    html.Label('🏢 Industry Sector', 
                              style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                    dcc.Dropdown(id='sector', options=[{'label': v, 'value': k} for k, v in sectors.items()],
                                value='52', style={'fontSize': '16px'}, clearable=False)
                ]),
                html.Div(children=[
                    html.Label('🗺️ State', 
                              style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                    dcc.Dropdown(id='state', options=[{'label': s, 'value': s} for s in states],
                                value='CA', style={'fontSize': '16px'}, clearable=False)
                ])
            ]),
            
            html.Div(style={'marginBottom': '30px'}, children=[
                html.Label('👔 Business Type', 
                          style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                dcc.Dropdown(
                    id='business-type',
                    options=[
                        {'label': '✅ Established (>2 years)', 'value': 'established'},
                        {'label': '🟡 Recent (1-2 years)', 'value': 'recent'},
                        {'label': '🆕 New Startup', 'value': 'new'}
                    ],
                    value='established',
                    style={'fontSize': '16px'},
                    clearable=False
                )
            ]),
            
            html.Div(style={'marginBottom': '30px'}, children=[
                html.Label('👥 Employees', 
                          style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                dcc.Input(id='employees', type='number', value=10, min=1, className='custom-input')
            ]),
            
            html.Div(style={'marginBottom': '30px'}, children=[
                html.Label('💼 Jobs to Create', 
                          style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                dcc.Input(id='jobs', type='number', value=5, min=0, className='custom-input')
            ]),
            
            html.Div(style={'marginBottom': '30px'}, children=[
                html.Label('📍 Location', 
                          style={'fontWeight': '700', 'marginBottom': '12px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                dcc.Dropdown(
                    id='location',
                    options=[
                        {'label': '🏙️ Urban', 'value': 'urban'},
                        {'label': '🌾 Rural', 'value': 'rural'}
                    ],
                    value='urban',
                    style={'fontSize': '16px'},
                    clearable=False
                )
            ]),
            
            html.Div(style={'marginBottom': '35px'}, children=[
                html.Label('Additional Features:', 
                          style={'fontWeight': '700', 'marginBottom': '15px', 'display': 'block', 'color': '#374151', 'fontSize': '17px'}),
                dcc.Checklist(
                    id='loan-flags',
                    options=[
                        {'label': ' Revolving Line of Credit', 'value': 'revline'},
                        {'label': ' Low Documentation', 'value': 'lowdoc'},
                        {'label': ' Franchise', 'value': 'franchise'}
                    ],
                    value=[],
                    labelStyle={'display': 'block', 'marginBottom': '12px', 'fontSize': '16px'}
                )
            ]),
            
            html.Div(style={'textAlign': 'center'}, children=[
                html.Button('🔮 PREDICT RISK SCORE',
                           id='predict-btn',
                           n_clicks=0,
                           style={
                               'background': 'linear-gradient(135deg, #667eea, #764ba2)',
                               'color': 'white',
                               'border': 'none',
                               'padding': '20px 60px',
                               'fontSize': '20px',
                               'fontWeight': 'bold',
                               'borderRadius': '14px',
                               'cursor': 'pointer',
                               'boxShadow': '0 10px 25px rgba(102,126,234,0.5)'
                           })
            ])
        ]),
        
        html.Div(id='prediction-results')
    ]),
    
    html.Div(style={'textAlign': 'center', 'marginTop': '40px', 'color': 'white'}, children=[
        html.P('🚀 ML-Powered Risk Assessment | Anita Chelladurai',
               style={'fontSize': '15px', 'opacity': '0.95'})
    ])
])

@app.callback(
    Output('prediction-results', 'children'),
    Input('predict-btn', 'n_clicks'),
    [State('loan-amount', 'value'),
     State('loan-term', 'value'),
     State('sector', 'value'),
     State('state', 'value'),
     State('business-type', 'value'),
     State('employees', 'value'),
     State('jobs', 'value'),
     State('location', 'value'),
     State('loan-flags', 'value')],
    prevent_initial_call=True
)
def predict_risk(n_clicks, amount, term, sector, state, biz_type, employees, jobs, location, flags):
    
    # FIX: Proper conversion - handle None and empty values
    if amount is None or amount == '':
        amount = 0
    else:
        amount = float(amount)
    
    if term is None or term == '':
        term = 0
    else:
        term = int(term)
    
    if employees is None or employees == '':
        employees = 0
    else:
        employees = int(employees)
    
    if jobs is None or jobs == '':
        jobs = 0
    else:
        jobs = int(jobs)
    
    print(f"DEBUG: amount={amount}, term={term}, employees={employees}, jobs={jobs}")  # Debug output
    
    features_dict = {
        'amount': amount,
        'term_val': term,
        'employees': employees,
        'jobs_created': jobs,
        'jobs_retained': 0,
        'is_new': 1 if biz_type == 'new' else 0,
        'is_established': 1 if biz_type == 'established' else 0,
        'is_recent': 1 if biz_type == 'recent' else 0,
        'urban': 1 if location == 'urban' else 0,
        'rural': 1 if location == 'rural' else 0,
        'has_revline': 1 if flags and 'revline' in flags else 0,
        'is_lowdoc': 1 if flags and 'lowdoc' in flags else 0,
        'is_franchise': 1 if flags and 'franchise' in flags else 0,
        'sector_high_risk': 1 if sector in ['52', '53', '48', '51', '56'] else 0,
        'sector_medium_risk': 1 if sector in ['49', '23', '45', '61'] else 0,
        'sector_num': float(sector),
        'state_high_risk': 1 if state in ['DC', 'FL', 'GA', 'NV', 'MD'] else 0,
        'state_medium_risk': 1 if state in ['IL', 'NY', 'WV', 'MI', 'OH'] else 0,
        'state_low_risk': 1 if state in ['TX', 'LA', 'SC', 'IA', 'NE'] else 0,
        'small_loan': 1 if amount < 50000 else 0,
        'medium_loan': 1 if 50000 <= amount < 250000 else 0,
        'large_loan': 1 if amount >= 250000 else 0,
        'short_term': 1 if term < 120 else 0,
        'long_term': 1 if term >= 240 else 0,
        'amount_per_employee': amount / employees if employees > 0 else amount,
        'amount_per_job_created': amount / jobs if jobs > 0 else amount,
        'double_risk': 1 if (sector in ['52', '53', '48'] and state in ['DC', 'FL', 'GA']) else 0,
        'triple_risk': 1 if (biz_type == 'new' and sector in ['52', '53', '48'] and state in ['DC', 'FL', 'GA']) else 0
    }
    
    input_df = pd.DataFrame([features_dict])[feature_list]
    
    try:
        risk_probability = model.predict_proba(input_df)[0][1] * 100
    except:
        input_scaled = scaler.transform(input_df)
        risk_probability = model.predict_proba(input_scaled)[0][1] * 100
    
    if risk_probability < 15:
        risk_level = "🟢 LOW RISK"
        risk_color = "#10b981"
        recommendation = "✅ APPROVE - Low risk with standard terms"
        bg_color = "#d1fae5"
    elif risk_probability < 25:
        risk_level = "🟡 MEDIUM RISK"
        risk_color = "#f59e0b"
        recommendation = "⚠️ APPROVE - Monitor closely"
        bg_color = "#fef3c7"
    elif risk_probability < 40:
        risk_level = "🟠 ELEVATED RISK"
        risk_color = "#f97316"
        recommendation = "⚠️ CONDITIONAL - Require collateral"
        bg_color = "#fed7aa"
    else:
        risk_level = "🔴 HIGH RISK"
        risk_color = "#ef4444"
        recommendation = "❌ REJECT - Too risky"
        bg_color = "#fee2e2"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_probability,
        title={'text': "<b>Default Risk Probability</b>", 'font': {'size': 26}},
        number={'suffix': '%', 'font': {'size': 70, 'color': risk_color}},
        gauge={
            'axis': {'range': [0, 100], 'ticksuffix': '%'},
            'bar': {'color': risk_color},
            'steps': [
                {'range': [0, 15], 'color': "#d1fae5"},
                {'range': [15, 25], 'color': "#fef3c7"},
                {'range': [25, 40], 'color': "#fed7aa"},
                {'range': [40, 100], 'color': "#fee2e2"}
            ]
        }
    ))
    fig.update_layout(height=400, margin=dict(t=90, b=50))
    
    return html.Div([
        html.Div(style={
            'backgroundColor': bg_color,
            'padding': '40px',
            'borderRadius': '18px',
            'border': f'4px solid {risk_color}',
            'marginBottom': '30px',
            'boxShadow': f'0 10px 30px {risk_color}50'
        }, children=[
            html.H2('📊 Risk Assessment Results', 
                   style={'marginBottom': '25px', 'color': '#1f2937', 'fontSize': '30px', 'textAlign': 'center'}),
            
            html.Div(style={'display': 'flex', 'gap': '25px', 'marginBottom': '25px'}, children=[
                html.Div(style={'flex': '1', 'textAlign': 'center', 'padding': '30px',
                               'backgroundColor': 'white', 'borderRadius': '14px',
                               'boxShadow': '0 6px 16px rgba(0,0,0,0.12)'}, children=[
                    html.H4('Default Risk', style={'color': '#6b7280', 'fontSize': '16px', 'marginBottom': '12px'}),
                    html.H2(f'{risk_probability:.1f}%', 
                           style={'color': risk_color, 'fontSize': '50px', 'margin': '0', 'fontWeight': 'bold'})
                ]),
                html.Div(style={'flex': '1', 'textAlign': 'center', 'padding': '30px',
                               'backgroundColor': 'white', 'borderRadius': '14px',
                               'boxShadow': '0 6px 16px rgba(0,0,0,0.12)'}, children=[
                    html.H4('Risk Category', style={'color': '#6b7280', 'fontSize': '16px', 'marginBottom': '12px'}),
                    html.H2(risk_level, style={'fontSize': '28px', 'margin': '0', 'fontWeight': 'bold'})
                ])
            ]),
            
            html.Div(style={'backgroundColor': 'white', 'padding': '28px', 'borderRadius': '14px',
                           'boxShadow': '0 6px 16px rgba(0,0,0,0.12)'}, children=[
                html.H4('💡 Lending Recommendation:', 
                       style={'marginBottom': '14px', 'color': '#374151', 'fontSize': '19px'}),
                html.P(recommendation, 
                      style={'fontSize': '20px', 'fontWeight': '700', 'color': risk_color, 
                            'margin': '0', 'lineHeight': '1.5'})
            ])
        ]),
        
        html.Div(style={'backgroundColor': 'white', 'padding': '30px', 'borderRadius': '18px',
                       'boxShadow': '0 6px 20px rgba(0,0,0,0.15)', 'marginBottom': '30px'}, children=[
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ]),
        
        html.Div(style={'padding': '35px', 'backgroundColor': '#f9fafb', 'borderRadius': '16px',
                       'border': '2px solid #e5e7eb'}, children=[
            html.H4('⚠️ Input Summary:', 
                   style={'marginBottom': '20px', 'color': '#374151', 'fontSize': '20px', 'fontWeight': 'bold'}),
            html.Div(style={'display': 'grid', 'gap': '12px'}, children=[
                html.Div(style={'padding': '16px 20px', 'backgroundColor': 'white', 'borderRadius': '8px',
                               'borderLeft': '4px solid #667eea', 'fontSize': '16px'}, children=[
                    html.Strong('💰 Loan Amount: '), f'${amount:,}'
                ]),
                html.Div(style={'padding': '16px 20px', 'backgroundColor': 'white', 'borderRadius': '8px',
                               'borderLeft': '4px solid #667eea', 'fontSize': '16px'}, children=[
                    html.Strong('📅 Term: '), f'{term} months'
                ]),
                html.Div(style={'padding': '16px 20px', 'backgroundColor': 'white', 'borderRadius': '8px',
                               'borderLeft': '4px solid #667eea', 'fontSize': '16px'}, children=[
                    html.Strong('🏢 Sector: '), sectors.get(sector, 'Unknown'),
                    html.Span(' 🔴 High Risk' if sector in ['52','53','48'] else ' ✅ Lower Risk',
                             style={'float': 'right', 'fontWeight': 'bold'})
                ]),
                html.Div(style={'padding': '16px 20px', 'backgroundColor': 'white', 'borderRadius': '8px',
                               'borderLeft': '4px solid #667eea', 'fontSize': '16px'}, children=[
                    html.Strong('🗺️ State: '), state,
                    html.Span(' 🔴 High Risk' if state in ['DC','FL','GA'] else ' ✅ Lower Risk',
                             style={'float': 'right', 'fontWeight': 'bold'})
                ]),
                html.Div(style={'padding': '16px 20px', 'backgroundColor': 'white', 'borderRadius': '8px',
                               'borderLeft': '4px solid #667eea', 'fontSize': '16px'}, children=[
                    html.Strong('👔 Business: '), biz_type.title(),
                    html.Span(' 🔴 New' if biz_type=='new' else ' ✅ Established' if biz_type=='established' else ' 🟡 Recent',
                             style={'float': 'right', 'fontWeight': 'bold'})
                ])
            ])
        ]),
        
        html.Div(style={'marginTop': '30px', 'padding': '25px', 
                       'backgroundColor': 'rgba(102, 126, 234, 0.12)',
                       'borderRadius': '12px', 'border': '2px solid rgba(102, 126, 234, 0.3)'}, children=[
            html.P([
                html.Strong('ℹ️ Model Info: '),
                'Random Forest trained on 100,000 loans. Accuracy: 86.82% | ROC AUC: 94.79%'
            ], style={'margin': '0', 'fontSize': '14px', 'color': '#475569'})
        ])
    ])
server = app.server
if __name__ == '__main__':
    app.run(debug=True, port=8051)