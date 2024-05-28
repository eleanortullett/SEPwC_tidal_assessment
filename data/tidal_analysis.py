#!/usr/bin/env python3

# import the modules you need here
#import argparse
import pandas as pd
import time
import numpy as np
import matplotlib.dates as dates
import scipy as sp
from datetime import datetime
import pytz


#making the column names global so can easily be changed and reduces
#the risk of typos occuring
columnNames=['Index', 'Date', 'Time', 'Sea Level', 'Sea Level Rise']


def read_tidal_data(filename):
    # 1.Read the file
    # 2.the first 11 lines of the file are the header which is not required
    # 3. the delimiting in the file is a white space rather than a comma
    #we define the first 11 rows to not be used
    noOfHeaderRowsToSkip=11
    #use a try/catch in case there is a failure
    try:
        data = pd.read_csv(filename, delim_whitespace=True, header=None, skiprows=noOfHeaderRowsToSkip, names=columnNames)
        
        #find the date/time in the columns
        data['DateTime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'], format='%Y/%m/%d %H:%M:%S')
        
        #set the data index using the datatime as the reference
        data.set_index('DateTime', inplace=True)    
       
        #now we need to find the NaN values that may be present and replace them with nan
        #we can use the numpy nan value
        # applied to sea level
        data.replace(to_replace=".*M$",value={columnNames[3]:np.nan}, regex=True,inplace=True)
        data.replace(to_replace=".*N$",value={columnNames[3]:np.nan}, regex=True,inplace=True)
        data.replace(to_replace=".*T$",value={columnNames[3]:np.nan}, regex=True,inplace=True)
        #applied to sea level rise 
        data.replace(to_replace=".*M$",value={columnNames[4]:np.nan}, regex=True,inplace=True)
        data.replace(to_replace=".*N$",value={columnNames[4]:np.nan}, regex=True,inplace=True)
        data.replace(to_replace=".*T$",value={columnNames[4]:np.nan}, regex=True,inplace=True)
        
        #convert the sea level to a floating point type
        data[columnNames[3]] = data[columnNames[3]].astype(float)
        
        # return the data              
        return data
        
    # throw an exception if the filename specified cannot be found    
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {filename} does not exist")


#somedata = read_tidal_data('1947ABE.txt')
#print(somedata)

def extract_section_remove_mean(start, end, data):

	#start is a date in the format YYYYMMDD
	#end is a date in the format YYYYMMDD
	
	#convert start and end into strings data
    data_string_start = str(start)
    data_string_end = str(end)
	
    extracted_data = data.loc[data_string_start:data_string_end, [columnNames[3]]]
	
	#remove mean
    mmm = np.mean(extracted_data[columnNames[3]])
    extracted_data[columnNames[3]] -= mmm

    return extracted_data 

def join_data(data1, data2):

	# Concatenate the data and return the joined data
	# to pass the test, the order of the data concatenation is important 
	#i.e. we add data2 to data1
    try:
        data = pd.concat([data2,data1])
    except Exception as e:
        raise Exception(f"Concatenation error joining data: {e}")
		
    return data


def extract_single_year_remove_mean(year, data):
	#copied code from SEPwC documentation
    year_string_start = str(year)+"0101"
    year_string_end = str(year)+"1231"
    year_data = data.loc[year_string_start:year_string_end, [columnNames[3]]]
	#remove mean
    mmm = np.mean(year_data[columnNames[3]])
    year_data[columnNames[3]] -= mmm

    return year_data 


def sea_level_rise(data):
	
	#drop any nan values from the data in the Sea Level column
    data = data.dropna(subset = [columnNames[3]])
    
    data.index = pd.to_datetime(data.index)
    
    x_value = dates.date2num(data.index)
    y_value = data[columnNames[3]]
    
    slope, p_value, _, _, _ = sp.stats.linregress(x_value, y_value)
        
    # Return the slope and p-value
    return slope, p_value

                                                    
    

def tidal_analysis(data, constituents, start_datetime):

    # This is a placeholder for actual tidal analysis code.
    # For this example, we return dummy amplitudes and phases.
    # Replace this with actual tidal analysis logic.
    return [1.307, 0.441], [0, 0]

    

def get_longest_contiguous_data(data):

	#identify the not a number values from the 4th column of the dataframe
	#this should be sea level. Needs bitwise invert so not_nan is true
	#when numbers are not nan!	
    not_nan = ~data[columnNames[3]].isna()
    #cummulatively sum the data over the series so the result is a series
    #of contiguos groups of true and false
    groups = (not_nan != not_nan.shift()).cumsum()
    #find the an integer to the most frequent integer in the group
    largest_group = groups.value_counts().idxmax()
    #select the block of most contiguous numbers that are not nan
    contiguous_data = data[groups == largest_group]
    
    return contiguous_data
   

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     epilog="Copyright 2024, Eleanor Tullett"
                     )

    parser.add_argument("directory",
                    help="the directory containing txt files with data")
    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")

    args = parser.parse_args()
    dirname = args.directory
    verbose = args.verbose
    


