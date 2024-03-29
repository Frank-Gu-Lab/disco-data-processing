# -*- coding: utf-8 -*-
"""
Created on Thursday April 27 11:49 2021

@author: Samantha Stuart

Core disco data processing executable that governs global code operation.
"""

# importing required libraries:
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t
import scipy.stats as stats
from scipy.optimize import curve_fit
import os
import glob

# define handy shortcut for indexing a multi-index dataframe
idx = pd.IndexSlice

# import all data wrangling functions for Pt. 1 & 2, and data merge function for Pt. 3
from discoprocess.data_wrangling_functions import *
from discoprocess.data_merging import merge, etl_per_replicate, etl_per_sat_time, etl_per_proton
from discoprocess.data_analyze import *
from discoprocess.data_checker import *

# ESTABLISH LOCAL DIRECTORY PATHS ---------------------

#assign the local path to the raw Excel books
raw_book_path = os.path.abspath('../data/input')
print('Searching in directory:', raw_book_path, '\n')

#list all raw books in file
list_of_raw_books = glob.glob("../data/input/*.xlsx")
print('List of raw books to be analyzed are: ', list_of_raw_books, '\n')

# makes a global ouput directory if there isn't already one
global_output_directory = "../data/output"

if not os.path.exists(global_output_directory):
    os.makedirs(global_output_directory)

# PERFORM DATA WRANGLING - CONVERT ALL EXCEL BOOKS IN INPUT FOLDER TO DATAFRAMES ---------------------

# initialize global lists to hold all tuples generated, one tuple per polymer input will be generated (current_book_title, clean_df)
batch_tuple_list = []

clean_batch_tuple_list = []
clean_batch_list = []

#Input checking testing grounds:
#########################################################
name_checker(list_of_raw_books)
resonance_and_column_checker(list_of_raw_books)
range_checker(list_of_raw_books)
#########################################################

# Convert all Excel books in the input folder into tuple key-value pairs that can be indexed
for book in list_of_raw_books:
    #append tuples from the list output of the batch processing function, so that each unique polymer tuple is assigned to the clean_batch_tuple_list
    batch_tuple_list.append([polymer for polymer in batch_to_dataframe(book)])

# PERFORM DATA CLEANING ON ALL BOOKS PROCESSED VIA BATCH PROCESSING ----------------

#if there has been batch data processing, call the batch cleaning function
if len(batch_tuple_list) != 0:

    clean_batch_list = clean_the_batch_tuple_list(batch_tuple_list)

    # convert clean batch list to a clean batch tuple list format (polymer_name, df) for further processing
    clean_batch_tuple_list = [(clean_batch_list[i]['polymer_name'].iloc[0], clean_batch_list[i]) for i in range(len(clean_batch_list))]


# LOOP THROUGH AND PROCESS EVERY CLEAN DATAFRAME IN THE BATCH LIST GENERATED ABOVE, IF ANY ----------------------------------

if len(clean_batch_tuple_list) != 0:

    analyze_data(clean_batch_tuple_list, global_output_directory)

    print("Hooray! All polymers in the input files have been processed.")

# PART 3 - MERGE TRUE POSITIVE AND TRUE NEGATIVE BINDING OBSERVATIONS ---------------------

# makes a global ouput directory for merged data if not existing
merge_output_directory = "{}/merged".format(global_output_directory)

if not os.path.exists(merge_output_directory):
    os.makedirs(merge_output_directory)

# define data source path and data destination path to pass to data merging function
source_path = '{}/*/tables_*'.format(global_output_directory)
destination_path = '{}'.format(merge_output_directory)


replicate_summary_df = etl_per_replicate(source_path, destination_path)
if replicate_summary_df is not None:
    replicate_summary_df.to_excel(os.path.join(merge_output_directory, "merged_binding_dataset.xlsx"))

if replicate_summary_df is not None:
    quality_check_df = etl_per_sat_time(source_path, destination_path)
    quality_check_df.to_excel(os.path.join(merge_output_directory, "merged_fit_quality_dataset.xlsx"))

    proton_summary_df = etl_per_proton(quality_check_df)
    proton_summary_df.to_excel(os.path.join(merge_output_directory, "proton_binding_dataset.xlsx"))
else:
    print("Proton_summary_df not generated due to no binding detected")

print("Data processing completed! Summary dataset files are available in the output directory under merged.")
