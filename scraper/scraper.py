from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import requests
from itertools import chain

from bs4 import BeautifulSoup
import pandas as pd
import time
import numpy as np

'''
Selenium web scaper for sports reference 

set up:
import scraper in jupyter note book 
------------------------------------------------
from scraper import Sports_Ref_Scaper

url = "https://www.pro-football-reference.com"
options = Options()
options.headless = True
b = webdriver.Chrome(options=options)

scaper = Sports_Ref_Scraper(b, url)
------------------------------------------------


'''

class football_scraper:
    def __init__(self, driver, home_url):
        self.driver = driver
        self.home_url = home_url
        self.get_links()
        
    def get_links(self):
        url = self.home_url + '/years/'
        self.driver.get(url)
        page = BeautifulSoup(self.driver.page_source, features="lxml")
        table = page.find(id = "div_years")
        rows = []
        table.find_all("th")
        for th in table.find_all("th"):
            for data in th.find_all("a", href = True):
                row = [data.get_text(), data['href']]
                rows.append(row)

        links = pd.DataFrame(rows, columns=['year', 'link'])
        self.links = links
    
    def get_passing_data(self, link):
        url = self.home_url + link + 'passing.htm'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        tables = soup.find_all("table")

        table = tables[0]
        tab_data = [[cell.text for cell in row.find_all(["th","td"])]
                                for row in table.find_all("tr")]
        df = pd.DataFrame(tab_data)
        df.columns = df.iloc[0,:]
        df.drop(index=0,inplace=True)
        df['year'] = link

        return df
    
    def giant_concat(self, collection):
        list_of_dicts = [cur_df.T.to_dict().values() for cur_df in collection]    
        giant_concat_df = pd.DataFrame(list(chain(*list_of_dicts)))
        giant_concat_df = giant_concat_df.replace(r'^\s*$', np.NaN, regex=True)
        return giant_concat_df
    
    def get_individual_passing(self, num_years, label):
        
        collection = []
        for i in range(1, num_years):
            link = self.links.loc[i]['link']
            df = self.get_passing_data(link)
            collection.append(df)
        
        combined = self.giant_concat(collection)
        combined.to_csv(label + '.csv')
    
    def get_team_stats_helper(self, link, idd):
        url = self.home_url + link
        self.driver.get(url)
        time.sleep(3)
        page = BeautifulSoup(self.driver.page_source, features="lxml")
        table = page.find(id = idd)
        tab_data = [[cell.text for cell in row.find_all(["th","td"])]
                                    for row in table.find_all("tr")]

        df = pd.DataFrame(tab_data)
        df.columns = df.iloc[0,:]
        df.drop(index=0,inplace=True)
        df['year'] = link

        return df.reset_index(drop=True)
    
    def get_team_stats(self, num_years, label, idd):
        '''
        idds:
            - "passing": passing stats 
            - "team_stats": summary of team offense (not recommended at the moment)
        '''
        collection = []
        for i in range(1, num_years):
            print("iteration: ", i)
            link = self.links.loc[i]['link']
            df = self.get_team_stats_helper(link, idd)
            collection.append(df)
            
        combined = self.giant_concat(collection)
        combined.to_csv(label + '.csv')
        
    def get_data_tables(self, category, num_years):
        
        collection = []
        for i in range(1, num_years+1):
            page = self.home_url + self.links.loc[i]['link'] + '{}.htm'.format(category)
            print(page)
            r = requests.get(page)
            soup = BeautifulSoup(r.content, 'html.parser')
            table = soup.find_all('table')[0]  

            tab_data = [[cell.text for cell in row.find_all(["th","td"])]
                                        for row in table.find_all("tr")]
            df = pd.DataFrame(tab_data)
            df.columns = df.iloc[0,:]
            df.drop(index=0,inplace=True)
            df['year'] = self.links.loc[i]['link'].split("/")[2]
            df.query("Rk != {}".format("Rk"))

            collection.append(df)


        
        tables = pd.concat(collection)
        
        return tables
    
    
    
    def get_advanced_data_tables_passing(self, category, num_years, tbl_id):
        
        collection = []
        for i in range(1, num_years+1):
            page = self.home_url + self.links.loc[i]['link'] + 'passing_advanced.htm'
            print(page)
            r = requests.get(page)
            soup = BeautifulSoup(r.content, 'html.parser')
            table = soup.find(id = tbl_id)
            tab_data = [[cell.text for cell in row.find_all(["th","td"])]
                                                for row in table.find_all("tr")][1:]

            df = pd.DataFrame(tab_data)
            df.columns = df.iloc[0,:]
            df.drop(index=0,inplace=True)
            df['year'] = self.links.loc[i]['link'].split("/")[2]
            df.query("Rk != {}".format("Rk"))

            collection.append(df)


        
        tables = pd.concat(collection)
        
        return tables