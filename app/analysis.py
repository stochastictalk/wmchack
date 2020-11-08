# -*- utf-8 -*-

# Created: 7th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: functions for a pp.py

from nltk.corpus.reader import CategorizedPlaintextCorpusReader
import pandas as pd
import html
import os

def load_descriptions(feather_filepath: str):
    ''' Reads job descriptions from Feather file as NLTK Text obj.
    '''
    df = pd.read_feather(feather_filepath)
    df = df.loc[:, ['title', 'description', 'url']]
    df['description'] = df['description'].pipe(clean_descriptions)
    df['id'] = df['url'].str.slice(start=-9)
    return df

def write_corpus(feather_filepath: str, corpus_id: str):
    df = load_descriptions(feather_filepath)

    # need to remove special chars from job titles
    pattern = r'[\\/*?:"<>|]'
    df['safe_title'] = df['title'].str.replace(pat=pattern, repl='!')
    df['dst_fp'] = ('./' + corpus_id + '/' + df['id'] + '___' +
                    df['safe_title'] + '.txt')
    os.mkdir(corpus_id)
    for _, ser in df.iterrows():
        with open(ser['dst_fp'], 'w', encoding='utf-8') as f:
            f.write(ser['description'])

def read_corpus(corpus_id: str):
    corpus_root_dir = './' + corpus_id
    reader = CategorizedPlaintextCorpusReader(
                corpus_root_dir,
                r'.*\.txt', # fileid pattern,
                cat_pattern=r'.*___(.+)\.txt')
    return reader

def clean_descriptions(ser_desc: pd.Series):
    # replace entities
    ser_desc = ser_desc.apply(lambda value: html.unescape(value))
    # strip html tags 
    ser_desc = ser_desc.str.replace(pat='<\/?[^>]*>', repl='')
    # strip newline chars
    ser_desc = ser_desc.str.replace(pat='\\n', repl=' ')
    # cast to lowercase
    ser_desc = ser_desc.str.lower()
    #ser_desc = ser_desc.apply(lambda value: nltk.word_tokenize(value)) # splits string into list of tokens
    #ser_desc = ser_desc.apply(lambda value: nltk.Text(value))
    return ser_desc