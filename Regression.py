#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:11:43 2019

@author: erik
"""

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import statsmodels.tools
import statsmodels.formula.api as smf
from datetime import datetime
import statsmodels.stats.diagnostic as smd   #Breusch-Pagan and White test


def get_regression_data(loadpath="Regression/Input_Files/DotDelimiter - Copy of Events - RegressionVariablesValues.csv"):
    # prepare the data
    dataset = pd.read_csv(loadpath, header=0)
    rename_mapper = {'CAR_[-10;+10]':'car_10_10',
                     'CAR_[-5;+5]':'car_5_5',
                     'CAR_[-2;+5]':'car_2_5',
                     'CAR_[-2;+2]':'car_2_2',
                     'CAR_[-1;+1]':'car_1_1',
                     'CAR_[-1;+0]':'car_1_0',
                     }
    dataset = dataset.rename(columns=rename_mapper)
    # perform log-transformation
    dataset['LOG(MarketCap_T-1)'] = np.log(dataset['MarketCap_T-1'])
    dataset['LOG(NetSales_T-1)'] = np.log(dataset['NetSales_T-1'])
    dataset['LOG(TurnoverByVolume)'] = np.log(dataset['TurnoverByVolume'])
    all_columns = ['Block_3','Block_5','Block_10','Block_20','Block_30','GROUP_A',
                   'GROUP_F','GROUP_S','Leverage_T-1','MarketCap_T-1', 'NetSales_T-1', 
                   'SalesGrowth', 'MarketToBookValue_T-1','ReturnOnAssets_T-1', 'TurnoverByVolume',
                   'LOG(MarketCap_T-1)', 'LOG(NetSales_T-1)', 'LOG(TurnoverByVolume)']
    dataset = dataset.replace([np.inf, -np.inf], np.nan)
    dataset = dataset.dropna()
    return dataset

def print_regression_results(data_list, name=None, save_summary=False):
    data = dataset[data_list]
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna()
    y = data[data_list[0]]
    X = data[data_list[1:]]
    X = statsmodels.tools.tools.add_constant(X)
    ols_result = sm.OLS(y, X).fit(cov_type='HC0')
    if name != None:
        print("{}\n{}\n{}".format("="*60,name,"-"*60))
    print("Standard:")
    print(ols_result.summary())
    print("\n\n")
    if save_summary:
        regression_summary_path = os.path.join(os.getcwd(),"Regression/Results/summary_{}.csv".format(datetime.now().strftime("%Y_%m_%d")))
        if not os.path.exists(regression_summary_path):
            with open(regression_summary_path, "w+") as file:
                file.write('created on {}\n'.format(datetime.now().strftime("%d.%m.%Y at %H:%M")))
        with open(regression_summary_path, "a") as file:
            file.write("'{}\n{}, created on {}\n{}\n".format("="*60,name,datetime.now().strftime("%d.%m.%Y at %H:%M"),"-"*60))
            file.write("{}\n".format(ols_result.summary().as_csv()))
    return ols_result


def perform_regression(dataset):
    # modify to save summarys as csv
    save_summary_bool = True
    
    regression_dict = {"Model 20":['car_1_0','GROUP_A','GROUP_S','Leverage_T-1', 'SalesGrowth', 'MarketToBookValue_T-1','ReturnOnAssets_T-1', 'LOG(MarketCap_T-1)', 'LOG(NetSales_T-1)', 'BlockholderExchange'],
                       "Model 21":['car_1_0','Block_5','Block_10','Block_20','Block_30','Leverage_T-1', 'SalesGrowth', 'MarketToBookValue_T-1','ReturnOnAssets_T-1', 'LOG(MarketCap_T-1)', 'LOG(NetSales_T-1)', 'BlockholderExchange'],
                       "Model 22":['car_1_0','Block_5','Block_10','Block_20','Block_30','GROUP_A', 'GROUP_S','Leverage_T-1', 'SalesGrowth', 'MarketToBookValue_T-1','ReturnOnAssets_T-1', 'LOG(MarketCap_T-1)', 'LOG(NetSales_T-1)', 'BlockholderExchange'],
                       "Model 23":['car_1_0','Leverage_T-1', 'SalesGrowth', 'MarketToBookValue_T-1','ReturnOnAssets_T-1', 'LOG(MarketCap_T-1)', 'LOG(NetSales_T-1)', 'BlockholderExchange'],
                       }
    results_dict ={}
    for key in regression_dict.keys():
        result = print_regression_results(regression_dict[key], key, save_summary=save_summary_bool)
        results_dict[key] = result
    return regression_dict, results_dict


def plot_data(dataset, y_vals=None):
    plot_vars = ['Leverage_T-1', 'SalesGrowth', 'MarketToBookValue_T-1',
                 'ReturnOnAssets_T-1', 'LOG(MarketCap_T-1)',
                 'LOG(NetSales_T-1)', 'BlockholderExchange']  # 'LOG(TurnoverByVolume)',
    try:
        if y_vals == None:
            y_vals = dataset['Group']
    except ValueError:
        pass
    for name in plot_vars:
        plt.figure()
        plt.scatter(dataset[name],y_vals,label=name.replace('_T-1',""))
        plt.xlabel(name.replace('_T-1',""))

        
def white_test(regression_dict, results_dict):
   data = dataset[regression_dict["Model 8"]]
   data = data.replace([np.inf, -np.inf], np.nan)
   data = data.dropna()
   Xes = ['Block_3','Block_5','Block_10','Block_20','Block_30','GROUP_A','GROUP_F','GROUP_S','Leverage_T-1','SalesGrowth','MarketToBookValue_T-1','ReturnOnAssets_T-1','LOG(MarketCap_T-1)','LOG(NetSales_T-1)','LOG(TurnoverByVolume)']
   for exog in Xes:
       white = smd.het_white(results_dict["Model 8"].resid, statsmodels.tools.tools.add_constant(data[exog]))
       if white[1] > 0.05:
           print("Factor: {}\t--> Homoscedasticity\t :)".format(exog))
       else:
           print("Factor: {}\t--> HETEROSCEDASTICITY :(".format(exog))
         
def breusch_pagan_test(dataset, regression_dict, results_dict):
    for key in regression_dict.keys():
        BP_statistic = smd.het_breuschpagan(results_dict[key].resid, dataset[regression_dict[key][1:]])
        print("{}\nBP:\t{:.2f}\nP-Val:\t{:.4f}".format(key,BP_statistic[0],BP_statistic[1]))
    
           
def patsy_style_tests(dataset):
    # =============================================================================
    # Patsy style tests
    # =============================================================================
          
    formula_blocksize = 'car_1_1 ~ C(BlockSize, Treatment("THREE")) + Q("Leverage_T-1") + Q("SalesGrowth") + Q("MarketToBookValue_T-1") + Q("ReturnOnAssets_T-1") + Q("LOG(TurnoverByVolume)") + Q("LOG(NetSales_T-1)") + Q("LOG(MarketCap_T-1)")'
    
    df = dataset[['car_2_2','car_5_5', 'car_10_10','Group','BlockSize', 'Leverage_T-1', 'SalesGrowth', 'MarketToBookValue_T-1','ReturnOnAssets_T-1', 'MarketCap_T-1', 'NetSales_T-1', 'TurnoverByVolume']].dropna()
    mod = smf.ols(formula='car_2_2 ~ C(BlockSize, Treatment("THREE")) + C(Group, Treatment("FinancialBlock")) + np.log(Q("MarketCap_T-1")) + SalesGrowth + np.log(TurnoverByVolume) + Q("ReturnOnAssets_T-1") + np.log(Q("NetSales_T-1")) + Q("Leverage_T-1") + Q("MarketToBookValue_T-1")', data=df)
    res = mod.fit()
    print(res.summary())
            
    df = dataset[['car_2_2','Group','BlockSize','Leverage_T-1',
                   'MarketCap_T-1', 'NetSales_T-1', 
                   'SalesGrowth', 'MarketToBookValue_T-1',
                   'ReturnOnAssets_T-1', 'TurnoverByVolume']]
    mod = smf.ols(formula='car_2_2 ~ C(BlockSize, Treatment("THREE")) + Q("Leverage_T-1")+ np.log(Q("MarketCap_T-1")) + SalesGrowth + Q("MarketToBookValue_T-1") + Q("ReturnOnAssets_T-1")', data=df)
    res = mod.fit()
    print(res.summary())
    print("\n\n\n")
    
    mod = smf.ols(formula='car_2_2 ~ C(Group, Treatment("FinancialBlock")) + Q("Leverage_T-1")+ np.log(Q("MarketCap_T-1")) + SalesGrowth + Q("MarketToBookValue_T-1") + Q("ReturnOnAssets_T-1")', data=df)
    res = mod.fit()
    print(res.summary())          
    # =============================================================================

def bhar_scatterplot(bhar):
    legend_mapper = {'22':1, '66':3, '132':6,'264':12}
    marker_mapper = {'Activist':'o', 'Strategic':'^', 'FinancialBlock':'D'}
    color_mapper = {'Activist':'#4285f4', 'Strategic':'#34a853', 'FinancialBlock':'#ea4335'}
    label_mapper = {'Activist':'Aktivist', 'Strategic':'Strategisch', 'FinancialBlock':'FinBlock'}
    groups = pd.unique(bhar['GROUP'])
    for key in legend_mapper.keys():
        plt.figure()
        for group in groups:
            plt.scatter(bhar[key][bhar['GROUP']==group]*100, bhar['car_1_0'][bhar['GROUP']==group]*100, label=label_mapper[group], c=color_mapper[group], marker=marker_mapper[group])
            plt.legend(loc='upper right')
            plt.xlabel('BHAR [%]')
            plt.ylabel('CAR [%]')
            plt.grid(True)
            if legend_mapper[key] == 1:
                plural = ''
            else:
                plural = 'e'
            plt.title('{} Monat{} nach Ereignis'.format(legend_mapper[key], plural))
 
def load_bhar():
    bhar = pd.read_csv("/Users/erik/Documents/Thesis/03 Arbeitsordner/02 Datensatz/python_project/BHAR/DotDelimiter - Copy of Pivot-Data.csv")
    bhar = bhar[['EVENT-ID', 'GROUP', 'ISIN', 'DATE','car_1_0', '22', '66', '132', '264']]
    return bhar
    
if __name__ == "__main__":
    
    # get data
    dataset = get_regression_data()
    
    # perform regression
    regression_dict, results_dict = perform_regression(dataset)

    # Breusch-Pagan for each Model
    breusch_pagan_test(dataset, regression_dict, results_dict)
    
    # White Test for every Column:
    # white_test(regression_dict, results_dict)
    
    # use patsy style formulas
    #patsy_style_tests(dataset)
    