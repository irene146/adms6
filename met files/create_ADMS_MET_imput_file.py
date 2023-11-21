# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 13:06:09 2023

@author: Beth 
"""

import pandas as pd

# Assuming FAAM_data is a pandas DataFrame containing the necessary columns

# Rename columns and perform necessary calculations
met_data = FAAM_data.rename(columns={"SHIP": "STATION DCNN", "ws": "U", "wdir": "PHI", "tat_nd_r": "T0C"})
met_data["TDAY"] = met_data["date"].dt.dayofyear
met_data["THOUR"] = met_data["date"].dt.hour
met_data["YEAR"] = met_data["date"].dt.year
met_data["U"] = met_data["U"].round()
met_data["PHI"] = met_data["PHI"].round()
met_data["T0C"] = met_data["T0C"].round()
met_data["CL"] = met_data["CL"].round()

# Select relevant columns
met_data = met_data[["STATION DCNN", "YEAR", "TDAY", "THOUR", "T0C", "U", "PHI", "CL"]]

# Function to create met data file for ADMS input
def print_adms_met(data, path):
    # Get column names
    names = data.columns
    
    # Find length of names
    len_names = len(names)
    
    # Collapse names into one string, separated by \n (new line)
    names_str = "\n".join(names)
    
    # Create header in the same way
    header = f"VARIABLES:\n{len_names}\n{names_str}\nDATA:"
    
    # Write header
    with open(path, 'w') as f:
        f.write(header)
    
    # Write the rest of the table (without col/row names)
    data.to_csv(path, mode='a', sep=',', header=False, index=False)

# Call the function
print_adms_met(met_data, "C:/wherever/you/want/to/save/metfile.met")
