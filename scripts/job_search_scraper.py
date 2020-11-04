#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 11:33:49 2020

@author: mrkdsmith
"""

import requests
from bs4 import BeautifulSoup
import re
from math import ceil
from time import sleep
import logging
logging.basicConfig(filename='../logs/info.log', level=logging.INFO,
                    format=
                        '%(asctime)s:%(filename)s:%(funcName)s: %(message)s')

def write_job_description_urls_to_file():
    ''' Writes job description URLs to file.

        Args:
            none

        Returns:
            none 
    '''
    search_url_prefix="https://www.jobs.nhs.uk/xi/search_vacancy?action=page&page="
    headers = {
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

    # test that page can be retrieved (view info.log)
    search_url = search_url_prefix + str(1)
    logging.info('search url: {}'.format(search_url))
    response = requests.get(search_url, headers=headers)
    logging.info('page text: {}'.format(response.text))
    
    # compute number of pages to iterate over
    soup = BeautifulSoup(response.text, 'html.parser')
    job_count_txt = soup.find('span', class_='jobCount').get_text()
    job_count = int(re.sub("[^0-9]", "", job_count_txt))
    jobs_per_page = 20
    page_count = ceil(job_count/jobs_per_page)

    dst_fp = '../data/page_urls.txt'
    start_n = 1

    for i in range(start_n, page_count+1): # iterate over pages
        logging.info('Writing page {} of {}...'.format(i, page_count))
        try:
            r = requests.get(search_url_prefix + str(i),
                             headers=headers,
                             timeout=10)
        except requests.exceptions.ConnectionError:
            logging.info('ConnectionError thrown, retrying in 60 seconds...')
            sleep(60) # take a minute off before retrying

        soup = BeautifulSoup(r.text, 'html.parser')

        for v in soup.find_all('div', attrs={'class':'vacancy'}):
            rel_path = v.find('h2').find('a')['href']
            with open(dst_fp, 'a', encoding='utf-8') as f:
                f.write("https://www.jobs.nhs.uk" + rel_path)

list_job_urls()