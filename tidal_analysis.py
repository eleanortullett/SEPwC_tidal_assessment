"""
    A set of functions to provide manipulation of data for tidal analysis

    Author: Eleanor Tullett
    Date: 28th May 2024
    Revision: managed by Git
    Course: Solving Environmental Problems with Code
"""

#!/usr/bin/env python3

# import the modules you need here
# from datetime import datetime
import argparse
#import datetime
import pandas as pd
import numpy as np
from matplotlib import dates
import scipy as sp
import uptide
#import pytz


# making the column names global so can easily be changed and reduces
# the risk of typos occuring
columnNames = ["Index", "Date", "Time", "Sea Level", "Sea Level Rise"]


def read_tidal_data(filename):
    """
    reads a text file containing tidal data.

    Args:
        filename: the name of the data file to read.

    Returns:
        data: the data frame containing the data with the header stripped out
        and formatted with column names held in a global variable "columnnames"

    Raises:
        exception: If the file cannot be found.
    """
    # 1.Read the file
    # 2.the first 11 lines of the file are the header which is not required
    # 3. the delimiting in the file is a white space rather than a comma
    # we define the first 11 rows to not be used
    no_of_header_rows_to_skip = 11
    # use a try/catch in case there is a failure
    try:
        data = pd.read_csv(
            filename,
            delim_whitespace=True,
            header=None,
            skiprows=no_of_header_rows_to_skip,
            names=columnNames,
        )

        # find the date/time in the columns
        data["DateTime"] = pd.to_datetime(
            data["Date"] + " " + data["Time"], format="%Y/%m/%d %H:%M:%S"
        )

        # set the data index using the datatime as the reference
        data.set_index("DateTime", inplace=True)

        # now we need to find the NaN values that may be present and
        # replace them with nan. Wwe can use the numpy nan value
        # applied to sea level
        data.replace(
            to_replace=".*M$", value={columnNames[3]: np.nan}, regex=True, inplace=True
        )
        data.replace(
            to_replace=".*N$", value={columnNames[3]: np.nan}, regex=True, inplace=True
        )
        data.replace(
            to_replace=".*T$", value={columnNames[3]: np.nan}, regex=True, inplace=True
        )
        # applied to sea level rise
        data.replace(
            to_replace=".*M$", value={columnNames[4]: np.nan}, regex=True, inplace=True
        )
        data.replace(
            to_replace=".*N$", value={columnNames[4]: np.nan}, regex=True, inplace=True
        )
        data.replace(
            to_replace=".*T$", value={columnNames[4]: np.nan}, regex=True, inplace=True
        )

        # convert the sea level to a floating point type
        data[columnNames[3]] = data[columnNames[3]].astype(float)

        # return the data
        return data

    # throw an exception if the filename specified cannot be found
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"The file {filename} does not exist") from exc


def extract_section_remove_mean(start, end, data):
    """
    extracts a portion of the date between a start and end date.

    Args:
        start: date in the format YYYYMMDD
        end: date in the format YYYYMMDD
        data: the data frame

    Returns:
        extracted_data: the data that has been extracted between the two dates

    """
    # start is a date in the format YYYYMMDD
    # end is a date in the format YYYYMMDD

    # convert start and end into strings data
    data_string_start = str(start)
    data_string_end = str(end)

    extracted_data = data.loc[data_string_start:data_string_end, [columnNames[3]]]

    # remove mean
    mmm = np.mean(extracted_data[columnNames[3]])
    extracted_data[columnNames[3]] -= mmm

    return extracted_data


def join_data(data1, data2):
    """
    combines two sets of data into a single dataframe.

    Args:
        data1 and data2

    Returns:
        data: the dataframe containing the concatenated dataframes

    Raises:
        exception: If the data joining fails.
    """
    # Concatenate the data and return the joined data
    # to pass the test, the order of the data concatenation is important
    # i.e. we add data2 to data1
    try:
        data = pd.concat([data2, data1])
    # Catching a TypeError which can occur if a non-string element is in the list
    except TypeError as exc:
        raise ValueError(f"Concatenation error joining data: {exc}") from exc
    return data


def extract_single_year_remove_mean(year, data):
    """
    extracts data from a single year, removes the mean to centre the data
    around zero and returns the resultant data file

    Args:
        Year as a string
        data to be extracted from

    Returns:
        year_data: the data frame containing the data with within a given
        year with the data centred around zero
    """
    # copied code from SEPwC documentation
    year_string_start = str(year) + "0101"
    year_string_end = str(year) + "1231"
    year_data = data.loc[year_string_start:year_string_end, [columnNames[3]]]
    # remove mean
    mmm = np.mean(year_data[columnNames[3]])
    year_data[columnNames[3]] -= mmm

    return year_data


def sea_level_rise(data):
    """
    calculates the slope and p_value from the supplied data frame

    Args:
        data frame to calulate the rise from.

    Returns:
        slope and p_value from the data frame
    """
    # drop any nan values from the data in the Sea Level column
    data = data.dropna(subset=[columnNames[3]])

    data.index = pd.to_datetime(data.index)

    x_value = dates.date2num(data.index)
    y_value = data[columnNames[3]]

    slope, p_value, _, _, _ = sp.stats.linregress(x_value, y_value)

    # Return the slope and p-value
    return slope, p_value

def tidal_analysis(data, constituents, start_datetime):
    """
    Performs harmonic analysis on tidal data.
    
    Args:
        data: DataFrame containing the tidal data.
        constituents: List of tidal constituents.
        start_datetime: Start date and time for the analysis.

    Returns:
        amp: Amplitude of tidal constituents.
        pha: Phase of tidal constituents.
        
    Code based on SEPwC documentation
    """
    # Ensure start_datetime is timezone naive
    if start_datetime.tzinfo is not None:
        start_datetime = start_datetime.replace(tzinfo=None)

    # Create a tide object containing a list of the constituents
    tide = uptide.Tides(constituents)
    tide.set_initial_time(start_datetime)
    # Make the data index timezone naive
    data.index = data.index.tz_localize(None)
    # Calculate the number of seconds since start time
    seconds_since = (data.index - start_datetime).total_seconds()
    # Convert sea level to a numpy array
    sl = data[columnNames[3]].values

    # Filter out NaN values
    is_a_number = pd.notna(sl)
    sl = sl[is_a_number]
    seconds_since = seconds_since[is_a_number]

    # Perform harmonic analysis
    amp, pha = uptide.harmonic_analysis(tide, sl, seconds_since)

    return amp, pha


def get_longest_contiguous_data(data):
    """
    reads a data frame and works out the largets chunk of contiguous data.

    Args:
        the data frame

    Returns:
        contiguous_data frame
    """

    # identify the not a number values from the 4th col of the dataframe
    # this should be sea level. Needs bitwise invert so not_nan is true
    # when numbers are not nan!
    not_nan = ~data[columnNames[3]].isna()
    # cummulatively sum the data over the series so result is a series
    # of contiguos groups of true and false
    groups = (not_nan != not_nan.shift()).cumsum()
    # find the an integer to the most frequent integer in the group
    largest_group = groups.value_counts().idxmax()
    # select the block of most contiguous numbers that are not nan
    contiguous_data = data[groups == largest_group]

    return contiguous_data


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="UK Tidal analysis",
        description="Calculate tidal constiuents and RSL from tide gauge data",
        epilog="Copyright 2024, Eleanor Tullett",
    )

    parser.add_argument(
        "directory", help="the directory containing txt files with data"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False, help="Print progress"
    )

    args = parser.parse_args()
    dirname = args.directory
    verbose = args.verbose
