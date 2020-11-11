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

# Load data
data = an.load_viz_data()
data['n_unique_words'] = viz.get_n_unique_words(data)
data['example_fileid'] = viz.get_example_fileid(data)
data['example_source_text'] = viz.get_example_source_text()
data['example_raw_tokens'] = viz.get_example_raw_tokens(data)
data['example_filtered_tokens'] = viz.get_example_filtered_tokens(data)

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
e_corpus_spec = [
    dcc.Markdown('''
    #### **Corpus Specification**

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
    + '{:,}'.format(data['n_unique_words'])
    + '''  

    **Sample text from source**  
    > ```
    '''
    + data['example_source_text']
    + '''```    

    **Sample raw tokens from file ''' 
    + '`{}`'.format(data['example_fileid']) 
    + '''**  
    > ```'''
    + data['example_raw_tokens']
    + '''``` 

    **Sample filtered tokens from file ''' 
    + '`{}`'.format(data['example_fileid']) 
    + '''**  
    > ```'''
    + data['example_filtered_tokens']
    + '''```  '''
    )
]

e_corpus_statistics = [
    dcc.Markdown('''
    #### **Corpus Statistics**  
    '''),

    dcc.Markdown('''
    **Distribution of file lengths**  ''' 
    ),
    dcc.Graph(
        id='cdf_of_file_lengths',
        figure=viz.get_fig_cdf_of_file_lengths(data),
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
    **Distribution of token lengths**  ''' 
    ),
    dcc.Graph(
        id='pmf_of_token_lengths',
        figure=viz.get_fig_pmf_of_token_lengths(data),
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
    **Most common tokens**  ''' 
    ),
    dcc.Graph(
        id='most_common_tokens',
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
    **Co-featured word search**
    
    Enter a keyword to find words that commonly occur in the same file,
     but are not common to all files in the corpus.
    '''
    ),
    dhtml.Div(['Keyword: ',
              dcc.Input(id='input-keyword', value='analyst', type='text')],
              style={'width':'40%', 'display':'inline-block'}),
    dhtml.Div(id='output-keyword-confirm',
              style={'width':'60%', 'display':'inline-block'}),

    dhtml.Div(id='output-keyword-table'),

    dhtml.Br(),

    dcc.Markdown('''
        **Latent dimension analysis**  

        '''),
    dhtml.Div([
        dcc.Graph(
            id='dimensionality-reduction',
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
        dcc.Markdown(id='output-filtered-tokens',
                     children=viz.get_filtered_file_tokens(data, 
                         '915892388___Senior Staff Nurse.txt'))
        ],
    style={'width':'50%', 'display':'inline-block', 'vertical-align':'top'}
    )
]

app.layout = dhtml.Div([
    *e_header,
    dhtml.Hr(),
    *e_corpus_spec,
    dhtml.Hr(),
    *e_corpus_statistics
], 
style={'width': '60%', 'margin':'auto'}
)


# define callbacks

# keyword search
@app.callback(
    [Output(component_id='output-keyword-confirm', component_property='children'),
     Output(component_id='output-keyword-table', component_property='children')],
    [Input(component_id='input-keyword', component_property='value')]
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

# display text on click
@app.callback(
    Output('output-filtered-tokens', 'children'),
    [Input('dimensionality-reduction', 'clickData')])
def update_file_displayed(clickData):
    try:
        fileid = clickData['points'][0]['hovertext']
        return (
            'File id  \n`\'{}\'`  \n\n'.format(fileid) 
            + 'Tokens in file  \n `{}`  \n\n'.format(viz.get_file_length(data, fileid))
            + 'Distinguishing tokens  \n'
            + '`' + viz.get_file_top_tfidf(data, fileid) + '`'
            )
    except TypeError:
        return '> `Click a marker to display file text and statistics`'

if __name__ == '__main__':
	app.run_server(debug=True)