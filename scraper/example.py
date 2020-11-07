# -*- utf-8 -*-

# Created: 6th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: Demo of how to use scraper.py.

from scraper import scrape_vacancies
from time import time # to generate a timestamp for the scrape

scrape_id: str = 'example'
scrape_vacancies(scrape_id)

