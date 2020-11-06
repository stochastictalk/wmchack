# -*- utf-8 -*-

# Created: 4th November 2020
# Authors: Jerome Wynne (jeromewynne@das-ltd.co.uk)
#          Mark Drakeford
# Environment: wmchack
# Summary: Scrapes job descriptions from the NHS Jobs
#          website and writes them to a JSON list.
# Contents:
#   fnc write_vacancy_to_json
#   fnc write_vacancies_to_json
#   fnc write_vacancy_urls_to_file
# TODO:
#   enable running multiple times for scraping at different periods of time
#   include write merge JSON to dataframe, write to Feather

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

LOG_PATH = '..\\logs\\scraper.log'
logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format=
                        '%(asctime)s:%(filename)s:%(funcName)s: %(message)s')

# header spoofing is necessary otherwise NHS Job does not return page
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
TMP_FILEPATH = '.\\tmp\\scraper.tmp' # in case the script is interrupted
URLS_FP = '..\\data\\vacancy_page_urls.txt'
JSON_FP = '..\\data\\json\\'
IGNORED_IDS_FP = '..\\data\\ignored_page_ids.txt'

def graceful_request_to_soup(url):
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

def write_vacancy_urls_to_file():
    ''' Writes vacancy URLs to file.
    '''
    print('URL scraper intialised. Refer to {} for status updates.'.format
                                                                    (LOG_PATH))
    search_url_prefix = "https://www.jobs.nhs.uk/xi/search_vacancy?action=page&page="

    try: # if scraper.tmp exists, contains 'n_pages,last_page_scraped'
        logging.info('Resuming scrape.')
        with open(TMP_FILEPATH, 'r', encoding='utf-8') as f:
            s = f.read()
            n_pages, start_page_n = [int(v) for v in s.split(',')]
            start_page_n += 1

    except FileNotFoundError: # if scraper.tmp does not exist
        logging.info('Starting scrape.')
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
        soup = graceful_request_to_soup(search_url_prefix + str(page_n))

        # use bs to get vacancy page URL
        for v in soup.find_all('div', attrs={'class':'vacancy'}):
            rel_path = v.find('h2').find('a')['href']

            # write vacancy page URL to file
            with open(URLS_FP, 'a', encoding='utf-8') as f:
                f.write("https://www.jobs.nhs.uk" + rel_path + '\n')

        if page_n < n_pages: # update number of last page scraped in scraper.tmp
            with open(TMP_FILEPATH, 'w', encoding='utf-8') as f:
                f.write(str(n_pages) + ',' + str(page_n))
        if page_n == n_pages: # delete scraper.tmp
            os.remove(TMP_FILEPATH)
            logging.info('All vacancy page URLs scraped successfully.')

def write_vacancies_to_json():
    logging.info('Scraping vacancy pages based on URLs in {}.'.format(URLS_FP))
    # get vacancy ids that have already been captured
    captured_ids = set([v.split('\\')[-1][:-5] 
                                    for v in glob(JSON_FP + '*.json')])
    try:
        with open(IGNORED_IDS_FP, 'r', encoding='utf-8') as f:
            ignored_ids = set(f.read().split('\n'))
    except FileNotFoundError:
        ignored_ids = set()

    ids_to_skip = captured_ids.union(ignored_ids)

    urls_file = open(URLS_FP, 'r', encoding='utf-8')
    list_of_urls = urls_file.read().splitlines()
    n_urls = len(list_of_urls)
    for j, page_url in enumerate(list_of_urls):
        logging.info('Scraping vacancy description page {} of {}.'.format(j+1,
                                                                     n_urls))
        page_id = page_url.split('/')[-1] # is a string
        if page_id not in ids_to_skip: 
            try:
                write_vacancy_to_json(page_id) # download
            except AttributeError: # occurs if page isn't structured correctly
                # add id to ignored ids
                with open(IGNORED_IDS_FP, 'a', encoding='utf-8') as f:
                    f.write(page_id + '\n')
                logging.info('Page format incorrect, appending page id to {} and skipping.'.format(IGNORED_IDS_FP))
                continue
        else:
            logging.info('Skipping vacancy page {}.'.format(page_id))
    
    urls_file.close()

def write_vacancy_to_json(page_id: str):
    ''' Parses a job description web page and writes its fields
        to a JSON file.
    '''
    url = ' https://www.jobs.nhs.uk/xi/vacancy/' + page_id
    logging.info('Scraping vacancy description at {}.'.format(url))
    soup = graceful_request_to_soup(url)
    json_str = soup.find('script', # job description in JSON (see end of file)
                          attrs={'id':'jobPostingSchema'}).contents[0]
    page_dct = json.loads(json_str)
    with open(JSON_FP + page_id + '.json', 'w', encoding='utf-8') as f:
        json.dump(page_dct, f)

