# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 13:06:09 2023

@author: Beth and translated wihth ai. modifications by Irene 
"""
import pandas as pd

# Assuming FAAM_data is a pandas DataFrame containing the necessary columns

# Rename columns and perform necessary calculations
met_data = pd.DataFrame(columns=["YEAR", "TDAY", "THOUR", "T0C", "U", "PHI", "P", "CL", "H"])


# Function to create met data file for ADMS input
def print_adms_met(data, path):
    # Get column names
    names = data.columns
    
    # Find length of names
    len_names = len(names)
    
    # Collapse names into one string, separated by \n (new line)
    names_str = "\n".join(names)
    
    # Create header in the same way
    header = f"VARIABLES:\n{len_names}\n{names_str}\nDATA:\n"
    
    # Write header
    with open(path, 'w') as f:
        f.write(header)
    
    # Write the rest of the table (without col/row names)
    data.to_csv(path, mode='a', sep=',', header=False, index=False)

# Call the function
for x in range(20,25):
    met_data.loc[0,'YEAR'] = 1
    met_data.loc[0,'TDAY'] = 1
    met_data.loc[0,'THOUR'] = 1
    met_data.loc[0,'T0C'] = x
    met_data.loc[0,'U'] = 1
    met_data.loc[0,'PHI'] = 1
    met_data.loc[0,'P'] = 1
    met_data.loc[0,'CL'] = 1
    met_data.loc[0,'H'] = 1
    print_adms_met(met_data, f"C:/directory/metfile_variable_{x}.met")
