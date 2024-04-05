# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 10:19:28 2024

@author: FAAM_Student
"""

import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import numpy as np
import glob
from scipy.optimize import curve_fit
from scipy.integrate import quad

# Define the log-normal function
def log_normal(x, yo, A, xo, width):
    return yo + A * np.exp(-(np.log(x/xo)/width)**2)

def gaussian(x, a, b, c):
    return a *np.exp(-((x-b)**2)/2*c**2)


def ADMS_peak_area(filename):
    df_adms= pd.read_csv(filename, header=0)
    df_plot_adms = df_adms.filter(['X(m)','Y(m)','Conc|ppb|Methane|Elgin|-|   1s'])
    df_adms.rename(columns={df_adms.columns[-1]: 'CH4'}, inplace=True)
    
    # load the data fgga
    df_fgga= pd.read_csv("fgga_b689_x_y.csv", header=0, index_col=0)
    df_fgga = df_fgga.loc[(df_fgga['HGT_RADR'] >filename.split('_')[1].split('m')[0] -20) & (df_fgga['HGT_RADR'] <= filename.split('_')[1].split('m')[0] +20)]
    df_fgga = df_fgga.filter(['X','Y','CH4'])
    df_fgga['CH4'] = df_fgga.CH4 - 1889.0479508196722
    
    df_adms.rename(columns={df_adms.columns[-1]: 'CH4'}, inplace=True)
    adms_interpolated = griddata((df_adms['X(m)'], df_adms['Y(m)']), df_adms.CH4,(df_fgga.X, df_fgga.Y))
    x = df_fgga.X
    y = df_fgga.Y
    dist = (((x - x.shift())**2 + (y-y.shift())**2)**.5).cumsum().fillna(0)
    
    fit, cov = curve_fit(gaussian, dist, adms_interpolated)
    a, b, c = fit
    
    min_limit_dist = np.min(dist)
    max_limit_dist = np.max(dist)

    # Define the integrand function
    def integrand(x):
        return gaussian(x, a, b, c)

    int_gauss_result, int_error = quad(integrand, min_limit_dist, max_limit_dist)
    return int_gauss_result, int_error

    

# Directory containing all the folders
directory_1 = "/path/to/your/directory/"

# Glob all the folders
flux_folders = glob.glob(directory_1)

fluxes = []
ints = []
errs = []

# Iterate through each folder
for folder in flux_folders:
    flux = int(folder)  # Assuming the folder name is the flux and converting it to an integer
    fluxes.append(flux)
    
    directory_2 = directory_1 + str(flux) + "/"
    gst_files = glob.glob(directory_2 + "*.gst") 
    
    heights = []
    peak_areas = []
    peak_errors = []
    
    # Iterate through each file in the folder
    for filename in gst_files:
        peak_area, peak_error= ADMS_peak_area(filename)
        peak_areas.append(peak_area)
        
    
        peak_errors.append(peak_error)

        height = int(filename.split('_')[1].split('m')[0])  # Extract height from filename
        heights.append(height)
            
    # Fit the data
    popt, pcov = curve_fit(log_normal, heights, peak_areas, sigma=peak_errors)
    yo, A, xo, width = popt

    min_limit = np.min(heights)
    max_limit = np.max(heights)

    # Define the integrand function
    def integrand(x):
        return log_normal(x, yo, A, xo, width)

    # Integrate the function over the range of heights
    int_result, int_error = quad(integrand, min_limit, max_limit)
    ints.append(int_result)
    errs.append(int_error)

# Create a dictionary to hold the results
adms_results = {'flux': fluxes, 'peak_area': ints, 'peak_area_error': errs}

# Convert the dictionary to a pandas DataFrame
df_adms_results = pd.DataFrame(adms_results)





    
    