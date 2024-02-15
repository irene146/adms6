# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 11:00:21 2024

@author: Jake
"""

import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns

# load the data
df = pd.read_csv("momentum_ws_15.levels.gst", header=0)

# delete useless columns
df.drop(columns=['Year', 'Day', 'Hour', 'Time(s)', 'Z(m)'], inplace=True)

# delete columns that only have 0 values 
df_plot = df.loc[:, (df != 0).any(axis=0)] 

# create a square grid of subplots
num_plots = len(df_plot.columns) - 2  # number of 'Z' columns excluding 'X' and 'Y'
num_cols = int(num_plots**0.5)
num_rows = (num_plots + num_cols - 1) // num_cols

fig, axes = plt.subplots(num_rows, num_cols, figsize=(20, 20))

# flatten the axes array in case it's a single row or column
axes = axes.flatten()

global_min = df_plot.iloc[:, 2:].min().min()
global_max = df_plot.iloc[:, 2:].max().max()


# loop through each 'Z' column and create a heatmap
for i, z_column in enumerate(df_plot.columns[2:]):  # [2:] because x and y are the two first columns 
    ax = axes[i]
    
    # extract the Z value from the column name
    z_value = z_column.split('|')[3].strip()  # Extracts the 'Z=0m' part
    
    # reshape the data for heatmap
    heatmap_data = df_plot.pivot(index='Y(m)', columns='X(m)', values=z_column)
    heatmap_data_plot = heatmap_data.loc[:, (heatmap_data != 0).any(axis=0)] 

    # Plot the heatmap with vmin and vmax
    graph = sns.heatmap(heatmap_data_plot, ax=ax, cmap='YlOrBr', cbar_kws={'label': 'CH4 enhancement / ppb'})
    
       #change legend font size using stack overflow tricks 
    graph.figure.axes[-1].yaxis.label.set_size(30)
    #graph.figure.axes[-1].yaxis.tick_params.set_size(20)

    ax.set_title(z_value)
    
    #set font size 
    ax.tick_params(axis='both', labelsize=17)
    ax.set_xlabel('X (m)', fontsize=25)
    ax.set_ylabel('Y (m)', fontsize=25)
    ax.set_title(z_value, fontsize=30)


# Adjust layout
plt.tight_layout()

# Show the plot
plt.show()

plt.savefig('ADMS.png')