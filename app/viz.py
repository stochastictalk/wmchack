# -*- utf-8 -*-

# Created: 9th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: visualizations for app.py

import pandas as pd
import analysis as an
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_cdf_of_file_lengths(data):
    x, P_x = an.cdf(an.file_lengths(data['corpus_raw']))
    N_x = P_x*data['n_files'] # cumulative count

    # create figure with secondary y-axis
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(
        go.Scatter(x=x, y=N_x, mode='lines'),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=x, y=P_x, mode='lines', name='Fraction of corpus'),
        secondary_y=True
    )
    fig.update_xaxes(title_text='Words in file')
    fig.update_yaxes(title_text='Files with this many words or fewer', secondary_y=False)
    fig.update_yaxes(title_text='Fraction of corpus', secondary_y=True)
    fig.update_layout(
        showlegend=False,
        margin=go.layout.Margin(l=20, r=20, b=20, t=20)
    )

    return fig