# -*- utf-8 -*-

# Created: 4th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: Scrapes job descriptions from the NHS Jobs
#          website and writes them to a JSON list.

import requests
import bs4 as bs

# example URL: https://www.jobs.nhs.uk/xi/vacancy/916247105
# questions:
#   how can we identify job description URLs?
#   how can we extract the information from the page?

base_url = 'https://www.jobs.nhs.uk/xi/vacancy/'

requests.get()