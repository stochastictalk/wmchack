#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Created: 9th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: functions that return data directly displayed in app.py

import pandas as pd
import analysis as an
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_html_components as dhtml
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
import pickle
import numpy as np

import json
import os
import glob

# text_analysis.py contains utilities for reading, writing, and processing text documents
# viz.py contains utilities for that store and pass data to the front-end
# convention is _not_ to use plotly express
# while the app is running
# app needs two things
#   initial data load
#   runtime data retrieval
# types of data
#   graphs
#   tables
#   markdown

class Backend:
    ''' Object for retrieving data to be displayed by front end.
    '''

    def __init__(self, corpus_id):

        # init data
        self.data = self.Data(corpus_id)
        self.viz = self.Viz()

    class Data:
        # wrapper for data used by visualizations
        def __init__(self, corpus_id):
            self.corpus_id = corpus_id
            self.corpus_raw = an.read_corpus(corpus_id)
            self.corpus_words = an.get_corpus_words(self.corpus_raw)
            self.corpus_types = an.get_corpus_types(self.corpus_words)
            self.n_files = an.n_fileids(self.corpus_raw)
            self.n_words = an.n_words(self.corpus_raw)
            self.token_index = an.get_token_index(self.corpus_types)
            self.fileid_index = an.get_fileid_index(self.corpus_types)
            self.token_i = {t: j for j, t in enumerate(self.token_index)}
            self.fileid_i = {fi: j for j, fi in enumerate(self.fileid_index)}
            (self.s_termfreq, self.s_tfidf) = an.tf_idf(self.corpus_types,
                                                        self.corpus_words,
                                                        self.fileid_index,
                                                        self.token_index)
            self.n_filt_tokens_by_file = an.n_tokens_by_file(self.corpus_words,
                                                             self.fileid_index)
            self.example_fileid  = self.get_example_fileid()


        def get_example_fileid(self):
                return [k for k in list(self.corpus_raw.keys()) 
                             if k == '915892388___Senior Staff Nurse.txt'][0]


    class Viz:
        # wrapper for groups of functions returning visualizations
        def __init__(self):
            self.graph = self.Graph()
            self.table = self.Table()
            self.md = self.Markdown()

        class Markdown:
            # wrapper for functions returning markdown strings
            def __init__(self): 
                pass

            def source_text(self, data, fileid):
                fp = os.path.join('.', data.corpus_id, fileid)
                with open(fp, 'r') as f:
                    f_str = f.read()
                return f_str

            def raw_tokens_in_file(self, data, fileid):
                return ', '.join(data.corpus_raw[fileid])

            def filtered_tokens_in_file(self, data, fileid):
                return ', '.join(data.corpus_words[fileid])

            def n_unique_tokens_in_raw(self, data):
                return '{:,}'.format(len(set.union(
                            *[set(txt) for txt in data.corpus_raw.values()]
                        )))

            def corpus_words(self, data, fileid):
                ''' Returns string listing tokens in file.
                '''
                return ', '.join(data.corpus_words[fileid])


            def top_tfidf(self, data, fileid):
                ''' Returns string listing file's words with highest tf-idf.
                '''
                i = data.fileid_i[fileid]
                ser_tfidf = pd.Series(data.s_tfidf[i, :].todense(), 
                                    index=data.token_index)
                return ', '.join(ser_tfidf.nlargest(20).index)


            def n_tokens_in_file(self, data, fileid):
                return str(len(data.corpus_words[fileid]))


        class Graph:

            # wrapper for functions returning graphs
            def __init__(self): 
                pass


            def line_cdf_n_tokens_in_corpus_raw(self, data):
                x, P_x = an.cdf(an.n_tokens_by_file(data.corpus_raw,
                                                    data.fileid_index))
                N_x = P_x*data.n_files # cumulative count

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

            
            def bar_pmf_token_lengths(self, data):
                ''' Returns frequency distribution of token lengths for corpus.
                '''
                ser_token_lens = pd.Series([len(t)
                                            for fileid in data.corpus_words.keys() 
                                            for t in data.corpus_words[fileid]])
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


            def bar_cdf_most_common_tokens(self, data, N=100):
                ''' Returns plot showing how many corpus tokens are of top N tokens.
                '''
                # get list of all tokens in filtered corpus
                tokens = [t for fileid in data.corpus_words.keys()
                          for t in data.corpus_words[fileid]]

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
            
            def scatter_pc_tfidf(self, data):
                Xin = data.s_tfidf.tocsr() # to scipy sparse CSR format
                Xin = normalize(Xin)
                svd = TruncatedSVD(n_components=2)
                svd.fit(Xin)
                Xout = svd.transform(Xin)

                df_display = pd.DataFrame({
                                    'Latent dimension 1': Xout[:, 0],
                                    'Latent dimension 2': Xout[:, 1],
                                    'File id': data.fileid_index,
                                    'File length': data.n_filt_tokens_by_file
                                })
                fig = px.scatter(df_display, x='Latent dimension 1',
                                y='Latent dimension 2', hover_name='File id',
                                color='File length',
                                hover_data={
                                    'Latent dimension 1': False,
                                    'Latent dimension 2': False,
                                    'File length': False
                                })
                fig.update_traces(marker=dict(size=5,
                                line=dict(width=1,
                                            color='white')),
                                selector=dict(mode='markers'))
                fig.update_layout(
                    showlegend=False,
                    margin=go.layout.Margin(l=20, r=20, b=20, t=20),
                    clickmode='event'
                )
                return fig

                
            def scatter_jacard(self, data):

                fileid_1 = '916243993___Occupational Therapist.txt'
                fileid_2 = '916250258___Experienced Care Support Worker.txt'

                # compute jacard_index(fileid_1, fileid) for all fileid
                ser_ji_1 = an.jacard_index(s_tf=data.s_termfreq, 
                                            fileid=fileid_1,
                                            fileid_i=data.fileid_i,
                                            fileid_index=data.fileid_index)
                ser_ji_2 = an.jacard_index(
                                s_tf=data.s_termfreq, # and for fileid_2
                                fileid=fileid_2,
                                fileid_i=data.fileid_i,
                                fileid_index=data.fileid_index)

                # put the Series in a DataFrame for display
                df_display = pd.DataFrame({'File 1 JI':ser_ji_1,
                                            'File 2 JI':ser_ji_2,
                                            'File id': data.fileid_index})
                fig = px.scatter(df_display, x='File 1 JI',
                                y='File 2 JI', hover_name='File id',
                                hover_data={'File 1 JI': False,
                                            'File 2 JI': False})

                fig.update_traces(marker=dict(size=5,
                                            line=dict(width=1,
                                                        color='white')),
                                selector=dict(mode='markers'))
                fig.update_layout(
                    showlegend=False,
                    margin=go.layout.Margin(l=20, r=20, b=20, t=20),
                    clickmode='event')
                return fig

            

        class Table:
            # wrapper for funcitons returning tables
            def __init__(self):
                pass


            def similar_words(self, data, keyword, N=10):
                # get dataframe containing top N most similar words
                df_similar = an.similar_words(keyword, data.token_i,
                                              data.token_index, data.s_tfidf, N=N)
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
                return self.__generate_table(df_similar, max_rows=N)


            def __generate_table(self, dataframe, max_rows=10):
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
