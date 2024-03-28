# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 12:19:23 2024

@author: FAAM_Student
"""

import datetime
import pandas as pd
import numpy as np
from acruisepy import peakid
import matplotlib.pyplot as plt 
from scipy.optimize import curve_fit
from scipy.integrate import quad 
from scipy.stats import sem 

#load fgga data from James 
#fix timestamps and index

df = pd.read_csv("b689_fgga.csv", header=[0], parse_dates=True, index_col=0,
   date_parser=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y %H:%M"),)

df=df.loc[df.index>df.index[0]]
df=df.loc[df.index<df.index[-1]]
a = pd.date_range(start=df.index[0], end=df.index[-1]+datetime.timedelta(seconds=59), freq='s')
df.index=a

#filter by time 

start_time = datetime.datetime(2012, 4, 3, 13, 45, 0)
end_time = datetime.datetime(2012, 4, 3, 15, 45, 0)
df = df.loc[start_time : end_time]

#select only methane colum and delete calibration data 
ch4= df['CH4']

ch4.loc[df['CH4_Flag'] >1] = np.nan

#save in a csv

ch4.to_csv('fgga_b689_fixed.csv')

#run peak ID 

#yellow line(plume threshold)x:limit to detect plume
#blue line (plume starting):where plume starts once it is detected
bg = peakid.identify_background(ch4, bg_sd_window=3, bg_sd_threshold=0.3, bg_mean_window=116)
#peakid.plot_background(ch4, bg, plume_sd_threshold=10, plume_sd_starting=0.5)

plumes = peakid.detect_plumes(ch4, bg, plume_sd_threshold=10, plume_sd_starting=0.5, plume_buffer=20)
#peakid.plot_plumes(ch4, plumes)

#save areas in a df

ch4_areas = peakid.integrate_aup_trapz(ch4 - bg, plumes, dx=0.1)

#need to calculate sd for peak integration!!

#select plumes close to the source where plume was gaussian 

ch4_areas_gauss = ch4_areas.head(6)


#heights from elgin paper (approximated form core data)
heights= [30, 75, 150, 220, 295, 595]

#make dataset with height annd area 
ch4_areas_gauss['height'] = heights

ch4_plot = ch4_areas_gauss[["area", "height"]]

#average the last 3 datapoints and calculate mean standard error  

#reindex

ch4_plot.index = range(1, len(ch4_plot) + 1)


xdata, ydata = np.asarray(ch4_plot['height']), np.asarray(ch4_plot['area'])

last_y= ydata[-3:]
last_avg_y =np.mean(last_y)
last_std_y=sem(last_y)

ydata = np.append(ydata[:-3], np.tile(last_avg_y, 3))
y_errors_fit = np.concatenate(([0.1, 0.1, 0.1], np.tile(last_std_y, 3)))


# Define log normal function
def log_normal(x, yo, A, xo, width):
    return yo + A * np.exp(-(np.log(x/xo)/width)**2)

# Initial guess parameters
p0 = [40, 272, 80, 0.57]

# Fit the data
popt, pcov = curve_fit(log_normal, xdata, ydata, p0=p0, sigma=y_errors_fit)

yo, A, xo, width = popt

plt.errorbar(xdata, ydata, yerr=y_errors_fit, fmt='o', label='Data with Errors')

# Plot fit
xfit = np.linspace(min(xdata), max(xdata), 100)
yfit = log_normal(xfit, *popt)
plt.plot(xfit, yfit, 'r-', label='Fit')

plt.xlabel('Height')
plt.ylabel('Area')
plt.legend()
plt.show()


min_limit = np.min(xdata)
max_limit = np.max(xdata)


#  integrand function
def integrand(x):
    return log_normal(x, yo, A, xo, width)

# integrate the function over the range of ydata
result, error = quad(integrand, min_limit, max_limit)  #integral is correct 

