## TODO:
#   Rewrite web scraper so that it is reliable


# -*- utf-8 -*-
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

# include visualizations
e_header = [dcc.Markdown('''
_© 2020 Decision Analysis Services Ltd._

# **Text Mining Web Application**
''')]

corpus_id = 'Vacancy descriptions featured on NHS Jobs on 7th Nov 2020'
source_url = 'https://www.jobs.nhs.uk/'
offset = 15

e_contents = [
    dcc.Markdown('## **Contents**  ', id='sec-contents'),
    dhtml.A('Corpus Specification', href='#sec-corpus-spec'),
    dhtml.Br(),
    dhtml.A('Preprocessing Summary', href='#sec-preprocessing-summary'),
    dhtml.Br(),
    dhtml.A('Corpus Statistics', href='#sec-corpus-statistics')
]

e_corpus_spec = [
    dcc.Markdown('''
    ## **Corpus Specification**

    **Data source:**  ''' + '&nbsp;'*(offset-12) 
    + '[' + corpus_id + ']'
    + '(' + source_url + ')'
    + '''  

    **Files:** ''' + '&nbsp;'*offset
    + '{:,}'.format(data['n_files'])
    + '''  

    **Words:** ''' + '&nbsp;'*(offset-2) 
    + '{:,}'.format(data['n_words'])
    + '''  

    **Unique words:** ''' + '&nbsp;'*(offset - 14)
    + '{:,}'.format(data['n_unique_words']),
    id='sec-corpus-specification'
    ),
]

e_corpus_preprocessing = [
    dcc.Markdown('''
    ## **Preprocessing summary**  

    #### **Sample text from source**  
    > ```
    '''
    + data['example_source_text']
    + '''```    

    #### **Sample raw tokens from file ''' 
    + '`{}`'.format(data['example_fileid']) 
    + '''**  
    > ```'''
    + data['example_raw_tokens']
    + '''``` 

    #### **Sample filtered tokens from file ''' 
    + '`{}`'.format(data['example_fileid']) 
    + '''**  
    > ```'''
    + data['example_filtered_tokens']
    + '''```  ''',
    id='sec-preprocessing-summary')
]

e_corpus_statistics = [
    dcc.Markdown('''
    ## **Corpus Statistics**  
    ''',
    id='sec-corpus-statistics'),

    dhtml.Div([
        dcc.Markdown('''
        #### Distribution of file lengths  ''' 
        ),
        dcc.Graph(
            id='graph-filelengthcdf',
            figure=viz.get_fig_cdf_of_file_lengths(data),
            style={
                'width':'350px',
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
        #### Distribution of token lengths  ''' 
        ),
        dcc.Graph(
            id='graph-tokenlengthpmf',
            figure=viz.get_fig_pmf_of_token_lengths(data),
            style={
                'width':'350px',
                'height':'350px',
                'display':'block',
                'margin-left':'auto',
                'margin-right':'auto'
            }
        )],
    style={'width':'50%', 'display':'inline-block', 'vertical-align':'top'}
    ),

    dhtml.Br(),

    dcc.Markdown('''
    #### 100 most common tokens  ''' 
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

    dhtml.Br(),

    dcc.Markdown('''
    #### What other words appear in files that contain `keyword`?
    
    Enter a keyword to find words that commonly occur in the same file,
     but are not common to all files in the corpus.
    '''
    ),
    dhtml.Div(['Keyword: ',
              dcc.Input(id='input-wordsearch', value='analyst', type='text')],
              style={'width':'40%', 'display':'inline-block'}),
    dhtml.Div(id='div-wordsearch-confirm',
              style={'width':'60%', 'display':'inline-block'}),

    dhtml.Div(id='div-wordsearch-table'),

    dhtml.Br(),

    dcc.Markdown('''
        #### Are there clusters of files containing similar words?  

        '''),
    dhtml.Div([
        dcc.Graph(
            id='graph-pca',
            figure=viz.get_fig_scatter_of_pc_tfidf(data),
            style={
                'width':'350px',
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

    dhtml.Br(),


    dcc.Markdown('''
        #### Which files are similar to `file1` and `file2`?  

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

app.layout = dhtml.Div([
    *e_header,
    dhtml.Hr(),
    *e_contents,
    dhtml.Hr(),
    *e_corpus_spec,
    dhtml.A('return to contents', href='#sec-contents'),
    dhtml.Hr(),
    *e_corpus_preprocessing,
    dhtml.A('return to contents', href='#sec-contents'),
    dhtml.Hr(),
    *e_corpus_statistics,
    dhtml.A('return to contents', href='#sec-contents'),
    dhtml.Br(),
    dhtml.Br()
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