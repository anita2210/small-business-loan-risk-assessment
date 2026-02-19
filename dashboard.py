import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.graph_objects as go
import pandas as pd
import base64

# Load data
overall_stats = pd.read_csv('data/overall_stats.csv')
sector_risk = pd.read_csv('data/sector_risk.csv')
state_risk = pd.read_csv('data/state_risk.csv')
business_maturity = pd.read_csv('data/business_maturity.csv')
loans_full = pd.read_csv('data/loans_sample.csv')

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Sector mapping
sector_names = {
    '52': 'Finance & Insurance', '53': 'Real Estate', '48': 'Transportation',
    '51': 'Information', '56': 'Admin Services', '49': 'Warehousing',
    '23': 'Construction', '45': 'Retail', '44': 'Retail Stores',
    '72': 'Food Services', '42': 'Wholesale', '71': 'Arts',
    '31': 'Manufacturing', '81': 'Other Services', '54': 'Professional',
    '62': 'Healthcare', '61': 'Education', '11': 'Agriculture'
}

sector_risk['industry_name'] = sector_risk['industry_sector'].astype(str).map(sector_names).fillna('Other')
sector_risk['sector_code'] = sector_risk['industry_sector'].astype(str)

# Prepare loans
loans_full['sector_2digit'] = loans_full['naics'].astype(str).str[:2]
loans_full['industry_name'] = loans_full['sector_2digit'].map(sector_names).fillna('Other')
loans_full['is_default'] = loans_full['chgoffdate'].apply(
    lambda x: False if (pd.isna(x) or x == 'N' or x == '' or str(x).strip() == '') else True
)

# Stats
total_loans = int(overall_stats['total_loans'].iloc[0])
default_rate = float(overall_stats['default_rate_percent'].iloc[0])
defaulted = int(overall_stats['defaulted_loans'].iloc[0])
paid = int(overall_stats['paid_loans'].iloc[0])

# Background
# Background
try:
    with open('background.png', 'rb') as f:
        bg_image = f'data:image/png;base64,{base64.b64encode(f.read()).decode()}'
except:
    bg_image = ''

# LAYOUT
app.layout = html.Div([
    dcc.Store(id='nav-state', data={'page': 'main', 'detail': None}),
    html.Div(id='app-content', style={
        'backgroundImage': f'linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url({bg_image})' if bg_image else 'linear-gradient(135deg, #1e1b4b, #312e81)',
        'backgroundSize': 'cover',
        'backgroundAttachment': 'fixed',
        'minHeight': '100vh',
        'padding': '40px'
    })
])

# MAIN CALLBACK
@app.callback(
    Output('app-content', 'children'),
    Input('nav-state', 'data')
)
def render_content(nav_state):
    page = nav_state.get('page', 'main')
    detail = nav_state.get('detail')
    
    if page == 'sector-detail' and detail:
        return build_sector_page(detail)
    elif page == 'state-detail' and detail:
        return build_state_page(detail)
    elif page == 'maturity-detail' and detail:
        return build_maturity_page(detail)
    else:
        return build_main_page()

