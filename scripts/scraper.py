# -*- utf-8 -*-

# Created: 4th November 2020
# Authors: Jerome Wynne (jeromewynne@das-ltd.co.uk)
#          Mark Drakeford
# Environment: wmchack
# Summary: Scrapes job descriptions from the NHS Jobs
#          website and writes them to a JSON list.
# Contents:
#   fnc scrape_vacancies
#   fnc graceful_request_to_soup
#   fnc write_vacancy_urls_to_file
#   fnc write_vacancies_to_json
#   fnc __write_vacancy_to_json
#   fnc write_json_to_feather
# Description:
#   This file contains a function, 
#       scrape_vacancies
#   that can be used to snapshot all vacancies on NHS Jobs at a 
#   particular point in time.
#     
#   scrape_vacancies accepts only one argument, 
#       scrape_id
#   which identifies the scrape instance. 
#   A good choice of scrape_id is 
#       str(int(time.time())).
#
#   Because the scrape takes several hours, scrape_vacancies
#   is designed to recover existing scrape progress if interrupted.
#   All you need to do to recoveer existing progess is to call
#       scrape_vacancies(scrape_id)
#   using the scrape_id of the scrape that was interrupted.
#
#   Files output:
#       ./data/scrape_id/json/*.json
#       ./data/scrape_id/vacancy_page_urls.csv
#       ./data/scrape_id/ignored_vacancy_page_urls.csv
#       ./data/scrape_id/vacancy_descriptions.feather
#       ./tmp/scrape_id.log
#       ./tmp/scrape_id.state
#       ./tmp/scrape_id_page.tmp

import requests
import bs4 as bs
import json
from glob import glob
import pandas as pd
from time import sleep
import logging
import os
import re
from math import ceil

# header spoofing is necessary otherwise NHS Job does not return pages
HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': 'general_session=F69F3B6C1E8911EB8AA577ACEE0D0942',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
    }
TIME_BETWEEN_UNSUCCESSFUL_REQUESTS = 60 # seconds
TIMEOUT = 10 # requests.get timeout, seconds
JOBS_PER_PAGE = 20.
STATE_URLS = '0'
STATE_JSON = '1'
STATE_FEATHER = '2'
STATE_END = '3'

def scrape_vacancies(scrape_id: str):
    ''' Scrapes vacancy page URLs from NHS Jobs, downloads vacancy
        descriptions at these URLs to JSON, merges these JSON
        files into a Feather dataframe.

        Scrape status is tracked via file ../data/scrape_id.status.
        Status codes:
            0: scraping vacancy descriptions urls to vacancy_page_urls.csv
            1: scraping vacancy descriptions from urls to .json files
            2: merging .json files into dataframe and writing to Feather
            3: scrape complete
    '''
    # check if required directories exist (make it if not)
    dirs = [
            os.path.join('.', 'data'),
            os.path.join('.', 'data', scrape_id),
            os.path.join('.', 'tmp')
    ]
    for dir_path in dirs:
        if not os.path.exists(dir_path): os.mkdir(dir_path)

    # check if tmp directory exists (make it if not)
    tmp_dir = os.path.join('.', 'tmp')
    if not os.path.exists(tmp_dir): os.mkdir(tmp_dir)

    # configure log
    log_path = os.path.join('.', 'tmp', scrape_id + '.log')
    logging.basicConfig(filename=log_path, level=logging.INFO,
        format='%(asctime)s:%(filename)s:%(funcName)s: %(message)s')
    logging.info('Scraper intialized. scrape_id is \'{}\'.'.format(scrape_id))

    # check if scrape has previously been started/completed
    state_fp = os.path.join('.', 'tmp', scrape_id + '.state')
    try:
        with open(state_fp, 'r', encoding='utf-8') as state_f:
            state = state_f.read()
    except FileNotFoundError:
        state = STATE_URLS
        with open(state_fp, 'w', encoding='utf-8') as state_f:
            state_f.write(state)

    logging.info('Entered state {}'.format(state))

    switchboard = { # maps states to functions
        STATE_URLS: write_vacancy_urls_to_file, # scrape URLs from index
        STATE_JSON: write_vacancies_to_json, # scrape JSON at URLs
        STATE_FEATHER: write_json_to_feather # write JSON to Feather
    }

    while state != STATE_END:
        state = switchboard[state](scrape_id)
        with open(state_fp, 'w', encoding='utf-8') as state_f:
            state_f.write(state)
        logging.info('Entered state {}. Updated {}.'.format(
            state, state_fp))

    logging.info('Scrape \'{}\' complete.'.format(scrape_id))


def graceful_request_to_soup(url: str):
    ''' requests.get that handles errors, retries.
    '''
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        soup = bs.BeautifulSoup(r.text, 'html.parser')

    except (requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout, 
            requests.exceptions.ReadTimeout):
        logging.info('ReadTimeout or ConnectTimeout thrown, retrying in 60 seconds...')
        sleep(TIME_BETWEEN_UNSUCCESSFUL_REQUESTS) # wait a bit before retrying
        soup = graceful_request_to_soup(url)
    return soup


