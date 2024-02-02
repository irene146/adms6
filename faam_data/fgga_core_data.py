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


##download and read FGGA data 
ifile = "C:\\Users\\Jake\\Downloads\\faam-fgga_faam_20190729_r1_c191.na"    
ds = nappy.openNAFile(ifile)  #open na file with nappy
ds.readData() #read data 


#fix timestamp 
time_units = ds.getIndependentVariable(0)[1] #recognises time data on file
time_units = time_units.replace('fractional', '').replace('elapsed','').strip() #remove wierd names 
timestamp = netCDF4.num2date(ds.X, time_units) #converts number to time format  


from collections import OrderedDict

_dict = OrderedDict()  #create empty organised dictionary (remebers what was added first )
_dict['timestamp'] = timestamp #adds timestamp to the dictionary 
for i, v in enumerate(['co2_ppm', 'co2_flag', 'ch4_ppb', 'ch4_flag']): #interates over the strings gettig both index (i) and value (v)                                                                       
    #print(f'reading {v}')
    _dict[v] = ds.V[i] #ask
df = pd.DataFrame(_dict) #converts _dic to a pandas dataframe
df = df.set_index('timestamp') #set index to timestamp column 


#reading data for a single gas 
#co2 = df.co2_ppm.copy(deep=True) #copy only co2 colum and timestamp   
#co2.loc[df.co2_flag>0] = np.nan #locate what values of co2 have a flag and convert them to nans 
#co2.plot()

df.to_csv('fgga_c191.csv')

#####read core data 
faam = FAAM(['C:\\Users\\Jake\\Downloads']) #recognises faam flight data on that directory 
faam.flights #recognises what flights you have available 

c191 = faam['c191'].core #put core flight data that you want in a variable 
data = c191[['LAT_GIN', 'LON_GIN', 'HGT_RADR']] #select variables that you want to include


data = data.interpolate().dropna() #interpolte over all values of lat long gin so that frequencies match 


fgga = pd.read_csv('fgga_c191.csv', index_col=[0], parse_dates=True, date_format="ISO8601")  #import fgga data correcting for date format 

new_index = data.index.union(fgga.index).sort_values()  #join indexes for both fgga and core data (they dont match)
data2 = data.reindex(new_index).interpolate().loc[fgga.index] #create new df where you interpolate lat lon hgt values over fgga values as well
                                                              #then after .loc[fgga.index] only picks values that had fgga time           
for i in fgga.columns: #paste fgga columns to data 2 so that timestamp is the same 
    data2[i] = fgga[i]
    
data2.plot()

data2.to_csv('fgga_core_c191.csv')