# NAVIGATION CALLBACK
@app.callback(
    Output('nav-state', 'data'),
    [Input({'type': 'sector-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'state-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'maturity-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'back-btn', 'index': ALL}, 'n_clicks')],
    State('nav-state', 'data'),
    prevent_initial_call=True
)
def navigate(sector_clicks, state_clicks, mat_clicks, back_clicks, current_state):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_state
    
    trigger = ctx.triggered[0]['prop_id']
    
    if 'back-btn' in trigger:
        return {'page': 'main', 'detail': None}
    elif 'sector-btn' in trigger and sector_clicks:
        clicked_idx = next((i for i, c in enumerate(sector_clicks) if c and c > 0), None)
        if clicked_idx is not None:
            sector_data = sector_risk.iloc[clicked_idx]
            return {'page': 'sector-detail', 'detail': {
                'code': sector_data['sector_code'],
                'name': sector_data['industry_name']
            }}
    elif 'state-btn' in trigger and state_clicks:
        clicked_idx = next((i for i, c in enumerate(state_clicks) if c and c > 0), None)
        if clicked_idx is not None:
            state_data = state_risk.iloc[clicked_idx]
            return {'page': 'state-detail', 'detail': {'code': state_data['state']}}
    elif 'maturity-btn' in trigger and mat_clicks:
        clicked_idx = next((i for i, c in enumerate(mat_clicks) if c and c > 0), None)
        if clicked_idx is not None:
            mat_data = business_maturity.iloc[clicked_idx]
            return {'page': 'maturity-detail', 'detail': {'type': mat_data['business_type']}}
    
    return current_state

# MAIN PAGE
def build_main_page():
    box = {
        'backgroundColor': 'rgba(255,255,255,0.97)',
        'borderRadius': '16px',
        'padding': '38px',
        'boxShadow': '0 10px 40px rgba(0,0,0,0.3)',
        'marginBottom': '28px',
        'backdropFilter': 'blur(10px)'
    }
    
    # Gauge - Purple theme
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=default_rate,
        title={'text': "<b>Default Rate</b>", 'font': {'size': 26, 'color': '#1e1b4b'}},
        number={'suffix': '%', 'font': {'size': 60, 'color': '#7c3aed'}},
        gauge={'axis': {'range': [0, 30], 'ticksuffix': '%'},
               'bar': {'color': "#7c3aed"},
               'steps': [{'range': [0, 10], 'color': "#e0e7ff"},
                        {'range': [10, 20], 'color': "#ddd6fe"},
                        {'range': [20, 30], 'color': "#fae8ff"}]}
    ))
    fig_gauge.update_layout(height=400, margin=dict(t=80))
    
    # Pie - Purple/Teal theme
    fig_pie = go.Figure(go.Pie(
        labels=['Paid', 'Defaulted'], values=[paid, defaulted],
        marker=dict(colors=['#14b8a6', '#a855f7'], line=dict(width=4, color='white')),
        hole=0.45, textinfo='label+percent', textfont=dict(size=17, family='Arial', color='#1e1b4b')
    ))
    fig_pie.update_layout(title="<b>Portfolio Status</b>", height=400, showlegend=False)
    
    # Sector bars - Purple to Teal gradient (20 distinct colors)
    sector_top = sector_risk.head(20)
    max_rate = sector_top['default_rate_percent'].max()
    colors = [
        '#7c3aed', '#8b5cf6', '#9333ea', '#a855f7', '#c084fc',
        '#d8b4fe', '#e879f9', '#f0abfc', '#f9a8d4', '#fbcfe8',
        '#fda4af', '#fb7185', '#f472b6', '#ec4899', '#db2777',
        '#be185d', '#9f1239', '#881337', '#701a75', '#581c87'
    ]
    
    sector_items = []
    for i, (_, row) in enumerate(sector_top.iterrows()):
        width_pct = (row['default_rate_percent'] / max_rate) * 100
        sector_items.append(
            html.Div(style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px', 'gap': '18px'}, children=[
                html.Div(style={'width': '200px', 'fontWeight': '600', 'fontSize': '14px', 'color': '#1e1b4b'}, 
                        children=[row['industry_name']]),
                html.Div(style={
                    'height': '38px',
                    'background': f'linear-gradient(90deg, {colors[i]}, {colors[i]}dd)',
                    'borderRadius': '10px',
                    'width': f'{width_pct}%',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'flex-end',
                    'paddingRight': '14px',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'fontSize': '15px',
                    'boxShadow': f'0 4px 12px {colors[i]}55'
                }, children=[f"{row['default_rate_percent']:.1f}%"]),
                html.Button('View →', 
                           id={'type': 'sector-btn', 'index': i},
                           n_clicks=0,
                           style={'background': 'linear-gradient(135deg, #4f46e5, #6366f1)',
                                 'color': 'white', 'border': 'none',
                                 'padding': '11px 24px', 'borderRadius': '10px', 'cursor': 'pointer',
                                 'fontWeight': '600', 'fontSize': '13px', 'whiteSpace': 'nowrap',
                                 'boxShadow': '0 4px 12px rgba(79,70,229,0.4)',
                                 'transition': 'all 0.3s'})
            ])
        )
    
    # States - Teal gradient
    state_top = state_risk.head(20)
    state_colors = []
    for r in state_top['default_rate_percent']:
        if r > 27: state_colors.append('#7c2d12')
        elif r > 25: state_colors.append('#9a3412')
        elif r > 23: state_colors.append('#c2410c')
        elif r > 21: state_colors.append('#ea580c')
        elif r > 19: state_colors.append('#0891b2')
        else: state_colors.append('#0e7490')
    
    fig_states = go.Figure(go.Bar(
        x=state_top['state'],
        y=state_top['default_rate_percent'],
        marker=dict(color=state_colors, line=dict(color='rgba(255,255,255,0.3)', width=2)),
        text=state_top['default_rate_percent'].round(1).astype(str) + '%',
        textposition='outside',
        textfont=dict(size=16, family='Arial', color='#1e293b')
    ))
    fig_states.update_layout(
        title="<b>🗺️ Geographic Risk by State</b>",
        xaxis_title="State",
        yaxis_title="Default Rate (%)",
        height=560,
        plot_bgcolor='rgba(248,250,252,0.5)',
        paper_bgcolor='rgba(255,255,255,0.9)',
        margin=dict(t=80, b=90),
        yaxis=dict(range=[0, max(state_top['default_rate_percent']) * 1.15], gridcolor='rgba(148,163,184,0.2)'),
        xaxis=dict(tickfont=dict(size=14))
    )
    
    state_items = []
    for i, (_, row) in enumerate(state_top.iterrows()):
        state_items.append(
            html.Button(
                f"{row['state']}: {row['default_rate_percent']:.1f}%",
                id={'type': 'state-btn', 'index': i},
                n_clicks=0,
                style={
                    'background': f'linear-gradient(135deg, {state_colors[i]}, {state_colors[i]}dd)',
                    'color': 'white',
                    'border': 'none',
                    'padding': '16px 30px',
                    'margin': '8px',
                    'borderRadius': '12px',
                    'cursor': 'pointer',
                    'fontWeight': '600',
                    'fontSize': '15px',
                    'boxShadow': f'0 6px 16px {state_colors[i]}50',
                    'display': 'inline-block',
                    'minWidth': '155px',
                    'transition': 'transform 0.2s'
                }
            )
        )
    
    # Maturity - Coordinated purple theme
    colors_mat = {
        'Established': '#14b8a6',  # Teal
        'Recent': '#8b5cf6',       # Purple
        'New': '#ec4899',          # Pink
        'Other': '#64748b'         # Slate
    }
    
    fig_mat_compare = go.Figure()
    for _, row in business_maturity.iterrows():
        fig_mat_compare.add_trace(go.Bar(
            x=[row['business_type']],
            y=[row['default_rate_percent']],
            marker=dict(
                color=colors_mat.get(row['business_type']),
                line=dict(color='rgba(255,255,255,0.5)', width=2)
            ),
            text=f"{row['default_rate_percent']:.1f}%",
            textposition='outside',
            textfont=dict(size=19, family='Arial', color='#1e293b'),
            width=0.65,
            showlegend=False
        ))
    
    fig_mat_compare.update_layout(
        title="<b>Default Rate by Maturity</b>",
        yaxis_title="Default Rate (%)",
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(248,250,252,0.5)',
        paper_bgcolor='rgba(255,255,255,0.9)',
        margin=dict(t=80, b=85),
        yaxis=dict(range=[0, max(business_maturity['default_rate_percent']) * 1.3], 
                  gridcolor='rgba(148,163,184,0.2)'),
        xaxis=dict(tickfont=dict(size=15))
    )
    
    fig_mat_donut = go.Figure(go.Pie(
        labels=business_maturity['business_type'],
        values=business_maturity['total_loans'],
        marker=dict(colors=[colors_mat.get(t) for t in business_maturity['business_type']], 
                   line=dict(width=5, color='white')),
        hole=0.52,
        textinfo='label+percent',
        textfont=dict(size=18, family='Arial', color='#1e293b')
    ))
    fig_mat_donut.update_layout(
        title="<b>Loan Distribution</b>",
        height=500,
        showlegend=False,
        paper_bgcolor='rgba(255,255,255,0.9)',
        margin=dict(t=80),
        annotations=[dict(text=f'<b>{total_loans:,}</b><br>Loans', x=0.5, y=0.5, 
                         font=dict(size=19, color='#475569'), showarrow=False)]
    )
    
    mat_buttons = []
    for i, (_, row) in enumerate(business_maturity.iterrows()):
        color = colors_mat.get(row['business_type'])
        mat_buttons.append(
            html.Div(style={'marginBottom': '16px', 'padding': '24px',
                           'background': 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95))',
                           'borderRadius': '14px',
                           'border': f"3px solid {color}",
                           'boxShadow': f'0 6px 18px {color}40'}, children=[
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, children=[
                    html.Div([
                        html.H4(row['business_type'], style={'margin': '0 0 10px 0', 'color': '#1e293b', 'fontSize': '18px'}),
                        html.P(f"Default: {row['default_rate_percent']:.1f}% | Loans: {row['total_loans']:,}",
                              style={'margin': '0', 'color': '#64748b', 'fontSize': '14px'})
                    ]),
                    html.Button('Explore →',
                               id={'type': 'maturity-btn', 'index': i},
                               n_clicks=0,
                               style={'background': f'linear-gradient(135deg, {color}, {color}dd)',
                                     'color': 'white', 'border': 'none', 'padding': '15px 32px',
                                     'borderRadius': '11px', 'cursor': 'pointer', 'fontWeight': '600',
                                     'fontSize': '15px', 'boxShadow': f'0 5px 14px {color}55',
                                     'transition': 'transform 0.2s'})
                ])
            ])
        )
    
    return html.Div([
        # Header
        html.Div(style={**box, 'textAlign': 'center', 'padding': '50px',
                       'background': 'linear-gradient(135deg, rgba(255,255,255,0.97), rgba(245,243,255,0.97))',
                       'border': '3px solid rgba(139,92,246,0.25)'}, children=[
            html.H1('🏦 SBA Loan Risk Assessment',
                    style={'fontSize': '50px', 'fontFamily': 'Arial Black', 'color': '#1e1b4b',
                          'marginBottom': '14px', 'letterSpacing': '-1px'}),
            html.H3(f'Interactive Dashboard | {total_loans:,} Loans Analyzed', 
                   style={'color': '#6366f1', 'fontSize': '23px', 'fontWeight': '500'})
        ]),
        
        # Metrics - Purple/Pink/Teal gradients
        html.Div(style={'display': 'flex', 'gap': '24px', 'marginBottom': '30px'}, children=[
            html.Div(style={'background': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                           'borderRadius': '16px', 'padding': '40px', 'flex': '1', 'textAlign': 'center',
                           'boxShadow': '0 10px 30px rgba(99,102,241,0.35)'}, children=[
                html.H4('💼 Total Loans', style={'color': 'rgba(255,255,255,0.95)', 'fontSize': '17px', 'marginBottom': '14px'}),
                html.H2(f'{total_loans:,}', style={'color': 'white', 'fontSize': '42px', 'margin': '0', 'fontWeight': 'bold'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #ec4899 0%, #d946ef 100%)',
                           'borderRadius': '16px', 'padding': '40px', 'flex': '1', 'textAlign': 'center',
                           'boxShadow': '0 10px 30px rgba(236,72,153,0.35)'}, children=[
                html.H4('⚠️ Default Rate', style={'color': 'rgba(255,255,255,0.95)', 'fontSize': '17px', 'marginBottom': '14px'}),
                html.H2(f'{default_rate}%', style={'color': 'white', 'fontSize': '42px', 'margin': '0', 'fontWeight': 'bold'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
                           'borderRadius': '16px', 'padding': '40px', 'flex': '1', 'textAlign': 'center',
                           'boxShadow': '0 10px 30px rgba(249,115,22,0.35)'}, children=[
                html.H4('❌ Defaulted', style={'color': 'rgba(255,255,255,0.95)', 'fontSize': '17px', 'marginBottom': '14px'}),
                html.H2(f'{defaulted:,}', style={'color': 'white', 'fontSize': '42px', 'margin': '0', 'fontWeight': 'bold'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
                           'borderRadius': '16px', 'padding': '40px', 'flex': '1', 'textAlign': 'center',
                           'boxShadow': '0 10px 30px rgba(20,184,166,0.35)'}, children=[
                html.H4('✅ Paid', style={'color': 'rgba(255,255,255,0.95)', 'fontSize': '17px', 'marginBottom': '14px'}),
                html.H2(f'{paid:,}', style={'color': 'white', 'fontSize': '42px', 'margin': '0', 'fontWeight': 'bold'})
            ]),
        ]),
        
        # Overview
        html.Div(style={'display': 'flex', 'gap': '30px', 'marginBottom': '30px'}, children=[
            html.Div(style={**box, 'flex': '1'}, children=[
                dcc.Graph(figure=fig_gauge, config={'displayModeBar': False})
            ]),
            html.Div(style={**box, 'flex': '1'}, children=[
                dcc.Graph(figure=fig_pie, config={'displayModeBar': False})
            ]),
        ]),
        
        # Sectors
        html.Div(style=box, children=[
            html.H2('🏢 Industry Sector Risk Analysis', 
                   style={'marginBottom': '30px', 'color': '#1e1b4b', 'fontSize': '30px', 'fontFamily': 'Arial Black'}),
            html.Div(children=sector_items)
        ]),
        
        # States
        html.Div(style=box, children=[
            html.H2('🗺️ Geographic Risk Distribution', 
                   style={'marginBottom': '24px', 'color': '#1e1b4b', 'fontSize': '30px', 'fontFamily': 'Arial Black'}),
            dcc.Graph(figure=fig_states, config={'displayModeBar': False}),
            html.Hr(style={'margin': '35px 0', 'border': 'none', 'borderTop': '2px solid #e2e8f0'}),
            html.H4('Select a state to explore in detail:', style={'marginBottom': '20px', 'color': '#475569'}),
            html.Div(children=state_items, style={'textAlign': 'center'})
        ]),
        
        # Maturity
        html.Div(style=box, children=[
            html.H2('👔 Business Maturity Analysis', 
                   style={'marginBottom': '30px', 'color': '#1e1b4b', 'fontSize': '30px', 'fontFamily': 'Arial Black'}),
            html.Div(style={'display': 'flex', 'gap': '30px', 'marginBottom': '30px'}, children=[
                html.Div(style={'flex': '1'}, children=[
                    dcc.Graph(figure=fig_mat_donut, config={'displayModeBar': False})
                ]),
                html.Div(style={'flex': '1'}, children=[
                    dcc.Graph(figure=fig_mat_compare, config={'displayModeBar': False})
                ]),
            ]),
            html.Hr(style={'margin': '32px 0', 'border': 'none', 'borderTop': '2px solid #e2e8f0'}),
            html.H4('Explore detailed breakdown by business type:', style={'marginBottom': '20px', 'color': '#475569'}),
            html.Div(children=mat_buttons)
        ]),
        
        # Footer
        html.Div(style={'background': 'linear-gradient(135deg, rgba(255,255,255,0.97), rgba(245,243,255,0.97))',
                       'borderRadius': '14px', 'padding': '30px', 'textAlign': 'center',
                       'boxShadow': '0 8px 25px rgba(0,0,0,0.3)',
                       'border': '2px solid rgba(139,92,246,0.2)'}, children=[
            html.P('🚀 Interactive Dashboard | Python + Dash + Plotly | AWS Pipeline | 👩‍💻 Anita Chelladurai',
                   style={'color': '#64748b', 'margin': '0', 'fontSize': '15px', 'fontWeight': '600'})
        ])
    ])

# DETAIL PAGES (same logic, better colors)
def build_sector_page(detail):
    sector_code, sector_name = detail['code'], detail['name']
    sector_loans = loans_full[loans_full['sector_2digit'] == sector_code]
    
    total = len(sector_loans)
    defaults = int(sector_loans['is_default'].sum()) if total > 0 else 0
    def_rate = (defaults / total * 100) if total > 0 else 0
    
    by_state_data = sector_loans.groupby('state').agg({
        'loannr_chkdgt': 'count',
        'is_default': lambda x: x.sum()
    }).reset_index()
    by_state_data.columns = ['state', 'loans', 'defaults']
    by_state_data['def_rate'] = (by_state_data['defaults'] / by_state_data['loans'] * 100).round(1)
    by_state_data = by_state_data.sort_values('def_rate', ascending=False).head(10)
    
    fig1 = go.Figure(go.Bar(
        x=by_state_data['state'], y=by_state_data['def_rate'],
        marker=dict(color='#8b5cf6', line=dict(color='rgba(255,255,255,0.3)', width=2)),
        text=by_state_data['def_rate'].astype(str) + '%',
        textposition='outside', textfont=dict(size=16)
    )) if len(by_state_data) > 0 else go.Figure()
    fig1.update_layout(title="<b>Default Rates by State</b>", height=400, 
                      plot_bgcolor='#faf5ff', paper_bgcolor='white')
    
    fig2 = go.Figure(go.Pie(
        labels=by_state_data['state'], values=by_state_data['loans'],
        textinfo='label+percent', textfont=dict(size=13),
        marker=dict(line=dict(color='white', width=3))
    )) if len(by_state_data) > 0 else go.Figure()
    fig2.update_layout(title="<b>Distribution</b>", height=400, showlegend=False, paper_bgcolor='white')
    
    sample = sector_loans[['name', 'city', 'state', 'is_default']].head(12)
    
    box = {
        'backgroundColor': 'rgba(255,255,255,0.97)',
        'borderRadius': '16px',
        'padding': '38px',
        'boxShadow': '0 10px 40px rgba(0,0,0,0.3)',
        'marginBottom': '28px'
    }
    
    return html.Div([
        html.Div(style=box, children=[
            html.Button('⬅️ Back to Dashboard', id={'type': 'back-btn', 'index': 0}, n_clicks=0,
                       style={'background': 'linear-gradient(135deg, #6366f1, #4f46e5)',
                              'color': 'white', 'border': 'none', 'padding': '20px 48px',
                              'fontSize': '18px', 'borderRadius': '13px', 'cursor': 'pointer',
                              'fontWeight': 'bold', 'boxShadow': '0 8px 20px rgba(99,102,241,0.4)'})
        ]),
        
        html.Div(style={**box, 'textAlign': 'center',
                       'background': 'linear-gradient(135deg, rgba(255,255,255,0.97), rgba(245,243,255,0.97))',
                       'border': '3px solid rgba(139,92,246,0.3)'}, children=[
            html.H1(f'🏢 {sector_name}', style={'fontSize': '44px', 'fontFamily': 'Arial Black', 'color': '#1e1b4b'}),
            html.H4(f'NAICS Code: {sector_code}', style={'color': '#6b7280'})
        ]),
        
        html.Div(style={'display': 'flex', 'gap': '26px', 'marginBottom': '28px', 'justifyContent': 'center'}, children=[
            html.Div(style={'background': 'linear-gradient(135deg, #6366f1, #4f46e5)',
                           'borderRadius': '16px', 'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(99,102,241,0.35)'}, children=[
                html.H4('Sample', style={'color': 'white', 'marginBottom': '12px'}),
                html.H2(f'{total:,}', style={'color': 'white', 'fontSize': '40px'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #ec4899, #d946ef)',
                           'borderRadius': '16px', 'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(236,72,153,0.35)'}, children=[
                html.H4('Defaults', style={'color': 'white', 'marginBottom': '12px'}),
                html.H2(f'{defaults:,}', style={'color': 'white', 'fontSize': '40px'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #f59e0b, #d97706)',
                           'borderRadius': '16px', 'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(245,158,11,0.35)'}, children=[
                html.H4('Rate', style={'color': 'white', 'marginBottom': '12px'}),
                html.H2(f'{def_rate:.1f}%', style={'color': 'white', 'fontSize': '40px'})
            ]),
        ]),
        
        html.Div(style={'display': 'flex', 'gap': '30px', 'marginBottom': '28px'}, children=[
            html.Div(style={**box, 'flex': '1'}, children=[dcc.Graph(figure=fig1, config={'displayModeBar': False})]),
            html.Div(style={**box, 'flex': '1'}, children=[dcc.Graph(figure=fig2, config={'displayModeBar': False})]),
        ]),
        
        html.Div(style=box, children=[
            html.H3("📋 Sample Businesses", style={'marginBottom': '22px', 'color': '#1e293b'}),
            html.Table([
                html.Thead(html.Tr([
                    html.Th('Business', style={'padding': '15px', 'backgroundColor': '#1e293b', 'color': 'white'}),
                    html.Th('City', style={'padding': '15px', 'backgroundColor': '#1e293b', 'color': 'white'}),
                    html.Th('State', style={'padding': '15px', 'backgroundColor': '#1e293b', 'color': 'white'}),
                    html.Th('Status', style={'padding': '15px', 'backgroundColor': '#1e293b', 'color': 'white'}),
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(str(row['name'])[:50] if pd.notna(row['name']) else 'N/A',
                               style={'padding': '12px', 'borderBottom': '1px solid #e2e8f0'}),
                        html.Td(str(row['city']) if pd.notna(row['city']) else 'N/A',
                               style={'padding': '12px', 'borderBottom': '1px solid #e2e8f0'}),
                        html.Td(str(row['state']) if pd.notna(row['state']) else 'N/A',
                               style={'padding': '12px', 'borderBottom': '1px solid #e2e8f0'}),
                        html.Td('❌ Default' if row['is_default'] else '✅ Paid',
                               style={'padding': '12px', 'borderBottom': '1px solid #e2e8f0',
                                     'color': '#ec4899' if row['is_default'] else '#14b8a6', 'fontWeight': '600'}),
                    ], style={'backgroundColor': '#fafafa' if i % 2 == 0 else 'white'})
                    for i, (_, row) in enumerate(sample.iterrows())
                ])
            ], style={'width': '100%', 'borderCollapse': 'collapse'}) if len(sample) > 0 else html.P("No data")
        ])
    ])

def build_state_page(detail):
    state_code = detail['code']
    state_loans = loans_full[loans_full['state'] == state_code]
    
    total = len(state_loans)
    defaults = int(state_loans['is_default'].sum()) if total > 0 else 0
    def_rate = (defaults / total * 100) if total > 0 else 0
    
    by_sector = state_loans.groupby('industry_name').size().reset_index(name='count')
    by_sector = by_sector.sort_values('count', ascending=False).head(10)
    
    fig = go.Figure(go.Bar(
        y=by_sector['industry_name'], x=by_sector['count'],
        orientation='h',
        marker=dict(color='#14b8a6', line=dict(color='rgba(255,255,255,0.3)', width=2)),
        text=by_sector['count'], textposition='outside', textfont=dict(size=14)
    ))
    fig.update_layout(title=f"<b>Top Industries</b>", height=500, 
                     plot_bgcolor='#f0fdfa', paper_bgcolor='white', margin=dict(l=170, t=70))
    
    box = {
        'backgroundColor': 'rgba(255,255,255,0.97)',
        'borderRadius': '16px',
        'padding': '38px',
        'boxShadow': '0 10px 40px rgba(0,0,0,0.3)',
        'marginBottom': '28px'
    }
    
    return html.Div([
        html.Div(style=box, children=[
            html.Button('⬅️ Back', id={'type': 'back-btn', 'index': 1}, n_clicks=0,
                       style={'background': 'linear-gradient(135deg, #6366f1, #4f46e5)', 'color': 'white',
                              'border': 'none', 'padding': '20px 48px', 'fontSize': '18px',
                              'borderRadius': '13px', 'cursor': 'pointer', 'fontWeight': 'bold',
                              'boxShadow': '0 8px 20px rgba(99,102,241,0.4)'})
        ]),
        
        html.Div(style={**box, 'textAlign': 'center'}, children=[
            html.H1(f'🗺️ State: {state_code}', style={'fontSize': '44px', 'fontFamily': 'Arial Black', 'color': '#1e1b4b'})
        ]),
        
        html.Div(style={'display': 'flex', 'gap': '26px', 'marginBottom': '28px', 'justifyContent': 'center'}, children=[
            html.Div(style={'background': 'linear-gradient(135deg, #6366f1, #4f46e5)', 'borderRadius': '16px',
                           'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(99,102,241,0.35)'}, children=[
                html.H4('Sample', style={'color': 'white'}), html.H2(f'{total:,}', style={'color': 'white'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #ec4899, #d946ef)', 'borderRadius': '16px',
                           'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(236,72,153,0.35)'}, children=[
                html.H4('Defaults', style={'color': 'white'}), html.H2(f'{defaults:,}', style={'color': 'white'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #f59e0b, #d97706)', 'borderRadius': '16px',
                           'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(245,158,11,0.35)'}, children=[
                html.H4('Rate', style={'color': 'white'}), html.H2(f'{def_rate:.1f}%', style={'color': 'white'})
            ]),
        ]),
        
        html.Div(style={'backgroundColor': 'rgba(255,255,255,0.97)', 'borderRadius': '16px', 'padding': '38px',
                       'boxShadow': '0 10px 40px rgba(0,0,0,0.3)'}, children=[
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ])
    ])

def build_maturity_page(detail):
    biz_type = detail['type']
    type_map = {'Established': 0, 'Recent': 1, 'New': 2}
    type_val = type_map.get(biz_type)
    
    if type_val is None:
        type_loans = loans_full[~loans_full['newexist'].isin([0,1,2])]
    else:
        type_loans = loans_full[loans_full['newexist'] == type_val]
    
    total = len(type_loans)
    defaults = int(type_loans['is_default'].sum()) if total > 0 else 0
    def_rate = (defaults / total * 100) if total > 0 else 0
    
    by_sector = type_loans.groupby('industry_name').size().reset_index(name='count')
    by_sector = by_sector.sort_values('count', ascending=False).head(10)
    
    fig = go.Figure(go.Bar(
        y=by_sector['industry_name'], x=by_sector['count'],
        orientation='h',
        marker=dict(color='#ec4899', line=dict(color='rgba(255,255,255,0.3)', width=2)),
        text=by_sector['count'], textposition='outside'
    ))
    fig.update_layout(title=f"<b>Top Industries</b>", height=500, 
                     plot_bgcolor='#fdf4ff', paper_bgcolor='white', margin=dict(l=170, t=70))
    
    box = {
        'backgroundColor': 'rgba(255,255,255,0.97)',
        'borderRadius': '16px',
        'padding': '38px',
        'boxShadow': '0 10px 40px rgba(0,0,0,0.3)',
        'marginBottom': '28px'
    }
    
    return html.Div([
        html.Div(style=box, children=[
            html.Button('⬅️ Back', id={'type': 'back-btn', 'index': 2}, n_clicks=0,
                       style={'background': 'linear-gradient(135deg, #6366f1, #4f46e5)', 'color': 'white',
                              'border': 'none', 'padding': '20px 48px', 'fontSize': '18px',
                              'borderRadius': '13px', 'cursor': 'pointer', 'fontWeight': 'bold',
                              'boxShadow': '0 8px 20px rgba(99,102,241,0.4)'})
        ]),
        
        html.Div(style={**box, 'textAlign': 'center'}, children=[
            html.H1(f'👔 {biz_type}', style={'fontSize': '44px', 'fontFamily': 'Arial Black', 'color': '#1e1b4b'})
        ]),
        
        html.Div(style={'display': 'flex', 'gap': '26px', 'marginBottom': '28px', 'justifyContent': 'center'}, children=[
            html.Div(style={'background': 'linear-gradient(135deg, #6366f1, #4f46e5)', 'borderRadius': '16px',
                           'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(99,102,241,0.35)'}, children=[
                html.H4('Sample', style={'color': 'white'}), html.H2(f'{total:,}', style={'color': 'white'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #ec4899, #d946ef)', 'borderRadius': '16px',
                           'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(236,72,153,0.35)'}, children=[
                html.H4('Defaults', style={'color': 'white'}), html.H2(f'{defaults:,}', style={'color': 'white'})
            ]),
            html.Div(style={'background': 'linear-gradient(135deg, #f59e0b, #d97706)', 'borderRadius': '16px',
                           'padding': '38px', 'minWidth': '210px', 'textAlign': 'center',
                           'boxShadow': '0 10px 25px rgba(245,158,11,0.35)'}, children=[
                html.H4('Rate', style={'color': 'white'}), html.H2(f'{def_rate:.1f}%', style={'color': 'white'})
            ]),
        ]),
        
        html.Div(style=box, children=[
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ])
    ])
server = app.server
if __name__ == '__main__':
    app.run(debug=True, port=8050)