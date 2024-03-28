# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 11:48:09 2024

@author: FAAM_Student
"""
'''
import nappy in a wierd way from: https://github.com/cedadev/nappy, ask dave 
import FAAM library from https://github.com/FAAM-146/faam-datautils
for plane variable info: https://www.faam.ac.uk/sphinx/coredata/dynamic_content/coredata.html#variable-attributes
'''
import nappy
import netCDF4
import sys
import pandas as pd
import numpy as np
from faamda.wrapper import FAAM
import matplotlib.pyplot as plt
import datetime


#####read core data 

faam = FAAM(['d:\\faam_data_b689']) #recognises faam flight data on that directory 
faam.flights #recognises what flights you have available 
b689 = faam['b689'].core #put core flight data that you want in a variable 
df = b689[['LAT_GIN', 'LON_GIN', 'HGT_RADR', 'U_NOTURB', 'V_NOTURB', 'TAT_ND_R']] 

#select sampling period
start_time = datetime.datetime(2012, 4, 3, 13, 45, 0)
end_time = datetime.datetime(2012, 4, 3, 14, 40, 0)
df = df.loc[start_time : end_time]

##winds 
#delete turns and select are at 5NM (gaussian disperision)

wind = df.loc[(df['LON_GIN'] >= 1.58) & (df['LON_GIN'] <= 1.78)]
wind = wind.loc[(df['LAT_GIN'] >= 56.852) & (df['LAT_GIN'] <= 57)]
wind = wind.loc[(df['HGT_RADR'] <600)]

wind_plot = wind[["U_NOTURB", "V_NOTURB"]]

#convert u and v to ws and wdir 
def uv_to_spddir(u, v):
    _spd = (u**2 + v**2) ** .5
    _dir = np.arctan2(u/_spd, v/_spd) * 180 / np.pi
    return _spd, _dir

wind_plot[['ws', 'wdir']] = wind_plot.apply(lambda row: pd.Series(uv_to_spddir(row['U_NOTURB'], row['V_NOTURB'])), axis=1)

# drop original columns 
wind_plot.drop(columns=['U_NOTURB', 'V_NOTURB'], inplace=True)    

#plot to see if it is more or less the same to average 
'''
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(8, 8))

# plot wind speed
axes[0].plot(wind_plot.index, wind_plot['ws'], label='Wind Speed')
axes[0].set_ylabel('Speed (m/s)')
axes[0].legend()
# Plot wind direction
axes[1].plot(wind_plot.index, wind_plot['wdir'], label='Wind Direction')
axes[1].set_ylabel('Direction (degrees)')
axes[1].legend()
# Set common xlabel
axes[-1].set_xlabel('Time')
# Adjust layout
plt.tight_layout()
# Show plot
plt.show()
'''

#convert columns into arrays and calculate mean and sd 
ws_arr, wdir_arr = np.array(wind_plot['ws']), np.array(wind_plot['wdir'])


ws_avg, wdir_avg = np.mean(ws_arr), np.mean(wdir_arr)
wdir_sd = np.std(wdir_arr)

wdir_avg = 360 + wdir_avg
#temperature 

temp=  np.array(wind["TAT_ND_R"]-273.15)
mean_temp=np.mean(temp)

# BLH

#select varaibles for tephigram
blh_df = b689[['TAT_ND_R', 'HGT_RADR', 'TDEW_GE']]

#select time for profile
start_profile = datetime.datetime(2012, 4, 3, 13, 16, 37)  
end_profile = datetime.datetime(2012, 4, 3, 13, 41, 0)
blh_df = blh_df.loc[start_profile : end_profile]

#convert variables 
temperature = blh_df['TAT_ND_R'] - 273.15
height = blh_df['HGT_RADR']
dewpoint = blh_df['TDEW_GE'] - 273.15

#plot
plt.plot(temperature, height, label='Temperature (°C)', color='red')
plt.plot(dewpoint, height, label='Dew Point (°C)', color='blue')
plt.xlabel('Temperature/Dew Point (°C)')
plt.ylabel('Height (m)')
plt.legend()
plt.show()

blh= 1000



#make df for conversion to .met file (ADMS)

YEAR=2012
TDAY= 94
THOUR=14
CL = 6
PRECIP = 0 

met_data = {
    'YEAR': [YEAR],
    'TDAY': [TDAY],
    'THOUR': [THOUR],
    'T0C': [mean_temp],
    'U': [ws_avg],
    'PHI': [wdir_avg],
    'SIGMATHETHA': [wdir_sd],
    'CL': [CL],
    'H': [blh],
    'PRECIP': [PRECIP]
}

met_data = pd.DataFrame(met_data)


# function to create met data file for ADMS input
def print_adms_met(data, path):
    # get column names
    names = data.columns
    
    # gind length of names
    len_names = len(names)
    
    # collapse names into one string, separated by \n (new line)
    names_str = "\n".join(names)
    
    # create header in the same way
    header = f"VARIABLES:\n{len_names}\n{names_str}\nDATA:"
    
    # write header
    with open(path, 'w') as f:
        f.write(header)
    
    # Write the rest of the table (without col/row names)
    data.to_csv(path, mode='a', sep=',', header=False, index=False)


print_adms_met(met_data, "D:/faam_data_b689/b689_met.met")