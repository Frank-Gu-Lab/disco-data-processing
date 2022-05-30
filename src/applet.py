import streamlit as st
import numpy as np
import time

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

from sklearn.preprocessing import MaxAbsScaler
from discoprocess.data_plot import generate_buildup_curve
from discoprocess.data_plot import generate_fingerprint
from discoprocess.data_plot_helpers import tukey_fence

import importlib
std = importlib.import_module("standard-figures")

# define handy shortcut for indexing a multi-index dataframe
idx = pd.IndexSlice

# import all data wrangling functions for Pt. 1 & 2, and data merge function for Pt. 3
from discoprocess.data_wrangling_functions import *
from discoprocess.data_merging import merge, etl_per_replicate, etl_per_sat_time, etl_per_proton
from discoprocess.data_analyze import *
from discoprocess.data_checker import *

#list all raw books in file
list_of_raw_books = st.file_uploader("Please provide a file", accept_multiple_files = True)

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

    st.text("Hooray! All polymers in the input files have been processed.")

# PART 3 - MERGE TRUE POSITIVE AND TRUE NEGATIVE BINDING OBSERVATIONS ---------------------

# makes a global ouput directory for merged data if not existing
merge_output_directory = "{}/merged".format(global_output_directory)

if not os.path.exists(merge_output_directory):
    os.makedirs(merge_output_directory)

# define data source path and data destination path to pass to data merging function
source_path = '{}/*/tables_*'.format(global_output_directory)
destination_path = '{}'.format(merge_output_directory)

replicate_summary_df = etl_per_replicate(source_path, destination_path)
replicate_summary_df.to_excel(os.path.join(merge_output_directory, "merged_binding_dataset.xlsx"))

quality_check_df = etl_per_sat_time(source_path, destination_path)
quality_check_df.to_excel(os.path.join(merge_output_directory, "merged_fit_quality_dataset.xlsx"))

proton_summary_df = etl_per_proton(quality_check_df)
proton_summary_df.to_excel(os.path.join(merge_output_directory, "proton_binding_dataset.xlsx"))

st.text("Data processing completed! Summary dataset files are available in the output directory under merged.")

polymer_library_binding = set(glob.glob("../data/output/merged/stats_analysis_output_mean_*")) - set(glob.glob("../data/output/merged/stats_analysis_output_mean_all_*"))

# significant and zero peaks
polymer_library_all = glob.glob("../data/output/merged/stats_analysis_output_mean_all_*")

polymer_library_replicates = glob.glob("../data/output/merged/stats_analysis_output_replicate_*")

merged_bind_dataset = pd.read_excel("../data/output/merged/merged_binding_dataset.xlsx")

# Define a custom output directory for formal figures
output_directory = "../data/output/publications"

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# plot DISCO Effect build up curves with only significant peaks
for polymer in polymer_library_binding:

    binding_directory = f"{output_directory}/binding"

    if not os.path.exists(binding_directory):
        os.makedirs(binding_directory)

    polymer_name = std.grab_polymer_name(full_filepath = polymer,
    common_filepath="../data/output/merged/stats_analysis_output_mean_")

    # read polymer datasheet
    polymer_df = pd.read_excel(polymer, index_col=[0, 1, 2, 3], header=[0, 1])

    generate_buildup_curve(polymer_df, polymer_name, binding_directory)


# plot DISCO Effect build up curves with insignificant and significant peaks overlaid
for polymer in polymer_library_all:
    binding_directory2 = f"{output_directory}/all_peaks"

    if not os.path.exists(binding_directory2):
        os.makedirs(binding_directory2)

    polymer_name = std.grab_polymer_name(full_filepath=polymer,
                                     common_filepath="../data/output/merged/stats_analysis_output_mean_all_")

    # read polymer datasheet
    polymer_df = pd.read_excel(polymer, index_col=[0, 1, 2, 3], header=[0, 1])

    generate_buildup_curve(polymer_df, polymer_name, binding_directory2)


# plot binding fingerprints
binding_directory = f"{output_directory}/binding"

unique_bind_polymers = merged_bind_dataset.loc[merged_bind_dataset['AFo'] != 0, ('polymer_name')].unique()

# iterate through figures per polymer
for polymer in unique_bind_polymers:
    plot_df = merged_bind_dataset.loc[(merged_bind_dataset['polymer_name'] == polymer) & (merged_bind_dataset['AFo'] != 0)].copy()

    # identify univariate outliers in plot_df using Tukey-Fence method
    plot_df_outliers = tukey_fence(plot_df, 'AFo')
    # print(plot_df_outliers)

    # subset df to remove probable outliers
    plot_df_no_outliers = plot_df_outliers[plot_df_outliers['outlier_prob'] == False]

    # fit normalizer to AFo in the plot df after outliers removed
    scaler = MaxAbsScaler()
    plot_df_outliers['AFo_norm'] = scaler.fit(abs(plot_df_no_outliers['AFo'].values).reshape(-1,1))

    # transform all data (including outliers) and mark flagged outliers on plot, so outliers not used as normalization ref point
    plot_df_outliers['AFo_norm'] = scaler.transform(abs(plot_df_outliers['AFo'].values).reshape(-1,1))
    plot_df_outliers['SSE_bar_norm'] = scaler.transform(abs(plot_df_outliers['SSE_bar'].values).reshape(-1, 1))
    plot_df_outliers['AFo_bar_norm'] = scaler.transform(abs(plot_df_outliers['AFo_bar'].values).reshape(-1, 1))
    plot_df_outliers['SSE_norm'] = scaler.transform(abs(plot_df_outliers['SSE'].values).reshape(-1, 1))

    generate_fingerprint(plot_df_outliers, polymer, binding_directory)
