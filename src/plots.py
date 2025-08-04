import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

def plot_combined_by_channel(pivoted, country_name):
    fig = go.Figure()
    for channel in pivoted.columns:
        fig.add_trace(go.Scatter(
            x=pivoted.index,
            y=pivoted[channel],
            mode='lines+markers',
            name=channel.capitalize(),
            hovertemplate='Month: %{x|%B %Y}<br>' + f'{channel.capitalize()}: ' + '%{y}<extra></extra>'
        ))
    fig.update_layout(
        title=f'Monthly Transactions by Distribution Channel - {country_name}',
        xaxis_title='Month',
        yaxis_title='Number of Transactions',
        xaxis_tickformat='%Y-%m',
        hovermode='x unified'
    )
    return fig

def plot_customers_with_new_and_total(combined, country_name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=combined['transaction_month'],
        y=combined['Active Customers'],
        mode='lines+markers',
        name='Active Customers',
        line=dict(color='blue'),
        hovertemplate='Month: %{x|%B %Y}<br>Active Customers: %{y}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=combined['transaction_month'],
        y=combined['New Customers'],
        mode='lines+markers',
        name='New Customers',
        line=dict(color='green'),
        hovertemplate='Month: %{x|%B %Y}<br>New Customers: %{y}<extra></extra>'
    ))
    fig.update_layout(
        title=f'Active vs New Customers per Month – {country_name}',
        xaxis_title='Month',
        yaxis_title='Number of Customers',
        xaxis_tickformat='%Y-%m',
        hovermode='x unified'
    )
    return fig

def plot_pie(labels, values, title):
    import plotly.graph_objects as go
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo='label+percent',
        hovertemplate='%{label}: %{value}<extra></extra>',
        pull=[0.05]*len(labels)  # Slightly pull all slices for visibility
    )])
    fig.update_layout(
        title=title,
        legend_title_text='Category',
        legend=dict(orientation='h', y=-0.1),
        margin=dict(t=60, b=20)
    )
    return fig

def plot_cohort_heatmap(retention, cohort_labels, country_name):
    plt.figure(figsize=(16, 10))
    plt.title(f'Month-over-Month Retention Rate - {country_name}', fontsize=16)
    sns.heatmap(retention, annot=True, fmt='.1f', cmap='YlGnBu',
                vmin=0, vmax=100, cbar_kws={'label': 'Retention %'})
    plt.xlabel('Cohort Index (Months Since First Transfer)', fontsize=12)
    plt.ylabel('Cohort Month (First Transfer Month)', fontsize=12)
    plt.yticks(ticks=np.arange(len(cohort_labels)) + 0.5, labels=cohort_labels, rotation=0)
    plt.tight_layout()
    return plt 