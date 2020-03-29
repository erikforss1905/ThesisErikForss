#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 17:35:18 2019

@author: erik
"""

import pandas as pd
from bs4 import BeautifulSoup
import os
import time
from statistics import mean
import re
from datetime import datetime, timedelta, date
from selenium import webdriver
import shutil

def convert_datestring(date_string):
    date_list = re.split("[.-]", date_string)
    try:
        if date_string == "skip" or date_string == "interrupt":
            return None
        assert len(date_list) == 3, "Datestring does not have correct format"
        if len(date_list[0]) == 4:
            year = int(date_list[0])
            day = int(date_list[2])
        elif len(date_list[2]) == 4:
            year = int(date_list[2])
            day = int(date_list[0])
        elif len(date_list[2]) == 2 and re.search(r"[01][\d]", date_list[2]):
            year = int("20{}".format(date_list[2]))
            day = int(date_list[0])
        else:
            raise NotImplementedError("Wrong date format: \t{}".format(date_string))
        month = int(date_list[1])
        event_date = "{}-{}-{}".format(year, month, day)
        return event_date
    except Exception as e:
        print("\tDate conversion failed. Exception: {}".format(e))
        return None

def screen_regex_result(list_of_strings, regex_pattern):
    """
    takes a list containing strings : 
    ['string1', 
     'string2',
     'string3'
    ]
    a pattern to screen for in that list
    returns a list only containing the relevant information
    """
    # perform search
    search_result = []
    if list_of_strings == None:
        search_result = None
    elif len(list_of_strings) > 0:
        if type(regex_pattern) == dict:
            for key in regex_pattern:
                for result_string in list_of_strings:
                    if regex_pattern[key].findall(result_string):
                        search_result.extend([key])
        else:
            for result_string in list_of_strings:
                search_result.extend(re.findall(regex_pattern, result_string))
    else:
        search_result = None
    # transform results into a list
    if search_result == None:
        result_list = None
    elif len(search_result) == 1:
        result_list = search_result
    elif len(search_result) > 1:
        result_list = []
        for result in search_result:
            if not(result in result_list):
                result_list.append(result)
    else:
        result_list = None

    return result_list

def regex_tuple_to_list(list_of_tuples, relevant_position_in_tupel):
    result_list = []
    if len(list_of_tuples) == 1:
        result_list.append(list_of_tuples[0][relevant_position_in_tupel])
    elif len(list_of_tuples) > 1:
        for result_tuple in list_of_tuples:
            result_list.append(result_tuple[relevant_position_in_tupel])
    else:
        return None

    return result_list

def list_to_string(list_of_strings):
    """
    takes a string or a list, returns a single string.
    if string, returns string, if number returns number
    """
    if type(list_of_strings) == str:
        if re.match(r"^[\d]+$",list_of_strings):
            list_of_strings = int(list_of_strings)
        elif re.match(r"^[\d,.]+$",list_of_strings):
            list_of_strings = float(list_of_strings.replace(",","."))
        return list_of_strings
    elif type(list_of_strings) == list:
        result_string = ""
        for string_element in list_of_strings:
            if re.match(r"^[\d]+$",string_element):
                list_of_strings = int(string_element)
            elif re.match(r"^[\d,.]+$",string_element):
                string_element = float(string_element.replace(",","."))
            result_string = "{}\n{}".format(result_string, string_element)
        return result_string.strip()
    else:
        return None

def raise_not_implemented(reason="NOT DEFINED"):
    # not implemented Error
    print("{} failed.".format(reason))
    while True:
        action = input("Interrupt Classification?:")
        if action in ["yes","y", "no","n"]:
            break
        else:
            print("Bad input. Use (yes/no)")
            continue
    if action in ["yes", "y"]:
        raise NotImplementedError("Aborting because {} failed...".format(reason))
    else:
        return None

class Classification_Handler(object):
    def __init__(self, backlog_filepaths_folders=None):
        """
        Constructs a Classification_Handler object.
        Inputs:
            backlog_filepaths_folders (defaults=None)
              ==> A list of folders in the current working directory to search for html documents
        """
        self.cwd = os.getcwd()
        if not(backlog_filepaths_folders):
            backlog_filepaths_folders = ["Sites",
                                        "Handler_Classification_Failed",
                                        "Handler_RegexPreClassified",
                                        "Handler_Relevant"
                                        ]
        self.backlog_html_filepaths_list = []
        for folder in backlog_filepaths_folders:
            folder_filepath = os.path.join(self.cwd, folder)
            self.backlog_html_filepaths_list.append(folder_filepath)
            if not os.path.exists(folder_filepath):
                os.makedirs(self.backlog_html_filepaths_list)
        self.relevant_html_filepath = os.path.join(self.cwd, "Handler_Relevant")
        if not os.path.exists(self.relevant_html_filepath):
            os.makedirs(self.relevant_html_filepath)
        self.regex_preclassified_html_filepath = os.path.join(self.cwd, "Handler_RegexPreClassified")
        if not os.path.exists(self.regex_preclassified_html_filepath):
            os.makedirs(self.regex_preclassified_html_filepath)
        self.irrelevant_html_filepath = os.path.join(self.cwd, "Handler_Irrelevant")
        if not os.path.exists(self.irrelevant_html_filepath):
            os.makedirs(self.irrelevant_html_filepath)
        self.failed_html_filepath = os.path.join(self.cwd, "Handler_Classification_Failed")
        if not os.path.exists(self.failed_html_filepath):
            os.makedirs(self.failed_html_filepath)
        self.manually_classified_filepath = os.path.join(self.cwd, "Handler_Manually")
        if not os.path.exists(self.manually_classified_filepath):
            os.makedirs(self.manually_classified_filepath)
        self.second_level_regex_html_filepath = os.path.join(self.cwd, "Handler_RegexSecondLevel")
        if not os.path.exists(self.second_level_regex_html_filepath):
            os.makedirs(self.second_level_regex_html_filepath)
        self.classification_run_counter = 0
        self.month_string_mapping = {"Januar":1,
                                     "Februar":2,
                                     "März":3,
                                     "April":4,
                                     "Mai":5,
                                     "Juni":6,
                                     "Juli":7,
                                     "August":8,
                                     "September":9,
                                     "Oktober":10,
                                     "November":11,
                                     "Dezember":12}
        self.df_headers = ["CompanyName", 
                           "AdditionalInformationType",
                           "DocumentID",
                           "ReasonForInformation",
                           "DateOfCorrection",
                           "DateOfInformation",
                           "Classified",
                           "ClassificationTime",
                           "FileDirectory",
                           "NewVotingRights",
                           "OldVotingRights",
                           "DeltaVotingRights",
                           "NewInstrumentVotingRights",
                           "OldInstrumentVotingRights",
                           "NewTotalVotingRights",
                           "OldTotalVotingRights",
                           "DeltaTotalVotingRights",
                           "NewNumberOfVotingRights",
                           "EventDate",
                           "Comment",
                           "MaxBordersCrossed",
                           "MinBordersCrossed",
                           "Blockholders",
                           "IrrelevantBlockholders"
                          ]
        self.df_headers_dtypes = {"Classified":object,
                                  "ClassificationTime":object,
                                  "FileDirectory":str,
                                  "EventDate":object,
                                  "Comment":object,
                                  "NewVotingRights":object,
                                  "MaxBordersCrossed":object,
                                  "MinBordersCrossed":object,
                                  "Blockholders":object,
                                  "IrrelevantBlockholders":object
                                  }
        self.financial_advisor_regex_pattern = {
            "Bank of America":re.compile(r"Bank of America Corporation", re.IGNORECASE),
            "Barclays":re.compile(r"Barclays", re.IGNORECASE),
            "Black ?Rock":re.compile(r"Black ?Rock", re.IGNORECASE),
            "Bank of Montreal":re.compile(r"Bank of Montreal", re.IGNORECASE),
            "Citigroup":re.compile(r"Citigroup", re.IGNORECASE),
            "Commerzbank":re.compile(r"Commerzbank", re.IGNORECASE),
            "Credit Suisse":re.compile(r"Credit Suisse", re.IGNORECASE),
            "DekaBank":re.compile(r"DekaBank", re.IGNORECASE),
            "Deutsche Bank":re.compile(r"Deutsche Bank", re.IGNORECASE),
            "Goldman Sachs":re.compile(r"Goldman Sachs", re.IGNORECASE),
            "HSBC":re.compile(r"HSBC", re.IGNORECASE),
            "JP Morgan Chase":re.compile(r"J.?P.? ?Morgan (Chase)?", re.IGNORECASE),
            "Merrill Lynch":re.compile(r"Merrill Lynch", re.IGNORECASE),
            "Morgan Stanley":re.compile(r"Morgan Stanley", re.IGNORECASE),
            "Royal Bank of Scotland":re.compile(r"Royal Bank of Scotland", re.IGNORECASE),
            "UniCredit":re.compile(r"UniCredit", re.IGNORECASE),
            "UBS":re.compile(r"UBS (Group )?AG", re.IGNORECASE),
            "Lehman Brothers":re.compile(r"Lehman Brothers", re.IGNORECASE),
            }
    
    def create_backlog_from_scraping_result(self, path_to_scraper_result_csv, path_to_backlog_csv=None):
        """
        Implement a routine that takes a raw scraping results and adds relevant columns
        """
        # Pop unimportant columns
        colums_to_use = ["CompanyName", 
                         "AdditionalInformationType",
                         "DocumentID",
                         "ReasonForInformation",
                         "DateOfCorrection",
                         "DateOfInformation"
                         ]
        scraper_result_df = pd.read_csv(path_to_scraper_result_csv, sep=";", usecols=colums_to_use, dtype=object)
        # Add Columns:
        new_df_headers = self.df_headers
        new_df_columns_dtype = self.df_headers_dtypes
        scraper_result_df = scraper_result_df.reindex(columns=new_df_headers)
        scraper_result_df = scraper_result_df.astype(dtype=new_df_columns_dtype)
        backlog_filename_suffix = datetime.now().strftime("%Y_%m_%d_%H_%M")
        if not(path_to_backlog_csv):
            path_to_backlog_csv = os.path.join(self.cwd, "Temp/HandlerWorkingBacklog_{}.csv".format(backlog_filename_suffix))
        scraper_result_df.to_csv(path_to_backlog_csv, sep=";")
        return path_to_backlog_csv
    
    def create_event_list(self, path_to_classified_csv, path_to_event_list_backlog_csv=None):
        # Pop unimportant columns
        colums_to_use = ["CompanyName",
                          "DocumentID",
                          "ReasonForInformation",
                          "DateOfCorrection",
                          "DateOfInformation",
                          "Classified",
                          "ClassificationTime",
                          "FileDirectory",
                          "NewVotingRights",
                          "OldVotingRights",
                          "DeltaVotingRights",
                          "NewInstrumentVotingRights",
                          "OldInstrumentVotingRights",
                          "NewTotalVotingRights",
                          "OldTotalVotingRights",
                          "DeltaTotalVotingRights",
                          "NewNumberOfVotingRights"
                         ]
        event_list_df = pd.read_csv(path_to_classified_csv, sep=";", usecols=colums_to_use, dtype=object)
        # Add Columns:
        new_df_headers = self.df_headers
        new_df_columns_dtype = self.df_headers_dtypes
        event_list_df = event_list_df.reindex(columns=new_df_headers)
        event_list_df = event_list_df.astype(dtype=new_df_columns_dtype)
        backlog_filename_suffix = datetime.now().strftime("%Y_%m_%d_%H_%M")
        if not(path_to_event_list_backlog_csv):
            path_to_event_list_backlog_csv = os.path.join(self.cwd, "Temp/EventListWorkingBacklog_{}.csv".format(backlog_filename_suffix))
        event_list_df.to_csv(path_to_event_list_backlog_csv, sep=";")
        return path_to_event_list_backlog_csv

    def get_work_backlog(self, path_to_backlog_csv_file, scraping_results_path="FullSearchResult.csv"):
        """
        Reads the Result csv-File and creates working backlog for classification
        Filename for scraper result defaults to 'FullSearchResult.csv' in current wd
        """
        if not(path_to_backlog_csv_file) or not(os.path.isfile(path_to_backlog_csv_file)):
            scraping_result_path = os.path.join(self.cwd, scraping_results_path)
            path_to_backlog_csv_file = self.create_backlog_from_scraping_result(scraping_result_path, path_to_backlog_csv_file)
        self.backlog_csv_filepath = os.path.join(self.cwd, path_to_backlog_csv_file)
        loadpath = os.path.join(self.cwd, self.backlog_csv_filepath)
        work_backlog_df = pd.read_csv(loadpath, sep=";", index_col=0, dtype=object)
        # Sorting
        # list of lists with column name to sort by, and bool for ascending
        sorting_criteria = [["DateOfInformation", "Classified", "FileDirectory"],
                            [False,                True,        True]]
        work_backlog_df.sort_values(by=sorting_criteria[0], ascending=sorting_criteria[1], na_position="first")
        self.work_backlog = work_backlog_df
        return self.work_backlog

    def get_event_list_backlog(self, path_to_backlog_csv_file, classified_result_path="FullBacklog.csv"):
        if not(path_to_backlog_csv_file) or not(os.path.isfile(path_to_backlog_csv_file)):
            classified_result_path = os.path.join(self.cwd, classified_result_path)
            path_to_backlog_csv_file = self.create_event_list(classified_result_path, path_to_backlog_csv_file)
        self.backlog_csv_filepath = os.path.join(self.cwd, path_to_backlog_csv_file)
        loadpath = os.path.join(self.cwd, self.backlog_csv_filepath)
        work_backlog_df = pd.read_csv(loadpath, sep=";", index_col=0, dtype=object)
        # Sorting
        # list of lists with column name to sort by, and bool for ascending
        sorting_criteria = [["DateOfInformation", "Classified", "FileDirectory"],
                            [False,                True,        True]]
        work_backlog_df.sort_values(by=sorting_criteria[0], ascending=sorting_criteria[1], na_position="first")
        self.work_backlog = work_backlog_df
        return self.work_backlog
    
    def save_work_backlog(self):
        """
        Writes the current state of backlog to the csv-Backlog-File
        """
        self.work_backlog.to_csv(self.backlog_csv_filepath, sep=";")

    def is_document_available(self, document_tuple):
        """
        Checks, wether the document is available and 
        returns the working document filepath
        """
        self.current_working_document_filepath = None
        if document_tuple.FileDirectory:
            document_html_filepath = os.path.join(self.cwd, "{}/{}.html".format(document_tuple.FileDirectory, document_tuple.DocumentID))
            if os.path.exists(document_html_filepath):
                self.current_working_document_filepath = document_html_filepath
            else: 
                for check_path in self.backlog_html_filepaths_list:
                    document_html_filepath = os.path.join(check_path, "{}.html".format(document_tuple.DocumentID))
                    if os.path.exists(document_html_filepath):
                        self.current_working_document_filepath = document_html_filepath
                        break
        return self.current_working_document_filepath

    def has_tabular_format(self, document_soup):
        """
        The soup from from the working backlog and classifies, if the tuple has tabular format or not.
        Returns: 
            'True' if tabular,
            'False' if not tabular
        """
        if document_soup.find("p", string=re.compile(".*Gesamtstimmrechtsanteile.*")):
            return True
        else:
            return False

    def parse_tabular_row(self, row_elements_iterator, keywords_to_exclude_list=["Neu", "Letzte"]):
        document_information_list = []
        for pos, information_element in enumerate(row_elements_iterator):
            for keyword in keywords_to_exclude_list:
                excluded = re.search(keyword, information_element.string)
                if excluded:
                    break
            if excluded:
                pass
            elif pos in [1,2,3,6,7,8]:
                # voting rights in percent, sometimes digits sometimes commas
                cell_information = information_element.string.strip().replace(".",",").replace(" ","").replace("%","").replace(",",".")
                try:
                    if cell_information:
                        if cell_information.find(".") >= 0:
                            cell_information = float(cell_information)
                        else:
                            # throws ValueError if 'nan'
                            cell_information = int(cell_information)
                        # print("----------\n{}\n----------------------".format(cell_information))
                    else:
                        cell_information = None
                except ValueError:
                    # catch ValueError
                    # cell contains string, that means info n/a
                    cell_information = None
                    # check if cell containing some information or not
                    # if len(cell_information) == 0:
                    #     cell_information = None
                    # else:
                    #     # cell_information just remains the string
                    #     pass
                document_information_list.append(cell_information)
            elif pos in [4,9]:
                # total voting rights, sometimes digits sometimes commas
                cell_information = information_element.string.strip().replace(".","").replace(" ","").replace(",","")
                try:
                    if cell_information:
                        if cell_information.find(".") >= 0:
                            cell_information = float(cell_information)
                        else:
                            # throws ValueError if 'nan'
                            cell_information = int(cell_information)
                        # print("----------\n{}\n----------------------".format(cell_information))
                    else:
                        cell_information = None
                except ValueError:
                    # catch ValueError
                    # cell contains string, that means info n/a
                    cell_information = None
                    # check if cell containing some information or not
                    # if len(cell_information) == 0:
                    #     cell_information = None
                    # else:
                    #     # cell_information just remains the string
                    #     pass
                document_information_list.append(cell_information)
        return document_information_list

    def classify_tabular(self, soup):
        """
        Takes the soup of a tabular html document and parses for relevant information
        """
        document_information_dict = {"NewVotingRights":None,
                                     "NewInstrumentVotingRights":None,
                                     "NewTotalVotingRights":None,
                                     "OldVotingRights":None,
                                     "OldInstrumentVotingRights":None,
                                     "OldTotalVotingRights":None,
                                     "Blockholders":None,
                                     "IrrelevantBlockholders":None,
                                    }
        information_mapping_dict =  {0:"NewVotingRights",
                                     1:"NewInstrumentVotingRights",
                                     2:"NewTotalVotingRights",
                                     3:"NewNumberOfVotingRights",
                                     4:"OldVotingRights",
                                     5:"OldInstrumentVotingRights",
                                     6:"OldTotalVotingRights",
                                     7:"OldNumberOfVotingRights"
                                    }
        # document_information_list = []
        table_voting_rights = soup.find("p", string=re.compile(".*Gesamtstimmrechtsanteile.*")).find_next("table")
        # at first get the entries of new voting rights
        new_information_row_elements_iterator = table_voting_rights.find("tbody").find("tr").find_all("p")
        document_information_list = self.parse_tabular_row(new_information_row_elements_iterator)
        # now get the values for old voting rights
        old_information_row_elements_iterator = table_voting_rights.find("tbody").find("tr").find_next("tr").find_all("p")
        document_information_list.extend(self.parse_tabular_row(old_information_row_elements_iterator))
        # put the information into the dictionary
        for pos, cell_information in enumerate(document_information_list):
            document_information_dict[information_mapping_dict[pos]] = cell_information
        
        # parse blockholder
        page_string = " ".join(re.split(r" +", soup.get_text(), flags=re.UNICODE))
        page_string = re.sub(r"\n+", "\n", page_string)
        blockolder = re.findall(r"Angaben\s+zum\s+Mitteilungspflichtigen:\s+([\w ]*)\n",page_string)
        irrelevant_blockholders = screen_regex_result(blockolder, self.financial_advisor_regex_pattern)
        blockholder = list_to_string(blockolder)
        document_information_dict["Blockholders"] = blockholder
        document_information_dict["IrrelevantBlockholders"] = irrelevant_blockholders
        # Now decide if
        # relevant ==> new_voting_rights < 0.5 < 3 <= old_voting_rights
        # irrelevant ==> new_voting_rights >= old_voting_rights
        # not sure ==> probably any other case
        # TODO: Implement Handling for cases, where some cells are strings "nan" or "n/a" or similar
        try:
            # case 1: voting rights and total voting rigths available
            if (document_information_dict["OldVotingRights"] and document_information_dict["NewVotingRights"]) and (document_information_dict["NewTotalVotingRights"] and document_information_dict["OldTotalVotingRights"]):
                if (document_information_dict["NewVotingRights"] < 0.5 < 3 <= document_information_dict["OldVotingRights"] < 50) == (document_information_dict["NewTotalVotingRights"] < 0.5 < 3 <= document_information_dict["OldTotalVotingRights"] < 50):
                    relevant_bool = (document_information_dict["NewVotingRights"] < 0.5 < 3 <= document_information_dict["OldVotingRights"] < 50)
                else:
                    relevant_bool = None
                document_information_dict["DeltaVotingRights"]\
                    = document_information_dict["OldVotingRights"] - document_information_dict["NewVotingRights"]
                document_information_dict["DeltaTotalVotingRights"]\
                    = document_information_dict["OldTotalVotingRights"] - document_information_dict["NewTotalVotingRights"]
            # case 2: only voting rights available
            elif (document_information_dict["OldVotingRights"] and document_information_dict["NewVotingRights"]):
                relevant_bool = (document_information_dict["NewVotingRights"] < 0.5 < 3 <= document_information_dict["OldVotingRights"] < 50)
                document_information_dict["DeltaVotingRights"]\
                    = document_information_dict["OldVotingRights"] - document_information_dict["NewVotingRights"]
            # case 3: only total voting rights available
            elif (document_information_dict["NewTotalVotingRights"] and document_information_dict["OldTotalVotingRights"]):
                relevant_bool = document_information_dict["NewTotalVotingRights"] < 0.5 < 3 <= document_information_dict["OldTotalVotingRights"] < 50
                document_information_dict["DeltaTotalVotingRights"]\
                    = document_information_dict["OldTotalVotingRights"] - document_information_dict["NewTotalVotingRights"]
            # case 4: only New Voting Rights available
            elif not(document_information_dict["OldVotingRights"]) and document_information_dict["NewVotingRights"]:
                relevant_bool = document_information_dict["NewVotingRights"] < 0.5
            # case 5: only old voting rights available
            elif document_information_dict["OldVotingRights"] and not(document_information_dict["NewVotingRights"]):
                relevant_bool = document_information_dict["OldVotingRights"] < 50
            else:
                # TODO implement Handling for residual cases
                relevant_bool = None
        except TypeError:
            relevant_bool = None
            # TODO: Implement Handler, if e.g. old Voting rights are not found, but new voting rights > 0.5
            # or if e.g. Old Voting rights were a majority 
        if relevant_bool == True:
            result = "relevant"
            classified_by = "TabularClassifier"
            proposed_directory = self.relevant_html_filepath
        elif relevant_bool == False:
            result = "irrelevant"
            classified_by = "TabularClassifier"
            proposed_directory = self.irrelevant_html_filepath
        else:
            result = None
            classified_by = None
            proposed_directory = self.failed_html_filepath
            
        return result, classified_by, proposed_directory, document_information_dict

    def classify_non_tabular(self, soup):
        """
        Takes a non tabular document and tries to parse for relevant information
        """
        # get string
        # match some keywords
        page_string = " ".join(re.split(r"\s+", soup.get_text(), flags=re.UNICODE))
        match_relevant_keyword = re.search("Unterschreit", page_string, re.IGNORECASE) or\
                                    re.search("unterschritt", page_string, re.IGNORECASE) or\
                                    re.search("Schwellenunterschreitung", page_string, re.IGNORECASE)
        match_irrelevant_keyword = re.search("Überschreit", page_string, re.IGNORECASE) or\
                                    re.search("überschritt", page_string, re.IGNORECASE) or\
                                    re.search("Schwellenüberschreitung", page_string, re.IGNORECASE)
        # case 1: only "relevant" keywords found
        if match_relevant_keyword and not(match_irrelevant_keyword):
            result = "relevant"
            proposed_directory = self.regex_preclassified_html_filepath
            classified_by = "SimpleRegex"
            # perform advanced Regex-Search:
            result, classified_by, proposed_directory, document_information_dict = self.third_level_regex_search(soup)
        # case 2: only "irrelevant" keywords found
        elif not(match_relevant_keyword) and match_irrelevant_keyword:
            result = "irrelevant"
            proposed_directory = self.irrelevant_html_filepath
            classified_by = "SimpleRegex"
            document_information_dict = None
        # case 3: none of the above, Try third level Regex
        else:
            # result = None
            # proposed_directory = self.failed_html_filepath
            # classified_by = None
            # document_information_dict = None
            result, classified_by, proposed_directory, document_information_dict = self.third_level_regex_search(soup)

        return result, classified_by, proposed_directory, document_information_dict

    def second_level_regex_search(self, soup):
        r"""
        Define Regex-Strings for borders
            '\s?[%(Prozent)]'       --> suffix percent with optional space
            '[0]+[,.][0-4][\d]*'    --> 0.00 - 0.49
            '[0][0,.]+'             --> 0 or 00 or 0.00 or 0,00
            '[0]+[,.][5-9]\d'       --> 0.5 - 0.99    
            '[1-9]+[\d]?[,.]?[\d]'  --> 1.00 - 99.99
        """
        page_string = " ".join(re.split(r"\s+", soup.get_text(), flags=re.UNICODE))
        match_relevant_keyword = \
            re.search(r"die Schwelle von [\d]+[,.][\d]* der Stimmrechte unterschritten hat und an diesem Tag [0]+[,.][0-4][\d]*\s?[%(Prozent)]", page_string, re.IGNORECASE) or\
            re.search(r"Mitteilungspflichtiger Stimmrechtsanteil: [0]+[,.][0-4]+[\d]*\s?[%(Prozent)]", page_string, re.IGNORECASE) or\
            re.search(r"Mitteilungspflichtiger Stimmrechtsanteil: [0][0,.]+\s?[%(Prozent)]", page_string) or\
            re.search(r"diesem (Tag)?(Zeitpunkt)? [0]+[,.][0-4]+[\d]*\s?[%(Prozent)]", page_string) or\
            re.search(r"diesem (Tag)?(Zeitpunkt)? [0][0,.]+\s?[%(Prozent)]", page_string) or\
            re.search(r"und nun [0]+[,.][0-4]+[\d]*\s?[%(Prozent)]", page_string) or\
            re.search(r"und nun [0][0,.]+\s?[%(Prozent)]", page_string) or\
            re.search(r"nunmehr [0]+[,.][0-4]+[\d]*\s?[%(Prozent)]", page_string) or\
            re.search(r"nunmehr [0][0,.]+\s?[%(Prozent)]", page_string) or\
            re.search(r"einen Stimmrechtsanteil von [0]+[,.][0-4]+[\d]*\s?[%(Prozent)]", page_string) or\
            re.search(r"einen Stimmrechtsanteil von [0][0,.]+\s?[%(Prozent)]", page_string)
        match_irrelevant_keyword = \
            re.search(r"Mitteilungspflichtiger Stimmrechtsanteil: [1-9]+[\d]?[,.]?[\d]*\s?[%(Prozent)]", page_string, re.IGNORECASE) or\
            re.search(r"Mitteilungspflichtiger Stimmrechtsanteil: [0]+[,.]+[5-9]+\s?[%(Prozent)]", page_string) or\
            re.search(r"diesem (Tag)?(Zeitpunkt)? [0]+[,.][5-9]+[\d]*\s?[%(Prozent)]", page_string) or\
            re.search(r"diesem (Tag)?(Zeitpunkt)? [1-9]+[\d]?[,.]?[\d]*\s?[%(Prozent)]", page_string) or\
            re.search(r"und nun [0]+[,.]+[5-9]+\s?[%(Prozent)]", page_string) or\
            re.search(r"und nun [1-9]+[,.]?[\d]*\s?\s?[%(Prozent)]", page_string) or\
            re.search(r"nunmehr [0]+[,.]+[5-9]+\s?[%(Prozent)]", page_string) or\
            re.search(r"nunmehr [1-9]+[,.]?[\d]*\s?\s?[%(Prozent)]", page_string) or\
            re.search(r"einen Stimmrechtsanteil von [0]+[,.]+[5-9]+\s?[%(Prozent)]", page_string) or\
            re.search(r"einen Stimmrechtsanteil von [1-9]+[,.]?[\d]*\s?\s?[%(Prozent)]", page_string)
        # case 1: only "relevant" keywords found
        if match_relevant_keyword and not(match_irrelevant_keyword):
            result = "relevant"
            proposed_directory = self.second_level_regex_html_filepath
            classified_by = "SecondLevelRegex"
        elif match_irrelevant_keyword and not(match_relevant_keyword):
            result = "irrelevant"
            proposed_directory = self.irrelevant_html_filepath
            classified_by = "SecondLevelRegex"
        # case 2: No more keywords found, but still classified as relevant with SimpleRegex
        else:
            result = "relevant"
            proposed_directory = self.regex_preclassified_html_filepath
            classified_by = "SimpleRegex"

        return result, classified_by, proposed_directory

    def third_level_regex_search(self, soup, ignore_errors=False):
        ignore_errors = self.ignore_errors
        page_string = " ".join(re.split(r"\s+", soup.get_text(), flags=re.UNICODE))
        # at first set all used variables to None to not cause uncaught exceptions
        result = None
        majority_border_crossed = False
        min_border = None
        max_border = None
        # match = re.findall(r"", page_string, re.IGNORECASE)
        match_new_voting_rights = re.findall(r"(Mitteilungspflichtiger Stimmrechtsanteil: |einen Stimmrechtsanteil von |nunmehr |und nun |diesem (Tag)?(Zeitpunkt)?)\s?([0]+[,.]?[0-4][\d]+|[0,.]+) ?(%|Prozent)", page_string, re.IGNORECASE)
        irrelevant_new_voting_rights = re.findall(r"(Mitteilungspflichtiger Stimmrechtsanteil: |einen Stimmrechtsanteil von |nunmehr |und nun |diesem (Tag)?(Zeitpunkt)?)\s?([\d]+[,.]?[5-9][\d]+|[1-9][\d,]*) ?(%|Prozent)", page_string, re.IGNORECASE)
        match_blockholder = re.findall(r"(Mitteilungspflichtiger:\s?)(((())))((Frau Dr\.|Herr Dr\.)?[\w\s]*)([\w\s]*),", page_string, re.IGNORECASE) or\
            re.findall(r"((Für den Inhalt der Mitteilung ist der Emittent verantwortlich.\s)?(Die |Der (Stimmrechtsanteil (der )?)?|Das ))((?!Emittent|EQS Group AG)[\w\d\s.,\(\)]*?)( hat uns| hat am)", page_string, re.IGNORECASE)
            # re.findall(r"(Der (Stimmrechtsanteil (der )?)?|Die |Das )([\w\d\s.,\(\)]*?)( hat uns| hat am)", page_string, re.IGNORECASE)
        # reduce to only relevant information
        # actually, all list lengths should match, i could do this all together
        # borders crossed at group 2; check for majority
        match_borders = re.findall(r"(die Schwellen? von|Betroffene Meldeschwellen?:)\s{0,2}([\d,%\s]*(und\s(von\s)?)?([\d%\s]*))\s{0,2}([\w\s]{0,20}(unterschritten|unterschritt)?)", page_string, re.IGNORECASE)
        if match_borders:
            match_borders = regex_tuple_to_list(match_borders, 1)
            border_regex_pattern = re.compile(r"[\d]+", re.IGNORECASE)
            borders_crossed = screen_regex_result(match_borders, border_regex_pattern)
            all_borders = []
            if borders_crossed:
                for border in borders_crossed:
                    border = int(border)
                    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    # Decide wether to raise Exception or just pop the wrongly identified borders
                    # assert border in [0,3,5,10,15,20,25,30,35,40,45,50,75], "Something went wrong at parsing borders: {}".format(border)
                    if not (border in [0,3,5,10,15,20,25,30,35,40,45,50,75]):
                        continue
                    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    if border >= 50:
                        majority_border_crossed = True
                    if not(border in all_borders):
                        all_borders.append(border)
                if len(all_borders) > 0:
                    min_border = min(all_borders)
                    max_border = max(all_borders)
        else:
            if not(ignore_errors):
                raise_not_implemented("Finding Borders")
        # new voting rights at group 4
        match_new_voting_rights = regex_tuple_to_list(match_new_voting_rights, 3)
        # irrelevant voting rights at group 4
        irrelevant_new_voting_rights = regex_tuple_to_list(irrelevant_new_voting_rights, 3)
        # blockholder at group 6
        match_blockholder = regex_tuple_to_list(match_blockholder, 5)
        # TODO: implement routine for better blockholder screening
        if match_blockholder:
            for blockholder in match_blockholder:
                blockholder.replace("entspricht 0 Stimmrechten) betragen hat. ", "").replace("entspricht 216.122 Stimmrechten) betragen hat. ","")
        # financial advisors
        irrelevant_blockholders = screen_regex_result(match_blockholder, self.financial_advisor_regex_pattern)
        # relevant:
        #     - new voting rights < 0.5%
        #     - no irrelevant voting rights found
        #     - borders crossed < 50%
        #     - no financial advisors found
        # ++++++++++++++++++++++++++++++++++++++++++++
        # sooner or later implement standard filepaths
        success_filepath = self.success_filepath
        irrelevant_filepath = self.irrelevant_filepath
        double_check_filepath = self.double_check_filepath
        not_implemented_filepath = self.not_implemented_filepath
        # ++++++++++++++++++++++++++++++++++++++++++++
        if match_new_voting_rights and not(irrelevant_new_voting_rights) and not(majority_border_crossed) and not(irrelevant_blockholders):
            if not(ignore_errors):
                print("{}\nOnly sold! Very good!\nBlockholder:\n{}\n{}".format("+"*30, match_blockholder,"+"*30))
            result, classified_by, proposed_directory = "relevant","RegexThirdLevel", success_filepath
            # check for information is done lateron
        elif match_new_voting_rights and irrelevant_blockholders:
            if len(irrelevant_blockholders) == len(match_blockholder):
                if not(ignore_errors):
                    print("Seems like ONLY Financial Advisors were the blockholders! Very likely irrelevant")
                result, classified_by, proposed_directory = "irrelevant","RegexThirdLevel:FinancialAdvisorsOnly",irrelevant_filepath
            else:
                if not(ignore_errors):
                    print("Seems like a Financial Advisor was involved! Better check again!")
                result, classified_by, proposed_directory = "unsure","RegexThirdLevel:FinancialAdvisorInvolved",double_check_filepath
        elif match_new_voting_rights and irrelevant_new_voting_rights:
            if not(ignore_errors):
                print("Sold and bought! Maybe a takeover?")
            result, classified_by, proposed_directory = "unsure","RegexThirdLevel:Takeover?",double_check_filepath
        elif match_new_voting_rights and majority_border_crossed:
            if match_blockholder and match_borders:
                if len(match_blockholder)==len(match_borders):
                    if not(ignore_errors):
                        print("Majority border crossed! All Blockholders had majority")
                result, classified_by, proposed_directory = "irrelevant","RegexThirdLevel:MajorityBlockholder",irrelevant_filepath
            elif match_borders and not(match_blockholder):
                result, classified_by, proposed_directory = "unsure","RegexThirdLevel:MajorityInvolved",double_check_filepath
            else:
                result, classified_by, proposed_directory = "unsure","RegexThirdLevel:MajorityInvolved",double_check_filepath
        elif not(match_new_voting_rights) and irrelevant_new_voting_rights:
            if not(ignore_errors):
                print("Only irrelevant borders crossed. Irrelevant")
            result, classified_by, proposed_directory = "irrelevant","RegexThirdLevel:NotExit",irrelevant_filepath
        else:
            result, classified_by, proposed_directory = "not implemented","RegexThirdLevel:NotImplemented",not_implemented_filepath
            if not(ignore_errors):
                print("Not sure if I got every Case.") 
                # not implemented
                raise_not_implemented("Regex Classification")
            new_voting_rights = 9876543210
            max_border = 9876543210
            min_border = 9876543210

        if match_new_voting_rights and not(irrelevant_new_voting_rights):
            new_voting_rights = list_to_string(match_new_voting_rights)
        elif not(match_new_voting_rights) and irrelevant_new_voting_rights:
            new_voting_rights = list_to_string(irrelevant_new_voting_rights)
        elif match_new_voting_rights and irrelevant_new_voting_rights:
            new_voting_rights = list_to_string(match_new_voting_rights.extend(irrelevant_new_voting_rights))
        elif not(match_new_voting_rights) and not(irrelevant_new_voting_rights):
            new_voting_rights = None
        else:
            # not implemented
            new_voting_rights = 9876543210
            max_border = 9876543210
            min_border = 9876543210
            if not(ignore_errors):
                raise_not_implemented("Classification of Voting Rights")                
        
        if result in ["relevant","unsure", "not implemented"]:
            document_information_dict = {"NewVotingRights":new_voting_rights,
                                         "MaxBordersCrossed":max_border,
                                         "MinBordersCrossed":min_border,
                                         "Blockholders":list_to_string(match_blockholder),
                                         "IrrelevantBlockholders":list_to_string(irrelevant_blockholders)
                                         }
        else:
            document_information_dict = None
        if result == "relevant" and not(ignore_errors):
            for checker in ["Blockholders","MinBordersCrossed","MaxBordersCrossed","NewVotingRights"]:
                if document_information_dict[checker] == None:
                    print("Information missing:\t.\t.\t {}".format(checker))
                    raise_not_implemented("Gathering Information for relevant Event")
                    classified_by = "RegexThirdLevel:GatheringInfoFailed"     
        return result, classified_by, proposed_directory, document_information_dict 

    def update_backlog_tuple(self, classification_result, classified_by, proposed_directory, backlog_tuple, document_information_dict, move_docs=False):
        """
        Takes classification information an updates tuple of the work-backlog and moves file
        """
        # only move, if in moving mode and if document existant
        if proposed_directory !="NotFound":
            if not os.path.exists(proposed_directory):
                os.makedirs(proposed_directory)
            classified_savepath = os.path.join(proposed_directory, "{}.html".format(backlog_tuple.DocumentID))
            if classification_result != "irrelevant" and self.current_working_document_filepath != self.irrelevant_html_filepath:
                if classified_savepath != self.current_working_document_filepath:
                    self.classification_run_counter += 1
                if (move_docs=="copy" or move_docs=="c") and (classified_savepath != self.current_working_document_filepath) and (not os.path.isfile(classified_savepath)):
                    shutil.copy(self.current_working_document_filepath, proposed_directory)
                elif move_docs == True:
                    os.rename(self.current_working_document_filepath, classified_savepath)
        # anyways update backlog, also if file not existant
        self.work_backlog.at[backlog_tuple.Index, "Classified"] = classified_by
        self.work_backlog.at[backlog_tuple.Index, "FileDirectory"] = proposed_directory.replace(self.cwd, "")
        if document_information_dict:
            for key in document_information_dict.keys():
                self.work_backlog.at[backlog_tuple.Index, key] = document_information_dict[key]

    def move_docs(self, path_to_backlog_csv_file=None, debug_mode=False):
        self.time_measurement_list = []
        if not(path_to_backlog_csv_file):
            path_to_scraper_result_csv = os.path.join(os.getcwd(), "Temp/FullSearchResult.csv")
            self.get_work_backlog(None, path_to_scraper_result_csv)
        else:
            self.get_work_backlog(path_to_backlog_csv_file, "Temp/FullSearchResult.csv")
        if debug_mode:
            chromedriver_path = os.path.join(self.cwd,"chromedriver")
            driver = webdriver.Chrome(chromedriver_path)
        try:
            custom_iterator = self.create_backlog_iterator(None, None)
            for current_tuple in custom_iterator:
                doc_working_start_time = time.time()
                # load html Document as soup
                if self.is_document_available(current_tuple):
                    if debug_mode:
                        driver.get("file:///{}".format(self.current_working_document_filepath))
                    if current_tuple.FileDirectory != "NotFound":
                        proposed_directory = os.path.join(os.getcwd(),"{}/{}.html".format(current_tuple.FileDirectory, current_tuple.DocumentID))
                        os.rename(self.current_working_document_filepath, proposed_directory)
                self.measure_doc_working_time(doc_working_start_time, current_tuple.Index)
        except Exception as e:
            print("Something went wrong at DocumentID {}".format(current_tuple.DocumentID))
            print("Exception thrown: {}".format(e))
        except KeyboardInterrupt:
            print("Execution was interrupted!\nSaving Backlog...")
        if debug_mode:
            driver.quit()
        if len(self.time_measurement_list) > 0:
            average_classification_time = round(mean(self.time_measurement_list),3)
        else:
            average_classification_time = 0
        print("Classification run completed.\
               \nAverage classification time per document:\t{}\
               \nFor in total documents classified:\t.\t{}\
               \nEvent dates entered:\t.\t.\t.\t{}".format(average_classification_time,len(self.time_measurement_list)+1, self.classification_run_counter))
        self.classification_run_counter = 0

    def measure_doc_working_time(self, doc_working_start_time, tuple_index):
        doc_working_end_time = time.time()
        doc_working_time = doc_working_end_time - doc_working_start_time
        # put it in df
        self.work_backlog.at[tuple_index, "ClassificationTime"] = round(doc_working_time, 1)
        # put it in list
        self.time_measurement_list.append(doc_working_time)

    def create_backlog_iterator(self, filter_column, filter_criteria, empty_columns=None, automated_classification=False):
        if type(filter_column) == list and type(filter_criteria) == dict:
            filtered_backlog_df = self.work_backlog
            for column in filter_column:
                filtered_backlog_df = filtered_backlog_df[filtered_backlog_df[column].isin(filter_criteria[column])]
        elif filter_column and filter_criteria:
            filtered_backlog_df = self.work_backlog[self.work_backlog[filter_column].isin(filter_criteria)]
        else:
            filtered_backlog_df = self.work_backlog
        if type(empty_columns) == list:
            for column in empty_columns:
                filtered_backlog_df = filtered_backlog_df[filtered_backlog_df[column].isnull()]
        elif type(empty_columns) == str:
            filtered_backlog_df = filtered_backlog_df[filtered_backlog_df[empty_columns].isnull()]
        # ensure to never automatically classify manual classified documents again
        if automated_classification:
            filtered_backlog_df = filtered_backlog_df[filtered_backlog_df["Classified"] != "ManualClassifier"]
        custom_iterator = filtered_backlog_df.itertuples()
        backlog_size = filtered_backlog_df.shape[0] + 1    #+1 for index 0
        print("{}\nWorking Backlog size:\t{}\n{}".format("+"*30,backlog_size,"+"*30))
        return custom_iterator

    def run_classification(self, backlog_csv_path=None, filter_column=None, filter_criteria=None, empty_columns=None, move_docs=False, debug_mode=False):
        self.time_measurement_list = []
        self.get_work_backlog(backlog_csv_path)
        if debug_mode:
            chromedriver_path = os.path.join(self.cwd,"chromedriver")
            driver = webdriver.Chrome(chromedriver_path)
        try:
            assert filter_criteria != ["/Handler_Manually"] and filter_criteria != ["/Handler_Irrelevant"], "Don't automatically calssify this folder again!!"
            custom_iterator = self.create_backlog_iterator(filter_column, filter_criteria, empty_columns, automated_classification=True)
            for current_tuple in custom_iterator:
                doc_working_start_time = time.time()
                # load html Document as soup
                if self.is_document_available(current_tuple):
                    if debug_mode:
                        driver.get("file:///{}".format(self.current_working_document_filepath))
                    with open(self.current_working_document_filepath) as file:
                        soup = BeautifulSoup(file, "html.parser")
                    if self.has_tabular_format(soup):
                        case, classifier, proposed_directory, document_information_dict = self.classify_tabular(soup)
                    else:
                        # TODO
                        """
                        Implement:
                        1. Classify Regex
                        2. Handle other cases
                        """
                        case, classifier, proposed_directory, document_information_dict = self.classify_non_tabular(soup)
                    if case != "irrelevant" and case:
                        event_date, comment = self.regex_event_search(soup)
                    elif case == "irrelevant" or not(case):
                        event_date, comment = None, None
                else:
                    case, classifier, proposed_directory, document_information_dict = None, "FileNotFound", "NotFound", None
                    event_date, comment = None, None

                self.update_backlog_tuple(case, classifier, proposed_directory, current_tuple, document_information_dict, move_docs=move_docs)
                self.update_event_date(event_date, comment, current_tuple)
                self.measure_doc_working_time(doc_working_start_time, current_tuple.Index)
        except Exception as e:
            print("Something went wrong at DocumentID {}".format(current_tuple.DocumentID))
            print("Exception thrown: {}".format(e))
        except KeyboardInterrupt:
            print("Execution was interrupted!\nSaving Backlog...")
        # Save csv-file:
        self.save_work_backlog()
        print("Backlog saved!")
        # if interrupted or done print time KPI
        if len(self.time_measurement_list) > 0:
            average_classification_time = round(mean(self.time_measurement_list),3)
        else:
            average_classification_time = 0
        print("{}\nClassification run completed.\
               \nAverage classification time per document:\t{}\
               \nFor in total documents classified:\t.\t{}\
               \nDocuments moved:\t.\t.\t.\t{}\
               \n{}".format("+"*60,average_classification_time,len(self.time_measurement_list), self.classification_run_counter, "-"*60))
        print("Please Check Document with ID \t.\t.\t{}\n{}".format(current_tuple.DocumentID,"+"*60))
        self.classification_run_counter = 0

    def classify_manually(self, backlog_csv_path=None, filter_column=None, filter_criteria=None, move_docs=False):
        self.time_measurement_list = []
        self.get_work_backlog(backlog_csv_path)
        chromedriver_path = os.path.join(self.cwd,"chromedriver")
        driver = webdriver.Chrome(chromedriver_path)
        try:
            custom_iterator = self.create_backlog_iterator(filter_column, filter_criteria)
            for current_tuple in custom_iterator:
                doc_working_start_time = time.time()
                if self.is_document_available(current_tuple):
                    # output soup
                    driver.get("file:///{}".format(self.current_working_document_filepath))
                    # demand input
                    while True:
                        action = input("Does the document with ID {} seem relevant? (y/n/skip/interrupt): ".format(current_tuple.DocumentID))
                        if action == "y" or action == "n" or action == "interrupt" or action == "skip":
                            break
                        else:
                            print("Bad input. Please use (y/n/interrupt) only!")
                            continue
                    if action == "y":
                        # move file to relevant folder
                        case, classifier, = "relevant", "ManualClassifier"
                        proposed_directory = self.manually_classified_filepath
                    elif action == "n":
                        # move file to irrelevant folder
                        case, classifier, = "irrelevant", "ManualClassifier"
                        proposed_directory = self.irrelevant_html_filepath
                    elif action == "interrupt":
                        print("Classification interrupted.")
                        break
                    elif action == "skip":
                        continue
                    else:
                        print("Ooops! Something went wrong here! Aborting...")
                        break

                    document_information_dict = None
                    self.update_backlog_tuple(case, classifier, proposed_directory, current_tuple, document_information_dict, move_docs=move_docs)
                    self.measure_doc_working_time(doc_working_start_time, current_tuple.Index)
        except Exception as e:
            print("Exception at Document ID {}\nAborting...".format(current_tuple.DocumentID))
            print("Exception: {}".format(e))
        driver.quit()
        # Save csv-file:
        self.save_work_backlog()
        print("Backlog saved!")
        # if interrupted or done print time KPI
        if len(self.time_measurement_list) > 0:
            average_classification_time = round(mean(self.time_measurement_list),3)
        else:
            average_classification_time = 0
        print("Classification run completed.\
               \nAverage classification time per document:\t{}\
               \nFor in total documents classified:\t{}\n\
               Documents moved:\t{}".format(average_classification_time,len(self.time_measurement_list), self.classification_run_counter))
        print("Please Check Document with ID {}".format(current_tuple.DocumentID))
        self.classification_run_counter = 0

    def update_event_date(self, event_date, comment, backlog_tuple):
        if event_date != None:
            self.work_backlog.at[backlog_tuple.Index, "EventDate"] = event_date
        self.work_backlog.at[backlog_tuple.Index, "Comment"] = comment

    def define_event_dates(self, path_to_event_list_backlog_csv=None, filter_column=None, filter_criteria=None, empty_columns=None, mode="manually", debug_mode=False):
        self.time_measurement_list = []
        self.get_event_list_backlog(path_to_event_list_backlog_csv)
        chromedriver_path = os.path.join(self.cwd,"chromedriver")
        driver = webdriver.Chrome(chromedriver_path)
        try:
            custom_iterator = self.create_backlog_iterator(filter_column, filter_criteria, empty_columns)
            if mode == "manually" or mode == "m":
                self.manually_set_event_dates(driver, custom_iterator)
            elif mode == "automated" or mode == "a":
                self.automatical_event_parsing(driver, custom_iterator, debug_mode)
            else:
                raise NotImplementedError("Please use modes 'automated'(a) or 'manually'(m) only!")
        except Exception as e:
            print("\tException: {}\n\tAborting...".format(e))
        except KeyboardInterrupt:
            print("Execution was interrupted!\nSaving Backlog...")
        driver.quit()
        # Save csv-file:
        self.save_work_backlog()
        print("Backlog saved!")
        # if interrupted or done print time KPI
        if len(self.time_measurement_list) > 0:
            average_classification_time = round(mean(self.time_measurement_list),3)
        else:
            average_classification_time = 0
        print("Classification run completed.\
               \nAverage classification time per document:\t{}\
               \nFor in total documents classified:\t.\t{}\
               \nEvent dates entered:\t.\t.\t.\t{}".format(average_classification_time,len(self.time_measurement_list)+1, self.classification_run_counter))
        self.classification_run_counter = 0

    def manually_set_event_dates(self, driver, custom_iterator):
        for current_tuple in custom_iterator:
            doc_working_start_time = time.time()
            if self.is_document_available(current_tuple):
                # output soup
                driver.get("file:///{}".format(self.current_working_document_filepath))
                # demand input
                print("Working on ID:\t{}".format(current_tuple.DocumentID))
                while True:
                    date_string = input("\tPlease enter event date: ")
                    event_date = convert_datestring(date_string)
                    if event_date or date_string == "skip":
                        comment = input("\tWant to leave a comment?: ")
                        break
                    elif date_string == "interrupt": 
                        break
                    else:
                        print("\tBad input. Please enter a date!")
                        continue
                if date_string != "skip" and date_string != "interrupt":
                    # update event list backlog
                    self.update_event_date(event_date, comment, current_tuple)
                elif date_string == "interrupt":
                    print("\tClassification interrupted.")
                    break
                elif date_string == "skip":
                    if comment != "":
                        self.update_event_date(None, comment, current_tuple)
                    continue
                else:
                    print("Ooops! Something went wrong here! Aborting...")
                    break
                self.measure_doc_working_time(doc_working_start_time, current_tuple.Index)

    def automatical_event_parsing(self, driver, custom_iterator, debug_mode=False):
            for current_tuple in custom_iterator:
                doc_working_start_time = time.time()
                # load html Document as soup
                if self.is_document_available(current_tuple):
                    if debug_mode:
                        driver.get("file:///{}".format(self.current_working_document_filepath))
                    with open(self.current_working_document_filepath) as file:
                        soup = BeautifulSoup(file, "html.parser")
                    event_date, comment = self.regex_event_search(soup)
                else:
                    raise FileNotFoundError("\tDocument with ID {} was not found :'(")
                self.update_event_date(event_date, comment, current_tuple)
                self.measure_doc_working_time(doc_working_start_time, current_tuple.Index)
    
    def regex_event_search(self, soup):
        page_string = " ".join(re.split(r"\s+", soup.get_text(), flags=re.UNICODE))
        match = re.findall(r"(am|per|zum)\s?([\d]{1,4}[.-])\s?([\d]{1,2}[.-]|Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s?(\d{2,4}),?\s?(unter|die Schwelle|unterschritt|die Meldeschwellen?|Schwellen|den Schwelle?n?wert|die in § 21 Abs. 1 WpHG|veräußert|durch d?i?e? ?Veräußerung|durch Aktien|die Stimmrechtsschwellen|fiel|ihr Stimmrechtsanteil|sein Stimmrechtsanteil|aufgrund von Erwerb/Veräußerung|aufgrund einer Veräußerung)", page_string, re.IGNORECASE) or\
            re.findall(r"(Datum der Schwellenberü?u?e?hrung:? )(\d{1,4}[.-])\s?(\d{1,2}[.-]|Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s?(\d{2,4})", page_string, re.IGNORECASE)
        if len(match) == 1:
            start = match[0][1].replace(".","").replace("-","")
            mid = match[0][2].replace(".","").replace("-","")
            end = match[0][3]
            if mid in self.month_string_mapping:
                mid = self.month_string_mapping[mid]
            date_string = "{}.{}.{}".format(start, mid, end)
            event_date = convert_datestring(date_string)
            comment = "RegexSearch"
        elif len(match) > 1:
            comment = "RegexSearch"
            event_dates_list = []
            for pos, next_match in enumerate(match):
                start = next_match[1].replace(".","").replace("-","")
                mid = next_match[2].replace(".","").replace("-","")
                end = next_match[3]
                if mid in self.month_string_mapping:
                    mid = self.month_string_mapping[mid]
                if pos == 0:
                    first_date_string = "{}.{}.{}".format(start, mid, end)
                    event_date = convert_datestring(first_date_string)
                    event_dates_list.append(first_date_string)
                else:
                    next_date_string = "{}.{}.{}".format(start, mid, end)
                    if next_date_string in event_dates_list:
                        continue
                    else:
                        comment = "{}\n{}".format(comment,next_date_string)
                        event_dates_list.append(next_date_string)         
        else:
            event_date = None
            comment = "Regex Failed"
        return event_date, comment

def prepare_event_list_csv(file_directory, save_filename=None, delimiter_comma=False):
    """
    Screens ResultFile of classification for relevant events (with event dates)
    and transforms all numbers so that they have comma as decimal delimiter
    """
    columns_to_use = ["CompanyName", 
                    "AdditionalInformationType",
                    "DocumentID",
                    "ReasonForInformation",
                    "DateOfCorrection",
                    "DateOfInformation",
                    "Classified",
                    "ClassificationTime",
                    "FileDirectory",
                    "NewVotingRights",
                    "OldVotingRights",
                    "DeltaVotingRights",
                    "NewInstrumentVotingRights",
                    "OldInstrumentVotingRights",
                    "NewTotalVotingRights",
                    "OldTotalVotingRights",
                    "DeltaTotalVotingRights",
                    "NewNumberOfVotingRights",
                    "EventDate",
                    "Comment",
                    "MaxBordersCrossed",
                    "MinBordersCrossed",
                    "Blockholders",
                    "IrrelevantBlockholders"
                    ]
    transform_to_str_columns = ["NewVotingRights",
        "OldVotingRights",
        "DeltaVotingRights",
        "NewInstrumentVotingRights",
        "OldInstrumentVotingRights",
        "NewTotalVotingRights",
        "OldTotalVotingRights",
        "DeltaTotalVotingRights",
        "NewNumberOfVotingRights",
        "ClassificationTime",
        "MaxBordersCrossed",
        "MinBordersCrossed",
        ]
    event_list_df = pd.read_csv(file_directory, sep=";",usecols=columns_to_use)
    event_list_df[transform_to_str_columns].astype(str)
    # filter values for Events with EventDates
    event_list_df = event_list_df[event_list_df["FileDirectory"].isin(["/RegexThirdLevel/Success"])]
    # event_list_df = event_list_df[event_list_df["EventDate"].notna()]
    if delimiter_comma:
        # Excel / Sheets use commas instead of dots as decimal delimiter: replace . with , in numbers
        event_list_df[transform_to_str_columns] = event_list_df[transform_to_str_columns].applymap(lambda x: str(x).replace(".",","))
    if not(save_filename):
        filename_suffix = datetime.now().strftime("%Y%m%d") # <== optional: Hour and Minute: _%H%M
        save_filename = "EventsPreparedForSheets_{}.csv".format(filename_suffix)
    event_list_df.to_csv(save_filename, sep=";")
    return

def classify():
    # *************************************************************
    # Set parameters for run here
    # *************************************************************
    # backlog_filepaths_folders = ["Sites",
    #                             "Handler_Classification_Failed",
    #                             "Handler_RegexPreClassified",
    #                             "Handler_Relevant",
    #                             "Handler_RegexSecondLevel",
    #                             "Handler_Manually",
    #                             "Handler_Irrelevant"
    #                             ]
    backlog_filepaths_folders = ["RegexThirdLevel/Implement",
                                 "RegexThirdLevel/DoubleCheck",
                                 "RegexThirdLevel/Irrelevant",
                                 "RegexThirdLevel/Success"
                                ]
    custom_classification_column = None                        # <== AS list ["FileDirectory"]
    custom_classification_criteria = None # <== AS dict, keys are columns, values can be dicts with criteria  {"FileDirectory":["/RegexThirdLevel/Success"]} 
    empty_columns = None    # None or ColumnName as string or ColumnNames as list
    backlog_csv_file = "BacklogRegexThirdLevel.csv"
    move_docs = False        # <== True or "copy" or False
    debug_mode = False
    ignore_errors = True
    # not yet implemented in init
    success_filepath = os.path.join(os.getcwd(),"RegexThirdLevel/Success")
    irrelevant_filepath = os.path.join(os.getcwd(),"RegexThirdLevel/Irrelevant")
    double_check_filepath = os.path.join(os.getcwd(),"RegexThirdLevel/DoubleCheck")
    not_implemented_filepath = os.path.join(os.getcwd(),"RegexThirdLevel/Implement")
    for _ in [success_filepath, irrelevant_filepath, double_check_filepath, not_implemented_filepath]:
        if not os.path.exists(_):
            os.makedirs(_)
    # *************************************************************
    # End of parameters
    # *************************************************************
    my_handler = Classification_Handler(backlog_filepaths_folders)
    my_handler.ignore_errors = ignore_errors
    my_handler.relevant_html_filepath = success_filepath
    my_handler.success_filepath = success_filepath
    my_handler.irrelevant_filepath = irrelevant_filepath
    my_handler.double_check_filepath = double_check_filepath
    my_handler.not_implemented_filepath = not_implemented_filepath
    my_handler.run_classification(backlog_csv_file, custom_classification_column, custom_classification_criteria, empty_columns, move_docs, debug_mode)
    # my_handler.classify_manually(backlog_csv_file, custom_classification_column, custom_classification_criteria, move_docs=False)
    prepare_event_list_csv(backlog_csv_file, "EventsPreparedForSheets.csv")

def events():
    # *************************************************************
    # Set parameters for run here
    # *************************************************************
    backlog_filepaths_folders = ["Handler_Manually",
                                 "Handler_Relevant",
                                 "Handler_RegexSecondLevel"
                                ]
    custom_classification_column = ["FileDirectory"]
    custom_classification_criteria = {"FileDirectory":["/Handler_RegexSecondLevel", "/Handler_Relevant", "/Handler_Manually"],
                                      }
    empty_columns = "EventDate"
    backlog_csv_file = "EventList.csv"
    # *************************************************************
    # End of parameters
    # *************************************************************
    my_handler = Classification_Handler(backlog_filepaths_folders)
    my_handler.define_event_dates(backlog_csv_file, custom_classification_column, custom_classification_criteria, empty_columns, mode="a", debug_mode=False)

def move():
    # *************************************************************
    # Set parameters for run here
    # *************************************************************
    backlog_filepaths_folders = ["Sites",
                                "Handler_Classification_Failed",
                                "Handler_RegexPreClassified",
                                "Handler_Relevant",
                                "Handler_RegexSecondLevel",
                                "Handler_Irrelevant"
                                ]
    backlog_csv_file = None
    # *************************************************************
    # End of parameters
    # *************************************************************
    my_handler = Classification_Handler(backlog_filepaths_folders)
    my_handler.move_docs(backlog_csv_file, debug_mode=True)

if __name__ == "__main__":
    classification_start_time = time.time()
    # *************************************************************
    classify()
    # *************************************************************
    classification_end_time = time.time()
    elapsed_time = classification_end_time - classification_start_time
    print("Total time elapsed: \t.\t.\t.\t{}".format(timedelta(seconds=elapsed_time)))