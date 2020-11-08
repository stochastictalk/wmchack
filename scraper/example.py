# -*- utf-8 -*-

# Created: 6th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: Demo of how to use scraper.py.

# To scrape NHS Jobs you need a cookie that identifies your search.
# You can get this cookie by following these steps.
# 1. Open your web browser and go to www.jobs.nhs.uk.
# 2. Click 'Accept all cookies'.
# 3. Specify your search terms then press 'Search'.
# 4. You will see the first page of search results. In your browser,
#    open Developer Tools > Network, then refresh the page by pressing F5.
# 5. You should see the Network pane populate with HTTP exchanges,
#    the first of which will be called 'search_vacancy/'. Click on it.
# 6. In the 'Headers' frame, scroll down to 'Request Headers' and find
#    the field 'cookie'. Copy its value.
# 7. Pass the cookie to scrape_vacancies() as a string.

from scraper import scrape_vacancies

scrape_id: str = 'example'
# you may need to replace this cookie by following the instructions above!
cookie = 'general_session=1697F97A212A11EBAB156F0BEF0D0942; cookies_settings=%7B%22usage%22%3A%22true%22%2C%22essential%22%3A%22true%22%2C%22version%22%3A2%2C%22origin_tracking%22%3A%22true%22%7D; _ga=GA1.3.1467946823.1604777586; _gid=GA1.3.1231016164.1604777586; _gat_gtag_UA_3320079_1=1'
scrape_vacancies(scrape_id, cookie)