def write_vacancy_urls_to_file(scrape_id: str):
    ''' Writes vacancy URLs to file.

        Returns STATE_JSON.
    '''
    urls_fp = os.path.join('.', 'data', scrape_id, 'vacancy_page_urls.csv')
    urls_tmp_fp = os.path.join('.', 'tmp', scrape_id + '_page.tmp') # tracks n_pages,
                                                                    # pages_read

    search_url_prefix = "https://www.jobs.nhs.uk/xi/search_vacancy?action=page&page="

    try: # if urls_scrape_id.tmp exists, contains 'n_pages,last_page_scraped'
        with open(urls_tmp_fp, 'r', encoding='utf-8') as f:
            s = f.read()
            n_pages, start_page_n = [int(v) for v in s.split(',')]
            start_page_n += 1

    except FileNotFoundError: # if urls_scrape_id.tmp does not exist
        page1_url = search_url_prefix + str(1)
        logging.info('Getting page count from page {}.'.format(page1_url))
        soup = graceful_request_to_soup(page1_url)
        job_count_txt = soup.find('span', class_='jobCount').get_text()
        job_count = float(re.sub("[^0-9]", "", job_count_txt))
        n_pages = ceil(job_count/JOBS_PER_PAGE)
        logging.info('Determined that there are {} pages to iterate over.'
                        .format(n_pages))
        start_page_n = 1

    # iterate over pages of NHS Jobs search results,
    # writing URLs of pages to file
    for page_n in range(start_page_n, n_pages+1):
        logging.info('Scraping URLs from page {} of {}.'.format(page_n,
                                                                n_pages))

        # get page page_n of search results
        soup = graceful_request_to_soup(search_url_prefix + str(page_n))

        # use bs to get vacancy page URLs
        for v in soup.find_all('div', attrs={'class':'vacancy'}):
            rel_path = v.find('h2').find('a')['href']

            # write vacancy page URL to file
            with open(urls_fp, 'a', encoding='utf-8') as f:
                f.write("https://www.jobs.nhs.uk" + rel_path + '\n')

        if page_n < n_pages: # update number of last page scraped
            with open(urls_tmp_fp, 'w', encoding='utf-8') as f:
                f.write(str(n_pages) + ',' + str(page_n))
        if page_n == n_pages: # delete urls_scrape_id.tmp
            os.remove(urls_tmp_fp)
            logging.info('All vacancy page URLs scraped successfully.')

    return STATE_JSON

def write_vacancies_to_json(scrape_id: str):
    ''' Returns STATE_FEATHER.
    '''
    json_dir = os.path.join('.', 'data', scrape_id, 'json', '')
    try: # make directory for json if it doesn't already exist
        os.mkdir(json_dir)
    except FileExistsError:
        pass
    
    ignored_ids_fp = os.path.join('.', 'data', scrape_id,
                                  'ignored_vacancy_page_urls.csv')
    urls_fp = os.path.join('.', 'data', scrape_id, 
                           'vacancy_page_urls.csv')

    logging.info('Scraping vacancy pages based on URLs in {}.'.format(urls_fp))
    # get vacancy ids that have already been captured
    captured_ids = set([v.split('\\')[-1][:-5] 
                                    for v in glob(json_dir + '*.json')])
    try: # get vacancy ids that are to be ignored
        with open(ignored_ids_fp, 'r', encoding='utf-8') as f:
            ignored_ids = set(f.read().split('\n'))
    except FileNotFoundError:
        ignored_ids = set()

    ids_to_skip = captured_ids.union(ignored_ids)

    # load urls to scrape descriptions from
    with open(urls_fp, 'r', encoding='utf-8') as urls_file:
        list_of_urls = urls_file.read().splitlines()
        n_urls = len(list_of_urls)
    
    for j, page_url in enumerate(list_of_urls):
        logging.info('Scraping vacancy description page {} of {}.'.format(j+1,
                                                                     n_urls))
        page_id = page_url.split('/')[-1] # is a string
        if page_id not in ids_to_skip: 
            try:
                __write_vacancy_to_json(dst_dir=json_dir,
                                        page_id=page_id) # download
            except AttributeError: # occurs if page isn't structured correctly
                # add id to ignored ids
                with open(ignored_ids_fp, 'a', encoding='utf-8') as f:
                    f.write(page_id + '\n')
                logging.info('Page format incorrect, appending page id to {} and skipping.'.format(ignored_ids_fp))
                continue # move on to next page_url
        else:
            logging.info('Skipping vacancy page {}.'.format(page_id))

    return STATE_FEATHER


def __write_vacancy_to_json(dst_dir: str, page_id: str):
    ''' Parses a job description web page and writes its fields
        to a JSON file.
    '''
    url = ' https://www.jobs.nhs.uk/xi/vacancy/' + page_id
    logging.info('Scraping vacancy description at {}.'.format(url))
    soup = graceful_request_to_soup(url)
    json_str = soup.find('script', # job description in JSON (see end of file)
                          attrs={'id':'jobPostingSchema'}).contents[0]
    page_dct = json.loads(json_str)
    with open(dst_dir + page_id + '.json', 'w', encoding='utf-8') as f:
        json.dump(page_dct, f)


def write_json_to_feather(scrape_id: str):
    ''' Reads all .json files in /data into dataframe, saves dataframe
        in Feather format.

        Returns STATE_END.
    '''
    logging.info('Initialized write of JSON files to Feather dataframe.')
    json_dir = os.path.join('.', 'data', scrape_id, 'json', '')
    json_fps = glob(json_dir + '*.json')
    list_of_page_dct = []
    for fp in json_fps: # read all of the files into a list of dicts
        with open(fp, 'r', encoding='utf-8') as f:
            list_of_page_dct += [json.load(f)]
    
    # flatten the list of dicts to a DataFrame
    df = pd.json_normalize(list_of_page_dct)

    # write it to a Feather file
    dst_fp = os.path.join('.', 'data', scrape_id, 
                          'vacancy_descriptions.feather')
    df.to_feather(dst_fp)
    logging.info('Wrote JSON files to Feather dataframe at {}.'.format(dst_fp))

    return STATE_END