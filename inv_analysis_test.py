import pandas as pd 


def diff(r1, r2):
    # Calculate the differences for each column
    diff_lat = r1['lat'] - r2['lat']
    diff_long = r1['long'] - r2['long']
    diff_h = r1['h'] - r2['h']
    diff_conc = r1['conc'] - r2['conc']
    diff_total = diff_lat + diff_long + diff_h + diff_conc
    return diff_total


# Initialize an empty DataFrame to store the results
result_df = pd.DataFrame(columns=df2.columns)
# Iterate through rows in the first dataset
for index, r1 in df1.iterrows():
    # Initialize variables to store the minimum difference and the corresponding row
    #min_diff = 
    #min_diff_row
    # Iterate through rows in the second dataset
    for _, r2 in df2.iterrows():
        # Calculate the difference using the diff function
        current_diff = diff(r1, r2)
        # Check if the current difference is smaller than the minimum difference
        if abs(current_diff) < abs(min_diff):
            min_diff = current_diff
            min_diff_row = r2
    # Append the row from the second dataset with the minimum difference to the result DataFrame
    result_df = result_df.append(min_diff_row)
# result_df now contains the rows from the second dataset that are most similar to each row in the first dataset
print(result_df)
