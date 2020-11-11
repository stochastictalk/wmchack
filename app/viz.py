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
import dash_html_components as dhtml
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
import numpy as np

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
        go.Scatter(x=x, y=100*P_x, mode='lines', name='% of corpus files'),
        secondary_y=True
    )
    fig.update_xaxes(title_text='Words in file')
    fig.update_yaxes(title_text='Files with this many words or fewer', secondary_y=False)
    fig.update_yaxes(title_text='Cumulative % of corpus files', secondary_y=True)
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
               y=100*ser_freq_dist.values/ser_freq_dist.values.sum(),
               name=''),
        secondary_y=True
    )
    fig.update_xaxes(title_text='Number of characters in token')
    fig.update_yaxes(title_text='Number of tokens')
    fig.update_yaxes(title_text='% of corpus tokens', secondary_y=True)
    fig.update_layout(
        showlegend=False,
        margin=go.layout.Margin(l=20, r=20, b=20, t=20)
    )

    return fig

def get_fig_most_common_tokens(data, N=100):
    ''' Returns plot showing how many corpus tokens are of top N tokens.
    '''
    # get list of all tokens in filtered corpus
    tokens = [t for fileid in data['corpus_words'].keys()
              for t in data['corpus_words'][fileid]]

    # get token counts (as a proportion)
    ser_token_c = pd.Series(tokens).value_counts() # c for count
    n_words_in_corpus = ser_token_c.values.sum()

    # get cumulative fraction of corpus
    ser_token_p = ser_token_c.nlargest(N)/n_words_in_corpus
    ser_token_F = 100*ser_token_p.cumsum()

    # format index to include rank
    ser_token_F.index = [t + ' (' + str(j+1) + ')' for j, t in 
                         enumerate(ser_token_F.index)]
    ser_token_F = ser_token_F.sort_values(ascending=False)

    # plot it 
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=ser_token_F.values, 
               y=ser_token_F.index,
               orientation='h')
    )
    fig.update_xaxes(title_text='Cumulative % of corpus tokens')
    fig.update_yaxes(title_text='Token')
    fig.update_layout(
        showlegend=False,
        margin=go.layout.Margin(l=20, r=20, b=20, t=20)
    )

    return fig

def get_table_of_similar_words(data, keyword, N=10):
    # get dataframe containing top N most similar words
    df_similar = an.similar_words(keyword, data['token_index'],
                                  data['s_tfidf'], N=N)
    # format numeric cols to strings
    for coln in df_similar.columns:
        if coln not in ['Token', '# of files w token']:
            df_similar[coln] = df_similar[coln].apply(
                lambda v: '{:4.1f}'.format(v)
            )
        if coln == '# of files w token':
            df_similar[coln] = df_similar[coln].apply(
                lambda v: '{:,}'.format(v)
            )
    return __generate_table(df_similar, max_rows=N)

def __generate_table(dataframe, max_rows=10):
    ''' From https://dash.plotly.com/layout
    '''
    return dhtml.Table([
        dhtml.Thead(
            dhtml.Tr([dhtml.Th(col, style={'text-align':'center'})
                      for col in dataframe.columns],
                      style={'line-height': '11px' })
        ),
        dhtml.Tbody([
            dhtml.Tr([
                dhtml.Td(dataframe.iloc[i][col], style={'text-align':'center'})
                for col in dataframe.columns
            ], style={'line-height': '11px' })
            for i in range(min(len(dataframe), max_rows))
        ])
    ], style={'font-size':'11px', 'width':'70%', 'margin':'auto'})


def get_fig_scatter_of_pc_tfidf(data):
    Xin = data['s_tfidf'].tocsr() # to scipy sparse CSR format
    Xin = normalize(Xin)
    svd = TruncatedSVD(n_components=2)
    svd.fit(Xin)
    Xout = svd.transform(Xin)

    inv_fileid_index = {v: k for k, v in data['fileid_index'].items()}
    fileids = [inv_fileid_index[j] for j in range(len(inv_fileid_index.keys()))]
    df_display = pd.DataFrame({
                        'Latent dimension 1': Xout[:, 0],
                        'Latent dimension 2': Xout[:, 1],
                        'File id': fileids
                    })
    fig = px.scatter(df_display, x='Latent dimension 1',
                     y='Latent dimension 2', hover_name='File id',
                     hover_data={
                         'Latent dimension 1': False,
                         'Latent dimension 2': False
                     }
                     )
    fig.update_layout(
        showlegend=False,
        margin=go.layout.Margin(l=20, r=20, b=20, t=20),
        clickmode='event'
    )
    return fig

def get_filtered_file_tokens(data, fileid):
    return ', '.join(data['corpus_words'][fileid])

def get_file_top_tfidf(data, fileid):
    i = data['fileid_index'][fileid]
    ser_tfidf = pd.Series(data['s_tfidf'][i, :].todense(), 
                          index=sorted(data['token_index'].keys(),
                                       key=lambda k: data['token_index'][k]))
    return ', '.join(ser_tfidf.nlargest(20).index)

def get_file_length(data, fileid):
    return len(data['corpus_words'][fileid])