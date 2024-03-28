# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 12:03:13 2024

@author: Jake

import nappy in a wierd way from: https://github.com/cedadev/nappy, ask dave 
import FAAM library from https://github.com/FAAM-146/faam-datautils
"""
import nappy
import netCDF4
import sys
import pandas as pd
import numpy as np
from faamda.wrapper import FAAM
import matplotlib.pyplot as plt
import os 

#####read core data 
faam = FAAM(['d:\\faam_data_b689_final']) #recognises faam flight data on that directory 
faam.flights #recognises what flights you have available 
b689 = faam['b689'].core #put core flight data that you want in a variable 
data = b689[['LAT_GIN', 'LON_GIN', 'HGT_RADR']] #select variables that you want to include
'''
for variable names: https://www.faam.ac.uk/sphinx/coredata/dynamic_content/coredata.html#variables
for windir 
def uv_to_spddir(u, v):
    _spd = (u**2 + v**2) ** .5
    _dir = np.arctan2(u/_spd, v/_spd) * 180 / np.pi
    return _spd, _dir
from: https://github.com/FAAM-146/decades-ppandas/blob/master/ppodd/utils/conversions.py
'''
data = data.interpolate().dropna() #interpolte over all values of lat long gin so that frequencies match 


fgga = pd.read_csv('fgga_b689_fixed.csv', index_col=[0], parse_dates=True, date_format="ISO8601")  #import fgga data correcting for date format 

new_index = data.index.union(fgga.index).sort_values()  #join indexes for both fgga and core data (they dont match)
data2 = data.reindex(new_index).interpolate().loc[fgga.index] #create new df where you interpolate lat lon hgt values over fgga values as well
                                                              #then after .loc[fgga.index] only picks values that had fgga time           
for i in fgga.columns: #paste fgga columns to data 2 so that timestamp is the same 
    data2[i] = fgga[i]
    
data2.plot()

data2.to_csv('fgga_core_b689.csv')
