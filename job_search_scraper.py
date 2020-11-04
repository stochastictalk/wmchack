#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 11:33:49 2020

@author: mrkdsmith
"""



import requests
from bs4 import BeautifulSoup
import re



search_url_prefix="https://www.jobs.nhs.uk/xi/search_vacancy?action=page&page="
url_prefix="https://www.jobs.nhs.uk/"

def list_job_urls(search_url_prefix, url_prefix):
    ''' Create slise of job

        Args:
            search_url: Search URL

        Returns:
            url_list: list of strings containing job URls. 
    '''
    
    
    headers = {
            'User-Agent': 'Mozilla Firefox 5.0',
            }
#    
#        headers = {
#            'User-Agent': 'Mozilla/5.0',
#            }
#    


    url_list = []
    
    search_url = search_url_prefix + str(1)
    

    page = requests.get(search_url, headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    
    search_url="https://www.jobs.nhs.uk/xi/search_vacancy"
    
    
    job_count_txt = soup.find('span', class_='jobCount').get_text()
    job_count = int(re.sub("[^0-9]", "", job_count_txt))
    
    jobs_per_page=20
    
    page_count = ceil(job_count / jobs_per_page)
    
    
    for i in range(page_count): # g through each page
        
        search_url = search_url_prefix + str(i) # results url for current page
        
        page = requests.get(search_url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for h in soup.find_all('h2'): # for wach h2 tag in html
            url_list.append(url_prefix + h.find('a')['href']) # add the job url to list


    
    return url_list

