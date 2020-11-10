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

# Load data
data = an.load_viz_data()
data['n_unique_words'] = len(set.union(
                            *[set(txt) for txt in data['corpus_raw'].values()]
                        ))
data['example_fileid'] = list(data['corpus_raw'].keys())[777]

# intialize app obj
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# include visualizations
e_header = [dcc.Markdown('''
_© 2020 Decision Analysis Services Ltd._

# **Text Mining Web Application**
''')]

corpus_id = 'Vacancy descriptions featured on NHS Jobs on 7th Nov 2020'
offset = 15
e_corpus_spec = [
    dcc.Markdown('''
    #### **Corpus Specification**

    **Data source:**  ''' + '&nbsp;'*(offset-12) 
    + corpus_id
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

    **Sample file tokens from file ''' 
    + '`{}`'.format(data['example_fileid']) 
    + ''':**  
    > ```'''
    + ', '.join((data['corpus_raw'])[data['example_fileid']])[1:-1]
    + '''```

    **Distribution of file lengths**:  ''' 
    ),

    dcc.Graph(
        id='file_lengths',
        figure=viz.plot_cdf_of_file_lengths(data),
        style={
            'width':'700px',
            'height':'400px',
            'display':'block',
            'margin-left':'auto',
            'margin-right':'auto'
        }
    )
]

app.layout = dhtml.Div([
    *e_header,
    dhtml.Hr(),
    *e_corpus_spec,
], 
style={'width': '60%', 'margin':'auto'}
)


# define callbacks



if __name__ == '__main__':
	app.run_server(debug=True)