#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 11:09:09 2019

@author: erik
"""

# =============================================================================
# This script serves to extract data from the Unternehmensregister
# to then put in in a tabular format and extract all relevant result pages
# and saving them with an ID as filename
# 
# =============================================================================
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import os
import re
import time
from datetime import datetime, timedelta, date

if not os.path.exists("Sites/"):
	os.makedirs("Sites/")


def search_stimmrechtsmitteilungen(start_date=None, end_date=None, results_per_page=4):
    """
    Performs a search for given parameters to initiate a session
    in Unternehmensregister.
    Returns a driver and full result URL with sessionID
    """
    # Set parameters for search
    publication_category = "Stimm­rechts­mitteilungen"
    publication_type = "Mitteilung bedeutender Stimm­rechts­anteile"
    language = "Deutsch"
    if start_date == None:
        start_date = "01.01.2007"
    if end_date == None:
        end_date = date.today().strftime("%d.%m.%Y")
    
    """
    @var: results_per_page
        0 ==> 10
        1 ==> 20
        2 ==> 30
        3 ==> 50
        4 ==> 100
    """
    results_per_page = results_per_page
    
    # Start search with given parameters
    chromedriver_path = os.path.join(os.getcwd(),"chromedriver")
    driver = webdriver.Chrome(chromedriver_path)
    driver.get("https://unternehmensregister.de")
    main_menu_toggle = driver.find_element_by_class_name("menu__toggle")
    main_menu_toggle.click()
    search_menu_toggle = driver.find_element_by_class_name("menu_headline")
    search_menu_toggle.click()
    capital_market_search_button = driver.find_element_by_partial_link_text("Kapitalmarkt")
    capital_market_search_button.click()
    
    publication_category_input = Select(driver.find_element_by_id("searchRegisterForm:publicationsOfCapitalInvestmentsCategory"))
    publication_category_input.select_by_visible_text(publication_category)
    
    publication_type_input = Select(driver.find_element_by_id("searchRegisterForm:publicationsOfCapitalInvestmentsPublicationType"))
    publication_type_input.select_by_visible_text(publication_type)
    
    language_input = Select(driver.find_element_by_id("searchRegisterForm:publicationsOfCapitalInvestmentsLanguage"))
    language_input.select_by_visible_text(language)
    
    start_date_input = driver.find_element_by_id("searchRegisterForm:publicationsOfCapitalInvestmentsPublicationsStartDate")
    end_date_input = driver.find_element_by_id("searchRegisterForm:publicationsOfCapitalInvestmentsPublicationsEndDate")
    start_date_input.clear()
    end_date_input.clear()
    start_date_input.send_keys(start_date)
    end_date_input.send_keys(end_date)
    
    driver.find_element_by_name("searchRegisterForm:j_idt267").click()
    
    # adjust results per page
    results_per_page_input = Select(driver.find_element_by_id("hppForm:hitsperpage"))
    results_per_page_input.select_by_index(results_per_page)
    result_url = driver.current_url
    
    return driver, result_url

class Search_Result_Handler(object):
    def __init__(self):
        self.start_index = None        
        
    def generate_search_result_csv(self, start_date=None, end_date=None, filename_prefix=None):
        """
        Perform a search for given parameters and save it as a csv-file with name
        'SearchResult.csv'. Filename prefix can be passed.
        """
        # prepare lists for DataFrame
        self.all_results_data_dict =   {'CompanyName':[],
                                        'InformationType':[],
                                        'AdditionalInformationType':[],
                                        'href':[], 
                                        'DocumentID':[],
                                        'ReasonForInformation':[],
                                        'DateOfCorrection':[],
                                        'DateOfInformation':[]
                                        }
        # Needed: Routine to check, wether result page is open or not
        # if not, perform search
        self.driver, self.result_url = search_stimmrechtsmitteilungen(start_date, end_date)   
        # Existance of next page, as long as the next button has an href
        next_page_href = ""
        page_counter = 1
        result_counter = 1
        
        start_time = time.time()
        
        while next_page_href is not None:
            result_page_soup = BeautifulSoup(self.driver.page_source,"html.parser")
            next_button = result_page_soup.find("div", attrs={"class":"next"})
            try: 
                next_button.find("a")["href"]
                next_page_href = next_button.find("a")["href"]
            except KeyError:
                next_page_href = None
            
            # first step identify results in result container
            result_container = result_page_soup.find("div", attrs={"class":"container result_container global-search"})
            page_results_set = result_container.findAll("div", attrs={'class': ['row'], 'id':re.compile('pubwithoutcaf264er_*')})
            
            # now maintain info from each result and put it in a of a DataFrame Object
            for single_result in page_results_set:
                print("Page: {}, Result: {}".format(page_counter,result_counter))
                result_counter += 1
                # this is where the magic happens, take the result row and investigate
                # it and try to populate the lists with it
                # at first check, if standard format result
                if len(single_result.findAll("div", attrs={"class":"col-md-4"})) == 3:
                    # Three columns
                    # 1. Company result
                    # 2. Information result
                    # 3. Label result
                    # first get company result
                    self.all_results_data_dict["CompanyName"].append(single_result.find("div", attrs={"class":"company_result"}).find("span").string)
                    # now get information result, that is divided into several fields
                    self.all_results_data_dict["InformationType"].append(single_result.find("div", attrs={"class":"information_result"}).p.string)
                    temp_sibling = ""
                    for child in single_result.find("div", attrs={"class":"information_result"}).children:
                        if child == "\n":
                            pass
                        else:
                            temp_sibling += child.string + "\n"
                    temp_sibling = " ".join(re.split("\s+", temp_sibling, flags=re.UNICODE))
                    self.all_results_data_dict["AdditionalInformationType"].append(temp_sibling)
                    # now get the information containing the href
                    # as well as information regarding date, correction, or corrected by
                    label_result_box = single_result.find("div", attrs={"class":"label_result"})
                    self.all_results_data_dict["href"].append(label_result_box.find("a")["href"])
                    id_start_position = label_result_box.find("a")["href"].find("t&id=") + 5
                    self.all_results_data_dict["DocumentID"].append(label_result_box.find("a")["href"][id_start_position:])
                    self.all_results_data_dict["ReasonForInformation"].append(label_result_box.find("a")["title"])
                    # set correction Date to None, in case there is no correction
                    date_of_correction = None
                    # Now find Date, and possibly correction Date
                    for pos, label_result_box_content in enumerate(label_result_box.find_all("div")):
                        if label_result_box_content.string and label_result_box_content.string.find("Datum") > 0:
                            date_postion_start = label_result_box_content.string.find("Datum") + 7
                            date_position_end = label_result_box_content.string.find("Datum") + 17
                            self.all_results_data_dict["DateOfInformation"].append(label_result_box_content.string[date_postion_start:date_position_end])
                        elif label_result_box_content.string == None and label_result_box_content.find("b") != None:
                            date_of_correction= " ".join(re.split("\s+", label_result_box_content.find("b").text, flags=re.UNICODE))
                            
                    self.all_results_data_dict["DateOfCorrection"].append(date_of_correction)
                                            
            # move on to next page, as soon as results from one page are done
            if next_page_href:
                self.driver.get(self.result_url + next_page_href)
                page_counter += 1
        
        result_data_frame = pd.DataFrame(self.all_results_data_dict)
        if filename_prefix != None:
            result_data_frame.to_csv(filename_prefix+"_SearchResult.csv", sep=";")
        else:
            result_data_frame.to_csv("SearchResult.csv", sep=";")
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        estimated_time = elapsed_time / result_data_frame.index.stop * 31200
        elapsed_time = str(timedelta(seconds=elapsed_time))
        estimated_time = str(timedelta(seconds=estimated_time))
        print("Elapsed time for {} results:\t{}\nEstimated time for search:\t{}".format(result_data_frame.index.stop,elapsed_time,estimated_time))
        self.driver.quit()
        
        # Handle MaxRetryError
        # Handle TimeoutException
    def scrape_documents(self, path_to_result_csv):
        start_time = time.time()
        self.search_result_df = pd.read_csv(path_to_result_csv, delimiter=";", index_col=0)
        self.savepath = os.path.join(os.getcwd(), "Sites")
        self.move_to_page_url = "?submitaction=pathnav&page."
        if self.start_index != None:
            self.search_result_df = self.search_result_df.tail(self.start_index)
        self.driver, self.result_url = search_stimmrechtsmitteilungen()
        # list to append all exceptional documents
        not_successful_documents = []
        # Crawl Content of result page and save it to a text file with
        for row in self.search_result_df.itertuples():
            self.start_index = row.Index
            try:
                document_savepath = os.path.join(self.savepath,"{}.html".format(row.DocumentID))
                if os.path.exists(document_savepath):
                    pass
                else:
                    self.driver.get(self.result_url + row.href)
                    soup = BeautifulSoup(self.driver.page_source,"html.parser")
                    if soup.find("div", attrs={"class":"container result_container global-search detail-view"}) == None:
                        self.driver.get(self.result_url + self.move_to_page_url + "{}".format(row.Index // 100 + 1))
                        self.driver.get(self.result_url + row.href)
                        soup = BeautifulSoup(self.driver.page_source,"html.parser")
                    if soup.find("div", attrs={"class":"container result_container global-search detail-view"}) != None:
                        with open(document_savepath, "w") as file:
                            page_string = soup.find("div", attrs={"class":"container result_container global-search detail-view"}).prettify()\
                                          + soup.find("div", attrs={"class":"publication_container"}).prettify()
                            file.write(page_string)
                    else:
                        print("OOOPS... Something went wrong!\tDocumentID: {}".format(row.DocumentID))
                        not_successful_documents.append(row.DocumentID)
#                        raise NotImplementedError 
            except Exception as e:
                print(e)
                print("Index: \t{}".format(self.start_index))
                break
        end_time = time.time()
        elapsed_time = end_time - start_time
        elapsed_time = str(timedelta(seconds=elapsed_time))
        print("Elapsed time for {} results:\t{}".format(self.start_index, elapsed_time))
        # Save IDs of documents that couldn't be found for some reason
        if len(not_successful_documents) > 0:
            failed_savepath = os.path.join(os.getcwd(), datetime.now().strftime("Failed_%Y_%m_%d_%H_%M.csv"))
            series = pd.Series(not_successful_documents)
            series.to_csv(failed_savepath, sep=";", header=None)
        # close driver
        self.driver.quit()
        
def main():
    my_scraper = Search_Result_Handler()
    my_scraper.scrape_documents("FullSearchResult.csv")
    return my_scraper

if __name__ == "__main__":
    session_scraper = main()   
            
