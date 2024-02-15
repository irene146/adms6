# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 10:57:22 2024

@author: Jake
"""

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
df = pd.read_csv("test3kgh50mh.levels.gst", header=0)

# delete useless columns
#df.drop(columns=['Year', 'Day', 'Hour', 'Time(s)', 'Z(m)'], inplace=True)

# delete columns that only have 0 values 
df_plot = df.loc[:, (df != 0).any(axis=0)] 

#pick the columns that you need 

df_plot_210m = df.filter(['X(m)','Y(m)','Conc|ppb|Methane|source     Z=215.0m |-|   1s'])

#reshape df for heatmap
heatmap_data = df_plot_210m.pivot(index='Y(m)', columns='X(m)', values='Conc|ppb|Methane|source     Z=215.0m |-|   1s')
heatmap_data_plot = heatmap_data.loc[:, (heatmap_data != 0).any(axis=0)] 

#plot 
sns.heatmap(heatmap_data_plot, cmap='YlOrBr', cbar_kws={'label': 'CH4 concentration / ppb'})
 
# Adjust layout
plt.tight_layout()

# Show the plot
plt.show()
