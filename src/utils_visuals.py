import plotly.express as px
import streamlit as st

def plot_pdd_horizontal(df_perc,x,y):
    """
    Gera um gráfico de barras horizontais para PDD por Faixa.
    """
    fig = px.bar(
        df_perc, 
        x=x,      
        y=y,          
        orientation='h',        
        labels={
            f'{x}': f'Valor {x} (R$)', 
            f'{y}': f'{y}'
        },
        title="Distribuição da PDD por Faixa",
        color="PDD POR FAIXA",
        color_continuous_scale="Reds"
    )

    fig.update_traces(
        hovertemplate='<b>Faixa:</b> %{y}<br><b>PDD:</b> R$ %{x:,.2f}'
    )

    fig.update_layout(
        xaxis_tickprefix="R$ ",
        xaxis_tickformat=",",
        yaxis={'categoryorder': 'trace'}, # Mantém a ordem original do DF
        showlegend=False
    )
    
    return st.plotly_chart(fig, use_container_width=True)