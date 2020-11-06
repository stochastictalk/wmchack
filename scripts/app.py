## TODO:
#   Rewrite web scraper so that it is reliable


# -*- utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as dhtml
from dash.dependencies import Input, Output
import dash_table as dtable
from datetime import datetime, date, timezone, timedelta
import plotly.express as px
import pandas as pd
from glob import glob
import json
import numpy as np
import json


# from nb
import pandas as pd
from glob import glob
import json
from time import time
import html
import nltk
from matplotlib import pyplot as plt
import seaborn as sns
sns.set_style('darkgrid')
import numpy as np
from itertools import combinations_with_replacement

# data read and prep
fp = glob('../data/*.feather')[0]
df = pd.read_feather(fp)
ser_desc = df['description'] 
ser_desc.index = df['url']

def preprocess(ser_desc: pd.Series):
    ser_desc = ser_desc.copy()
    ser_desc = ser_desc.apply(lambda value: html.unescape(value)) # replace entities
    ser_desc = ser_desc.str.replace(pat='<\/?[^>]*>', repl='') # strip html tags
    ser_desc = ser_desc.str.replace(pat='\\n', repl=' ') # strip newline chars
    ser_desc = ser_desc.str.lower()
    ser_desc = ser_desc.apply(lambda value: nltk.word_tokenize(value)) # splits string into list of tokens
    ser_desc = ser_desc.apply(lambda value: nltk.Text(value))
    #porter = nltk.PorterStemmer()
    #ser_desc = ser_desc.apply(lambda lst: [porter.stem(t) for t in lst]) 
    df_desc = ser_desc.to_frame()
    df_desc.columns = ['text']
    return df_desc

def get_keyword_presence(df_text: pd.DataFrame):
    ''' Creates a data frame containing counts of keywords.
    ''' 
    keywords = sorted(['analyst', 'analysis', 'analytical', 'data', 'prediction', 'predictive',
                       'sql', 'python', 'r', 'digital', 'software', 'automation', 'automate',
                       'maths', 'mathematics', 'physics', 'etl', 'informatics', 'bioinformatics',
                       'statistics', 'computing', 'computer science', 'excel', 'tableau', 'machine',
                       'programming', 'receptionist'])
    df_out = df_text.apply(axis=1, 
                           func=lambda rec: [float(rec['text'].count(kw) > 0) for kw in keywords],
                           result_type='expand')
    df_out.columns = keywords
    return df_out

df_text = ser_desc.pipe(preprocess) # field 'text' contains nltk Text objs
df_kw = get_keyword_presence(df_text)

def get_keyword_presence(df_text: pd.DataFrame):
    ''' Creates a data frame containing counts of keywords.
    ''' 
    keywords = sorted(['analyst', 'analysis', 'analytical', 'data', 'prediction', 'predictive',
                       'sql', 'python', 'r', 'digital', 'software', 'automation', 'automate',
                       'maths', 'mathematics', 'physics', 'etl', 'informatics', 'bioinformatics',
                       'statistics', 'computing', 'computer science', 'excel', 'tableau', 'machine',
                       'programming', 'receptionist'])
    df_out = df_text.apply(axis=1, 
                           func=lambda rec: [float(rec['text'].count(kw) > 0) for kw in keywords],
                           result_type='expand')
    df_out.columns = keywords
    return df_out

#### DASH STUFF


# Want to develop a tool that has a time slider and renders the headlines
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Intialize app obj
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

example_json_fp = '../data/example.json'
with open(example_json_fp, 'r', encoding='utf-8') as f:
    example_json = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)

# Define app layout
element_header = [
    dcc.Markdown('''

_NHS Wales Data Hackathon, 4th and 5th November 2020 with the WMC, WHAN and SeRP_

# **Classifying job roles: An NLP challenge using NHS Job descriptions**

This app summarizes the project and explores the properties of vacancy\
 descriptions from the [NHS Jobs website](https://www.jobs.nhs.uk/).

The scripts and requirements for this application are available through \
[this Github repository](https://github.com/stochastictalk/wmchack).

---

## **Project overview**
#### **[1. Data retrieval and Storage](#sec1)**  
#### **[2. Preprocessing the Vacancy Descriptions](#sec2)**
#### **[3. Analysis and Visualization](#sec3)**

---
'''),

dhtml.A('1. Data Retrieval and Storage', href='#sec1',
        style={'font-size':'24px', 'font-weight':'bold'}),
dhtml.Br(),
dcc.Markdown(
'''
 **Summary**  
 1. Scraped vacancy descriptions from NHS Jobs as separate local JSON files.  
 2. Merged JSON files into a table and saved to a 16MB Feather file.  
 Relevant scripts:  
* `/scripts/job_description_scraper.py`  
* first section of `/scripts/job_description_analysis.ipynb`  
  
  
**Details**  

 Vacancy descriptions were scraped from `jobs.nhs.uk` and written to\
 disk as JSON files. 

 HTTP headers needed to be spoofed to look like they were coming from a browser. 
 
 Not all current vacancy descriptions on NHS Jobs were captured.
 
 Some vacancy pages\
 did not serve the vacancy information in the correct format - this was\
 true for about 1 in 10 vacancies.

 Accessing each vacancy's page was the bottleneck in retrieving\
 vacancy descriptions. Although the capture script ran for ~2 hours,
 only ~4000 of ~17000 current vacancies were scraped.

The JSON captured from a vacancy page allowed descriptions and meta data\
to be extracted relatively easily.

An example of the JSON for a single vacancy:  
```''' +
 example_json +
'''
```
'''),

dhtml.Br(), dhtml.Br(),
dhtml.A('2. Preprocessing the Vacancy Descriptions', href='#sec2',
        style={'font-size':'24px', 'font-weight':'bold'}),
dhtml.Br(),
dcc.Markdown('''
 **Summary**  
 1. Stripped HTML entities and tags.  
 2. Stripped newline characters.  
 3. Cast to lowercase.  
 4. Removed stop words.  
 Relevant script:  
 * `/scripts/job_description_analysis.ipynb`


 **Details**  
Example input to the preprocessing pipeline, from [this job ad](''' +
ser_desc.index[0] +
'''):    
```
''' +
ser_desc.iloc[0] +
'''
```

Corresponding output from preprocessing pipeline:  

```  
''' +
"['" + "', '".join(list(df_text['text'][0])) + "']" +
'''

```  
'''),

dhtml.Br(), dhtml.Br(),
dhtml.A('3. Analysis & Visualization', href='#sec3',
        style={'font-size':'24px', 'font-weight':'bold'}),
dhtml.Br(),


dhtml.Img(src='https://github.com/stochastictalk/wmchack/blob/main/data/img/001.png?raw=true',
          width=600),

dhtml.Img(src='https://github.com/stochastictalk/wmchack/blob/main/data/img/002.png?raw=true',
          width=600)

]

app.layout = dhtml.Div([
    *element_header
], style={'width': '60%', 'margin':'auto'})


# Define callbacks



if __name__ == '__main__':
	app.run_server(debug=True)