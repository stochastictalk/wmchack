# -*- utf-8 -*-

# Created: 7th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: functions for app.py

from nltk.corpus.reader import CategorizedPlaintextCorpusReader
import pandas as pd
import html
import os

def load_descriptions_as_df(feather_filepath: str):
    ''' Reads job descriptions from Feather file as pd.DataFrame.

        Descriptions are stripped of HTML tags and entities and cast
        to lowercase.

        Args:
            feather_filepath: filepath of Feather file output by 
                              scraper.py.

        Returns:
            pd.DataFrame: contains metadata and vacancy descriptions.

    '''
    df = pd.read_feather(feather_filepath)
    df = df.loc[:, ['title', 'description', 'url']]
    df['description'] = df['description'].pipe(clean_descriptions)
    df['id'] = df['url'].str.slice(start=-9)
    return df


def clean_descriptions(ser_desc: pd.Series):
    ''' Cleans a pd.Series of vacancy description strings.
    '''
    # replace entities
    ser_desc = ser_desc.apply(lambda value: html.unescape(value))
    # strip html tags 
    ser_desc = ser_desc.str.replace(pat='<\/?[^>]*>', repl='')
    # strip newline chars
    ser_desc = ser_desc.str.replace(pat='\\n', repl=' ')
    # cast to lowercase
    ser_desc = ser_desc.str.lower()
    return ser_desc


def write_corpus(feather_filepath: str, corpus_id: str):
    ''' Writes vacancy descriptions to plaintext files with names
        containing vacancy id and job title.

        Creates directory 'corpus_id' in current working directory.

        Args:
            feather_filepath: filepath of Feather file output by 
                              scraper.py.
            corpus_id: your choice of name for the corpus directory.

        Returns:
            nothing
    '''
    df = load_descriptions_as_df(feather_filepath)

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
    ''' Reads the directory of plaintext files written by 
        write_corpus into Python as an NLTK CategorizedReader.

        Categories are job titles.

        Args:
            corpus_id: name of corpus directory.

        Returns:
            CategorizedPlaintextCorpusReader: NLTK categorized reader obj.
    '''
    corpus_root_dir = './' + corpus_id
    reader = CategorizedPlaintextCorpusReader(
                corpus_root_dir,
                r'.*\.txt', # fileid pattern,
                cat_pattern=r'.*___(.+)\.txt',
                encoding='utf8')
    return reader