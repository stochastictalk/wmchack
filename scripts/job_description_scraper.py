# -*- utf-8 -*-

# Created: 4th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: Scrapes job descriptions from the NHS Jobs
#          website and writes them to a JSON list.

import requests
import bs4 as bs
import json

# example URL: https://www.jobs.nhs.uk/xi/vacancy/916247105
# questions:
#   how can we identify job description URLs?
#   how can we extract the information from the page?

def write_job_description_to_json(url: str):
    ''' Parses a job description web page and writes its fields
        to a JSON file.

        Args:
            url: URL to a page with the same template as
                 https://www.jobs.nhs.uk/xi/vacancy/916243341.

        Returns:
            nothing
    '''
    page_id = url.split('/')[-1]
    soup = bs.BeautifulSoup(requests.get(url).text, 'html.parser')
    json_str = soup.find('script', # job description in JSON 
                          attrs={'id':'jobPostingSchema'}).contents[0]
    page_dct = json.loads(json_str)
    with open('../data/'+page_id+'.json', 'w', encoding='utf-8') as f:
        json.dump(page_dct, f)

url = 'https://www.jobs.nhs.uk/xi/vacancy/916243341'
write_job_description_to_json(url)