#write_vacancy_urls_to_file()
write_vacancies_to_json()


# Example of source JSON file
# {
#     "@context": "http://schema.org",
#     "@type": "JobPosting",
#     "baseSalary": {
#         "@type": "MonetaryAmount",
#         "currency": "GBP",
#         "value": {
#             "@type": "QuantitativeValue",
#             "maxValue": "38694",
#             "minValue": "38694",
#             "unitText": "YEAR",
#             "value": "\u00a338,694 per annum pro rata"
#         }
#     },
#     "datePosted": "2020-10-26T16:16:02+0000",
#     "description": "&lt;p&gt;&lt;strong&gt;&lt;span&gt;Weston General Hospital is looking to appoint two Clinical Fellows (CT1/2) to our Trust in General Surgery. There is also some financial support to work towards your MRCS qualification. There are dedicated MRCS sessions and for the last 3 years general surgery have achieved 100% pass with all their trainees in securing their MRCS.&lt;/span&gt;&lt;/strong&gt;&lt;/p&gt;\n&lt;p&gt;&lt;span&gt;When based in Surgery you will be involved in the care of all general surgical patients at WGH. The surgical specialties provided are upper GI, Colorectal, Breast and general surgery. There is a visiting vascular service. The General surgery department offers care to a wide range of UGI/General Surgery conditions and strives to provide patients with individualised clinic care. Together with our gastroenterology colleagues, we provide an endoscopy service (including gastroscopy and ERCP).&lt;/span&gt;&lt;/p&gt;\n&lt;p&gt;&lt;span&gt;Weston hospital is pleased to be able to provide UKBA sponsorships for candidates who require tier 5 through the Academy of Medical Royal Colleges or alternatively Tier 2 dependent on qualifications already gained. GMC registration requires achievement of an overall score of 7.5 in IELTS.&lt;/span&gt;&lt;/p&gt;\n&lt;p&gt;&lt;strong&gt;&lt;span&gt;The Hospital:&lt;/span&gt;&lt;/strong&gt;&lt;/p&gt;\n&lt;p&gt;&lt;span&gt;North Somerset, the surrounding county, has lovely coastline and cliff tops and superb English countryside. You&#39;ll find yourself visiting the Mendip Hills, the Quantocks and Cheddar Gorge sooner or later. The large, diverse cities of Bristol and Bath are only a short journey by car or train and our convenient location just off Junction 21 of the M5 mean the rest of Somerset, Devon and Cornwall are virtually on the doorstep.&lt;/span&gt;&lt;/p&gt;\n&lt;p&gt;&lt;span&gt;University Hospitals Bristol and Weston NHS Foundation Trust is committed to safeguarding and promoting the welfare of children, young people and vulnerable adults. All staff must be aware of, and follow Weston Area Health Trust guidance and policies on Safeguarding Children and Vulnerable adults and it is your duty to report any concerns you may have through your line manager and the Trust\u2019s designated Safeguarding Lead.&lt;/span&gt;&lt;/p&gt;\n&lt;p&gt;For further details / informal visits contact:&lt;/p&gt;\n&lt;p&gt;NameKaren Fifield/Reuben WestJob titleOperational Service Manager for General SurgeryEmail addresskaren.fifield@uhbw.nhs.ukTelephone number01934 636363&lt;/p&gt;",
#     "employmentType": "FULL_TIME",
#     "hiringOrganization": {
#         "@type": "Organization",
#         "logo": "https://www.jobs.nhs.uk/xi/db_image/logo/120778.png",
#         "name": "University Hospitals Bristol and Weston NHS Foundation Trust",
#         "url": "https://www.jobs.nhs.uk/xi/agency_info/?agency_id=120778"
#     },
#     "industry": "Healthcare",
#     "jobLocation": {
#         "@type": "Place",
#         "address": {
#             "@type": "PostalAddress",
#             "addressCountry": "GB",
#             "addressLocality": "Weston General Hospital, Weston-super-Mare",
#             "postalCode": "BS23 4TQ"
#         },
#         "geo": {
#             "@type": "GeoCoordinates",
#             "latitude": "51.3223",
#             "longitude": "-2.97141"
#         }
#     },
#     "title": "Clinical Fellow (CT1/2) in General Surgery",
#     "url": "https://www.jobs.nhs.uk/xi/vacancy/916243341",
#     "validThrough": "2020-11-08T23:59:59+0000"
# } 