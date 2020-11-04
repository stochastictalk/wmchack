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