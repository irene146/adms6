
"""
Created on Tue Feb  6 11:00:21 2024

@author: Irene
"""

import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns
import os 
import glob 
#put all gst files you want to analyse in the same directory as the script
# store current working directory 
path = os.getcwd()

#create list of files in that directory 
gst_files = glob.glob(os.path.join(path, "*.gst")) 
  
# loop over the list of csv files, and sotre the files in a dictionary of dfs 
file_dfs = {}
for f in gst_files:
    file_name = os.path.splitext(os.path.basename(f))[0]
    file_dfs[file_name] = pd.read_csv(f, header=0)
    
    
#create empty lists 
max_ch4= []
ws=[]
height=[] 

#loop over each file at different wind speeds 
for file in file_dfs:
    ws_current = file.split('_')[2].split('.')[0].strip()#store current winspeed
    #loop over each height colum in current file 
    for i, z_column in enumerate(file_dfs[file].columns[7:]):
        height_current = z_column.split('=')[1].split('.')[0]#store current height value 
        height.append(height_current) 
        max_ch4_current = file_dfs[file][z_column].max()#store max ch4 enhancement at that height
        max_ch4.append(max_ch4_current)
        ws.append(ws_current)#store current windspeed 
#put all the lists in a df 
df = pd.DataFrame({'Wind Speed / ms^-1':ws ,'Height / m': height, 'Max_CH4_enhancement': max_ch4})

#turn everything into numbers  
df = df.astype(float)

heatmap_data = df.pivot(index='Height / m', columns='Wind Speed / ms^-1', values='Max_CH4_enhancement')

# plotting the heatmap 
hm = sns.heatmap(data=heatmap_data, 
                annot=True,
                cbar_kws={'label': 'CH4 enhancement / ppb'},
                yticklabels=heatmap_data.index[::-1]) 
  
# displaying the plotted heatmap 
plt.show() 

