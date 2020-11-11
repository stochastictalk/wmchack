# -*- utf-8 -*-

# Created: 9th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: data and visualizations for app.py

import pandas as pd
import analysis as an
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os

def get_example_raw_tokens(data):
    return ', '.join((data['corpus_raw'])[data['example_fileid']])

def get_example_filtered_tokens(data):
    return ', '.join((data['corpus_words'])[data['example_fileid']])

def get_n_unique_words(data):
    return len(set.union(
                  *[set(txt) for txt in data['corpus_raw'].values()]
               ))

def get_example_fileid(data):
    return [k for k in list(data['corpus_raw'].keys()) 
            if k == '915892388___Senior Staff Nurse.txt'][0]

def get_example_source_text():
    ''' Returns raw text from 'description' field of ./data/example.json 
    '''
    with open(os.path.join('.', 'data', 'example.json'), 'r') as f:
        example_str = json.load(f)['description']
    return example_str

def get_fig_cdf_of_file_lengths(data):
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

def get_fig_pmf_of_token_lengths(data):
    ''' Returns frequency distribution of token lengths for corpus.
    '''
    ser_token_lens = pd.Series([len(t)
                                for fileid in data['corpus_words'].keys() 
                                for t in data['corpus_words'][fileid]])
    ser_freq_dist = ser_token_lens.value_counts()                    

    # create figure with secondary y-axis
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(
        go.Bar(x=ser_freq_dist.index, 
               y=ser_freq_dist.values, name=''),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(x=ser_freq_dist.index, 
               y=ser_freq_dist.values/ser_freq_dist.values.sum(),
               name=''),
        secondary_y=True
    )
    fig.update_xaxes(title_text='Number of characters in token')
    fig.update_yaxes(title_text='Number of tokens')
    fig.update_yaxes(title_text='Fraction of tokens', secondary_y=True)
    fig.update_layout(
        showlegend=False,
        margin=go.layout.Margin(l=20, r=20, b=20, t=20)
    )

    return fig