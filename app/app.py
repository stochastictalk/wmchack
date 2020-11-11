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

    dcc.Markdown('''
    **Co-featured word search**
    
    Enter a keyword to find words that commonly occur in the same file,
     but are not common to all files in the corpus.
    '''
    ),

    viz.get_table_of_similar_words(data, keyword='python'),
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



if __name__ == '__main__':
	app.run_server(debug=True)