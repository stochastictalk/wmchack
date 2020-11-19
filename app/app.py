#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as dhtml
from dash.dependencies import Input, Output
import dash_table as dtable
import analysis as an
import viz as viz
import json
import plotly.io as pio

pio.templates.default = 'seaborn'

# Load data
data = viz.load_data()

# intialize app obj
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# tab style
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#CC1F1F',
    'color': 'white',
    'padding': '6px'
}

main_tab_selected_style = {
    'borderTop': '1px solid #CC1F1F',
}

# include visualizations
e_header = [dcc.Markdown('''
_© 2020 Decision Analysis Services Ltd._

# **Text Mining Web Application**
''')]

corpus_id = 'Vacancy descriptions featured on NHS Jobs on 7th Nov 2020'
source_url = 'https://www.jobs.nhs.uk/'
offset = 20

e_corpus_spec = [
    dcc.Markdown('''
    ## **Corpus Specification**

    ##### Data source:  ''' + '&nbsp;'*(offset-12) 
    + '[' + corpus_id + ']'
    + '(' + source_url + ')'
    + '''  

    ##### Files: ''' + '&nbsp;'*offset
    + '{:,}'.format(data['n_files'])
    + '''  

    ##### Words: ''' + '&nbsp;'*(offset-2) 
    + '{:,}'.format(data['n_words'])
    + '''  

    ##### Unique words: ''' + '&nbsp;'*(offset - 15)
    + '{:,}'.format(data['n_unique_words']),
    id='sec-corpus-specification'
    ),

    dhtml.Br(),
    
    dhtml.Div([
        dcc.Markdown('''
        ##### Distribution of file lengths  ''' 
        ),
        dcc.Graph(
            id='graph-filelengthcdf',
            figure=viz.get_fig_cdf_of_file_lengths(data),
            style={
                'width':'450px',
                'height':'350px',
                'display':'block',
                'margin-left':'auto',
                'margin-right':'auto'
            }
        )],
    style={'width':'50%', 'display':'inline-block', 'vertical-align':'top'}
    ),

    dhtml.Div([
        dcc.Markdown('''
        ##### Distribution of token lengths  ''' 
        ),
        dcc.Graph(
            id='graph-tokenlengthpmf',
            figure=viz.get_fig_pmf_of_token_lengths(data),
            style={
                'width':'450px',
                'height':'350px',
                'display':'block',
                'margin-left':'auto',
                'margin-right':'auto'
            }
        )],
    style={'width':'50%', 'display':'inline-block', 'vertical-align':'top'}
    ),

    dhtml.Br(),
    dhtml.Br(),

    dcc.Markdown('''
    ##### 100 most common tokens  ''' 
    ),
    dcc.Graph(
        id='graph-toptokens',
        figure=viz.get_fig_most_common_tokens(data),
        style={
            'width':'700px',
            'height':'400px',
            'display':'block',
            'margin-left':'auto',
            'margin-right':'auto'
        }
    ),

]

e_corpus_preprocessing = [
    dcc.Markdown('''
    ## **Preprocessing summary**  
    '''
    ),
    
    dcc.Markdown('##### Sample text from source'),
    dhtml.Div([
        dcc.Markdown('''  
        > ```'''
        + data['example_source_text']
        + '''```  '''
        )
    ], style={'height':'300px', 'width':'100%',
              'overflow-y':'scroll',
              'word-wrap':'break-word'}
    ),
    dhtml.Br(),
    dcc.Markdown('''
        ##### Sample raw tokens from file ''' 
        + '`{}`'.format(data['example_fileid'])
    ),
    dhtml.Div([
        dcc.Markdown('''  
        > ```'''
        + data['example_raw_tokens']
        + '''```'''
        )
    ], style={'height':'300px', 'overflow':'auto'}
    ),
    dhtml.Br(),
    dcc.Markdown('''
        ##### Sample filtered tokens from file ''' 
        + '`{}`'.format(data['example_fileid'])
    ),
    dhtml.Div([
        dcc.Markdown('''  
        > ```'''
        + data['example_filtered_tokens']
        + '''```  '''
        )
    ], style={'height':'300px', 'overflow':'auto'}
    )
]


e_div_wordsearch = [
    dhtml.Br(), 
    dcc.Markdown('''
    ##### What other words appear in files that contain `keyword`?
    
    Enter a keyword to find words that commonly occur in the same file,
     but that are not common to all files in the corpus.
    '''
    ),
    dhtml.Div(['Keyword: ',
              dcc.Input(id='input-wordsearch', value='analyst', type='text')],
              style={'width':'40%', 'display':'inline-block'}),
    dhtml.Div(id='div-wordsearch-confirm',
              style={'width':'60%', 'display':'inline-block'}),

    dhtml.Br(),
    dhtml.Br(),

    dhtml.Div(id='div-wordsearch-table')
]


