# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 21:49:21 2016

@author: ssteffen
"""
import os
import requests
from bs4 import BeautifulSoup
import re
import datetime
import time
import numpy as np
import pandas as pd
import csv

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        print("Created Path.")
        os.makedirs(d)
   
def get_html(url, isMain = False):
    retries = 3
    for i in range(retries):
        try:
            r = requests.get(url)
            html = r.text
            return BeautifulSoup(html, 'html.parser')
        except requests.exceptions.Timeout:
        # Set up for a retry
            if i + 1 == retries:   
                print("Timeout Error.")
                errorDict[id] = (url, "TimeOut")
            else:
                time.sleep(2)
                return None
        except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
            print("TooManyRedirects Error.")
            errorDict[id] = (url, "TooManyRedirects")
            return None
        except requests.exceptions.RequestException as e:
        # Catastrophic error. bail.
            print("Catastropic Error.")
            errorDict[id] = (url, "Catastrophic Error")
            return None

def getNumUrls():
    soup = get_html('https://www.claimus.org/cases?page=1&pp=100')
    # Use regex to get the last page number.
    urls = soup.find_all("a", href=re.compile(r'.*/cases\?page=\d+.*'))
    # The second to last entry is always the correct one.
    return int(urls[-2].get_text())
       
def scrape_main(id, url):
    print('{0}: {1}'.format(id, url))
    if get_html(url, True) == None:
        pass
        print('Could not retrieve url: {0}'.format(url))       
        # Skip
    else:     
        # Scrape
        soup = get_html(url, True) 
        table = soup.find('table', {'class' : 'pagination'}) 
        rows = table.find_all('tr')[1:]
        data = []
        # Skip the header row
        for i in range(len(rows)):
            infoDict = dict() 
            infoDict['id'] = str(id)
            infoDict['url'] = url
            tds = rows[i].find_all('td')
            infoDict['uc_case'] = tds[0].text
            # Leaving in the following dublicates to get as much as data as possible
            infoDict['mec_num'] = tds[1].text
            infoDict['first_name'] = tds[2].text
            infoDict['last_name'] = tds[3].text
            infoDict['date_found'] = tds[4].text
            
            infoDict['county'] = tds[5].text
            infoDict['state'] = tds[6].text
            infoDict['case_url'] = tds[7].find('a')['href']
            
            infoDict_sub = scrape_sub(infoDict['case_url'])
            for k in infoDict_sub.keys():
                infoDict[k] = infoDict_sub[k]
            data.append(infoDict)
        return data   

def scrape_sub(case_url):
    # case_url = '/cases/5'
    url = 'https://www.claimus.org{0}'.format(case_url)    
    if get_html(url, False) == None:
        pass
        print('Could not retrieve url: {0}'.format(url))       
        # Skip
    else:     
        # Scrape
        soup = get_html(url, False) 
        tables = soup.find_all('table')
        infoDict = dict() 
        tds1 = tables[1].find_all('td', {'class' : 'view_field'})
        tds2 = tables[2].find_all('td', {'class' : 'view_field'})
        infoDict['next_of_kin_status'] = tds1[0].text
        infoDict['first_name'] = tds1[1].text
        infoDict['middle_name'] = tds1[2].text
        infoDict['last_name'] = tds1[3].text
        infoDict['nickname'] = tds1[4].text
        infoDict['year_of_birth'] = tds1[5].text
        infoDict['mec_num'] = tds1[6].text
        infoDict['agency_managing_case'] = tds1[7].text

        infoDict['date_found'] = tds2[0].text
        infoDict['max_age'] = tds2[1].text
        infoDict['race'] = tds2[2].text
        infoDict['ethnicity'] = tds2[3].text
        infoDict['sex'] = tds2[4].text
        return infoDict
#### Setup
main = 'C:/Projects/claimus/claimus'
os.chdir(main)  
today = datetime.date.today()
# today = datetime.date(2016, 9, 17)
errorDict = {}
test = False

print('Reading in urls.')
# Load urls from file
if test:
    urls = np.array(['https://www.claimus.org/cases?page=1&pp=20',
                'https://www.claimus.org/cases?page=2&pp=20'])
    dir = '{0}/data/{1}_{2}_{3}_Test'.format(main, today.year, today.month, today.day)
else:
    numUrls = getNumUrls()
    urls_list = ['https://www.claimus.org/cases?page={0}&pp=100'.format(i) for i in range(1, numUrls+1)]
    urls = np.array(urls_list)
    dir = '{0}/data/{1}_{2}_{3}'.format(main, today.year, today.month, today.day) 
    #start = 0
    #urls = urls.loc[start:]
dataPath = '{0}/data.csv'.format(dir)
errorPath = '{0}/errors.csv'.format(dir)

# Save
print('Saving to directory: {0}.'.format(dir))
ensure_dir(dataPath)
ensure_dir(errorPath)
# Get the keys
info = scrape_main(0, urls[0])
keys = info[0].keys()
# Scrape
with open(dataPath, 'w') as f:
    w = csv.DictWriter(f, fieldnames = keys, lineterminator = '\n')
    w.writeheader()
    for id in range(urls.shape[0]):
        #id = id + start
        print('Scraping id: {0}.'.format(str(id)))
        #Pause every 5 pages for 2 seconds
        if id % 5 == 0: time.sleep(2)
        info = scrape_main(id, urls[id])        
        w.writerows(info)

# Log errors
with open(errorPath, 'w') as f:  # Just use 'w' mode in 3.x
    w = csv.DictWriter(f, errorDict.keys())
    w.writeheader()
    w.writerow(errorDict)