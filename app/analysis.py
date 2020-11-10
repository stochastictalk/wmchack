# -*- utf-8 -*-

# Created: 7th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: data processing functions for viz.py

from nltk.corpus.reader import CategorizedPlaintextCorpusReader
import pandas as pd
import html
import os
import string
from nltk.corpus import stopwords
import numpy as np
import sparse
from tqdm import tqdm
import pickle

STOPWORDS_SET = set(stopwords.words('english'))
PUNCTUATION_SET = set(v for v in string.punctuation)
STOPWORDS_PUNCTUATION_SET = PUNCTUATION_SET.union(STOPWORDS_SET)


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
        write_corpus into Python as dictionary.

        Args:
            corpus_id: name of corpus directory.

        Returns:
            dict: keys are fileids, values are text strings.
    '''
    corpus_root_dir = './' + corpus_id
    reader = CategorizedPlaintextCorpusReader(
                corpus_root_dir,
                r'.*\.txt', # fileid pattern,
                cat_pattern=r'.*___(.+)\.txt',
                encoding='utf8')
    corpus_dct = {fileid: list(reader.words(fileids=[fileid])) 
                  for fileid in reader.fileids()}
    return corpus_dct


def n_fileids(corpus_raw: dict):
    ''' Returns raw corpus's number of fileids.
    '''
    return len(corpus_raw.keys())


def n_words(corpus_raw: dict):
    ''' Returns total number of words in corpus.
    '''
    return sum(len(v) for v in corpus_raw.values())


def file_lengths(corpus_raw: dict):
    ''' Returns number of words for each file in Reader.
    '''
    return [len(v) for v in corpus_raw.values()]


def cdf(X):
    ''' Plot cumulative distribution function for sample X.
    
        Args:
            X: np.array list containing sampled values.
            
        Returns:
            x, P(X <= x): both numpy arrays
    '''
    X = np.array(X)
    step_size = (max(X) - min(X))/1e4
    x = np.arange(min(X) - step_size, max(X) + step_size,
                  step_size)
    return x, np.array([np.mean(X <= v) for v in x])


def remove_stopwords_and_punctuation(tokens: list):
    return([t for t in tokens if t not in STOPWORDS_PUNCTUATION_SET])


def get_corpus_words(corpus_raw: dict):
    ''' Returns tokenised corpus with stopwords and punctuation stripped.
    '''
    corpus_words = {
        fileid: remove_stopwords_and_punctuation(filetxt)
        for fileid, filetxt in corpus_raw.items()
    }
    return corpus_words


def get_corpus_types(corpus_words: dict):
    ''' Returns unique tokens in each file of corpus.
    '''
    corpus_types = {
        fileid: set(file_tokens)
            for fileid, file_tokens in corpus_words.items()
    }
    return corpus_types


def get_token_index(corpus_types: dict):
    ''' Returns unique tokens in corpus.
    '''
    lexicon = set.union(*corpus_types.values())
    token_index = {token: j for j, token in enumerate(lexicon)}
    return token_index

def get_fileid_index(corpus_types: dict):
    ''' Returns sorted fileids of corpus_types as list.
    '''
    return {fileid: j for j, fileid in enumerate(corpus_types.keys())}

def term_frequency(corpus_types: dict,
                   corpus_words: dict,
                   fileid_index: dict,
                   token_index: dict):
    ''' Returns sparse.COO of token frequencies by fileid.

        Rows are fileids, columns are tokens.
    '''
    coords = []
    data = []
    for fileid, i in tqdm(fileid_index.items()): # i is row index
        for token in corpus_types[fileid]:
            j = token_index[token] # j is col index
            data.append(corpus_words[fileid].count(token))
            coords.append((i, j))
    
    s_tf = sparse.COO(coords=np.array(coords).transpose(), 
                      data=np.array(data),
                      shape=(len(fileid_index.keys()),
                             len(token_index.keys())))
    return s_tf


def inv_document_frequency(s_tf: sparse.COO):
    ''' Returns sparse.COO of number of documents a token appears in.

        token: log(N) - log(number_of_files_containing_token)
    '''
    s_invdocfreq = np.log(s_tf.shape[0]) - np.log((s_tf > 0).sum(axis=0))
    return s_invdocfreq.todense()


def tf_idf(corpus_types: dict, corpus_words: dict,
           fileid_index: dict, token_index: dict):
    ''' Returns pd.DataFrame of tf_idf values for each fileid/token combo.
    '''
    s_termfreq = term_frequency(corpus_types, corpus_words,
                                fileid_index, token_index)
    m_invdocfreq = inv_document_frequency(s_termfreq) # dense for fast index
    
    # nb if token doesn't appear in corpus_types[fileid] then its tf-idf is 0.
    termfreq_coords_n_data = np.vstack([s_termfreq.coords,
                                        s_termfreq.data]).transpose()
                                        # each row is (i, j, termfreq)
    tfidf_coords = s_termfreq.coords
    tfidf_data = [] # i is row (fileid) index, j is col (token) index
    for i, j, termfreq in tqdm(termfreq_coords_n_data):
        tfidf_data.append(termfreq*m_invdocfreq[j])
        
    s_tf_idf = sparse.COO(coords=np.array(tfidf_coords),
                          data=np.array(tfidf_data),
                          shape=(len(fileid_index.keys()),
                                 len(token_index.keys())))
    return s_termfreq, s_tf_idf


def similar_words(query_word: str, df_tf_idf: pd.DataFrame, N=10):
    ''' Returns words that are specific to documents that containing the query word.
    '''
    # Get tf_idf submatrix of documents that contain query word
    df_docs = df_tf_idf.query(query_word + ' > 0')
    
    # Return top n words with highest mean tf-idf
    return(df_docs.mean(axis=0).nlargest(n=N))


def jacard_index(df_tf: pd.DataFrame, fileid):
    ''' Returns Jacard index data frame.
    
        This function carries its calculations in using the sparse lib.
        https://sparse.pydata.org/en/stable/generated/sparse.html
        Operating directly on DataFrames is too slow, while
        standard numpy arrays consume too much memory.
    '''
    fileids = df_tf.index
    s_inc = sparse.COO((df_tf > 0).values) # word incidence matrix
    i = df_tf.index.get_loc(fileid)
    s_inc_row_stretched = s_inc[i, :]*sparse.ones(shape=s_inc.shape)
    tmp = np.stack([s_inc, s_inc_row_stretched], axis=-1)
    types_in_intersection = tmp.min(axis=-1).sum(axis=1)
    types_in_union = tmp.max(axis=-1).sum(axis=1)
    # nb a 'type' is an element of set(words_in_document)
    
    m_ji = types_in_intersection.todense()/types_in_union.todense()
    ser_ji = pd.Series(m_ji, index=fileids)
    
    return ser_ji.sort_values(ascending=False)

def load_viz_data():
    ''' Loads dictionary containing data for visualizations.

        Reads dictionary elements from .pkl files in ./pkl/

        If these .pkl files do not exist, the elements are computed from
        scratch.
    '''
    corpus_id = 'uk'
    data_vars = ['corpus_raw', 'n_files', 'n_words',
                'corpus_types', 'corpus_words',
                'token_index', 'fileid_index',
                's_termfreq', 's_tfidf']
    pkl_fp_dct = {k: os.path.join('.', 'pkl', k + '.pkl') for k in data_vars}
    data = {}

    # load pickled objs if they exist
    if os.path.exists(os.path.join('.', 'pkl', 'corpus_raw.pkl')):
        for k in pkl_fp_dct.keys():
            with open(pkl_fp_dct[k], 'rb') as f:
                data[k] = pickle.load(f)
    
    # otherwise create and pickle them
    else: 
        data['corpus_raw'] = read_corpus('uk')
        data['n_files'] = n_fileids(data['corpus_raw'])
        data['n_words'] = n_words(data['corpus_raw'])
        data['corpus_words'] = get_corpus_words(data['corpus_raw'])
        data['corpus_types'] = get_corpus_types(data['corpus_words'])
        data['token_index'] = get_token_index(data['corpus_types'])
        data['fileid_index'] = get_fileid_index(data['corpus_types'])
        data['s_termfreq'], data['s_tfidf'] = tf_idf(data['corpus_types'],
                                                     data['corpus_words'],
                                                     data['fileid_index'],
                                                     data['token_index'])
        for k in data.keys():
            with open(pkl_fp_dct[k], 'wb') as f:#
                pickle.dump(data[k], f)
        
    return data