e_graph_pca = [
    dhtml.Br(), 
    dcc.Markdown('''
        ##### Are there clusters of files containing similar words?  

        '''),
    dhtml.Div([
        dcc.Graph(
            id='graph-pca',
            figure=viz.get_fig_scatter_of_pc_tfidf(data),
            style={
                'width':'450px',
                'height':'350px',
                'display':'block-inline',
                'margin-left':'auto',
                'margin-right':'auto',
                'vertical-align':'top'
            }
        )],
    style={'width':'50%', 'display':'inline-block', 'vertical-align':'top'}
    ),
    dhtml.Div([
        dcc.Markdown(id='markdown-pca')
        ],
    style={'width':'50%', 'display':'inline-block', 'vertical-align':'top'}
    ),

    dhtml.Br()
]


e_graph_jacardindex = [
    dhtml.Br(),
    dcc.Markdown('''
        ##### Which files share words with `file1` and `file2`?  

        '''),
    dhtml.Div([
        dcc.Markdown(id='markdown-jacardindex',
                     children=viz.get_filtered_file_tokens(data, 
                         '915892388___Senior Staff Nurse.txt'))
        ],
    style={'height':'350px', 'width':'50%', 'overflow':'auto',
           'display':'inline-block', 'vertical-align':'top'}
    ),
    dhtml.Div([
        dcc.Graph(
            id='graph-jacardindex',
            figure=viz.get_fig_jacard_index_scatterplot(data),
            style={
                'width':'350px',
                'height':'350px',
                'display':'block-inline',
                'margin-left':'auto',
                'margin-right':'auto'
            })
        ],
    style={'width':'50%', 'display':'inline-block', 'vertical-align':'top'}
    )
]

e_corpus_statistics = [
    dcc.Markdown('''
    ## **Corpus Statistics**  
    ''',
    id='sec-corpus-statistics'),
    dhtml.Div([
        dcc.Tabs([
            dcc.Tab(label='Jacard index scatter plot',
                    children=e_graph_jacardindex,
                    style=tab_style,
                    selected_style=tab_selected_style),
            dcc.Tab(label='Word similarity search',
                    children=e_div_wordsearch,
                    style=tab_style,
                    selected_style=tab_selected_style),
            dcc.Tab(label='Document cluster analysis',
                    children=e_graph_pca,
                    style=tab_style,
                    selected_style=tab_selected_style)
        ],
        style={'width':'95%'})],
    style={'height':'700px'})
]

app.layout = dhtml.Div([
    *e_header,
    dhtml.Hr(),
    dcc.Tabs([
        dcc.Tab(label='Corpus Specification', 
                children=e_corpus_spec,
                selected_style=main_tab_selected_style
        ),
        dcc.Tab(label='Preprocessing',
                children=e_corpus_preprocessing,
                selected_style=main_tab_selected_style
        ),
        dcc.Tab(label='Corpus Statistics',
                children=e_corpus_statistics,
                selected_style=main_tab_selected_style
        )
    ])
], 
style={'width': '60%', 'margin':'auto'}
)


# define callbacks

# keyword search
@app.callback(
    [Output(component_id='div-wordsearch-confirm', component_property='children'),
     Output(component_id='div-wordsearch-table', component_property='children')],
    [Input(component_id='input-wordsearch', component_property='value')]
)
def update_table_of_similar_words(keyword):
    output_keyword_confirm = 'Showing results for token \'{}\''.format(
                                                                       keyword)
    try:
        output_keyword_table = viz.get_table_of_similar_words(data, keyword)
    except KeyError:
        output_keyword_table = ('The token \'{}\' does not appear in the'
                                ' corpus.').format(keyword)
    
    return (output_keyword_confirm, output_keyword_table)


# PCA explorer - display file info on click
@app.callback(
    Output('markdown-pca', 'children'),
    [Input('graph-pca', 'clickData')])
def update_file_displayed_pca(clickData):
    try:
        fileid = clickData['points'][0]['hovertext']
        return (
            'File id  \n`\'{}\'`  \n\n'.format(fileid) 
            + 'Tokens in file  \n `{}`  \n\n'.format(viz.get_file_length(data, fileid))
            + 'Distinguishing tokens  \n'
            + '`' + viz.get_file_top_tfidf(data, fileid) + '`'
            )
    except TypeError:
        return '> `Click a marker to display file statistics`'


# Document similarity explorer
@app.callback(
    Output('markdown-jacardindex', 'children'),
    [Input('graph-jacardindex', 'clickData')])
def update_file_displayed_jacardindex(clickData):
    try:
        fileid = clickData['points'][0]['hovertext']
        return ('Tokens in file `\'' + fileid + '\'`  \n' 
                + '> `' + viz.get_filtered_file_tokens(data, fileid) + '`')
    except TypeError:
        return '> `Click a marker to display file contents`'

if __name__ == '__main__':
	app.run_server(debug=True)