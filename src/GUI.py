import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t
import scipy.stats as stats
from scipy.optimize import curve_fit
import os
import glob
import shutil as sht

# define handy shortcut for indexing a multi-index dataframe
idx = pd.IndexSlice

# import all data wrangling functions for Pt. 1 & 2, and data merge function for Pt. 3
from discoprocess.data_wrangling_functions import *
from discoprocess.data_merging import merge, etl_per_replicate, etl_per_sat_time, etl_per_proton
from discoprocess.data_analyze import *
from discoprocess.data_checker import *

from sklearn.preprocessing import MaxAbsScaler
from discoprocess.data_plot import generate_buildup_curve
from discoprocess.data_plot import generate_fingerprint
from discoprocess.data_plot_helpers import tukey_fence

from PIL import Image

st.header("Welcome to the DISCO Data Processing Interactive GUI")

st.info("To begin your DISCO data processing, please enter a directory below where output files may be stored")
global_output_directory_1 = st.text_input("Directory: ")

list_of_raw_books = []

if global_output_directory_1 != None and global_output_directory_1 != "":
    global_output_directory = "../data/output/" + global_output_directory_1
    if not os.path.exists(global_output_directory):
        os.makedirs(global_output_directory)
    st.success("Thank you!  Please upload your data files to begin data processing!")
    list_of_raw_books = st.file_uploader("Please provide input files", accept_multiple_files = True)

i = 0


@st.cache(suppress_st_warning = True)
def analysis(list_of_raw_books):
    st.info("Checking names of polymers in datasets for correct formatting")

    i = 0

    if name_checker(list_of_raw_books):
        st.success("Names are formatted correctly!")
        i += 1

    if resonance_and_column_checker(list_of_raw_books):
        st.success("Data formatted correctly!")
        i += 1

    if range_checker(list_of_raw_books):
        st.success("Data ranges are all correct!")
        i += 1

    if i == 3:
        st.info("Great! Now it is time for data analysis!")
        i += 1

    batch_tuple_list = []

    clean_batch_tuple_list = []
    clean_batch_list = []

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
        with st.spinner("Analyzing data..."):
            analyze_data(clean_batch_tuple_list, global_output_directory)
            i += 1

    if i == 5:
        return

if len(list_of_raw_books) > 0:
    analysis(list_of_raw_books)
    i += 5


if i == 5:
    st.success("All polymers successfully analyzed")
    sht.make_archive(os.path.abspath('../data/output/' + global_output_directory_1), 'zip', '../data/output/',os.path.abspath(global_output_directory))
    with open('../data/output/' + global_output_directory_1 + '.zip', 'rb') as f:
       st.download_button('Download Zip with Analyzed Data', f, file_name=global_output_directory_1+'.zip')
       i += 1

if i == 6:
    # makes a global ouput directory for merged data if not existing
    merge_output_directory = "{}/merged".format(global_output_directory)

    if not os.path.exists(merge_output_directory):
        os.makedirs(merge_output_directory)
    # define data source path and data destination path to pass to data merging function
    source_path = '{}/*/tables_*'.format(global_output_directory)
    destination_path = '{}'.format(merge_output_directory)

    replicate_summary_df = etl_per_replicate(source_path, destination_path)
    rep_sum = replicate_summary_df.to_excel(os.path.join(merge_output_directory, "merged_binding_dataset.xlsx"))

    quality_check_df = etl_per_sat_time(source_path, destination_path)
    qual_check = quality_check_df.to_excel(os.path.join(merge_output_directory, "merged_fit_quality_dataset.xlsx"))

    proton_summary_df = etl_per_proton(quality_check_df)
    prot_sum = proton_summary_df.to_excel(os.path.join(merge_output_directory, "proton_binding_dataset.xlsx"))

    sht.make_archive(os.path.abspath(merge_output_directory), "zip", global_output_directory, os.path.abspath(merge_output_directory))
    with open(merge_output_directory + ".zip", "rb") as f:
        st.download_button("Press to download merged datesets", f, file_name = "merged" + ".zip")
        i = i + 1


if i == 7:

    st.info("Preparing supporting figures:")

    with st.spinner("Establishing directories"):
        # for only the peaks with a significant disco effect
        polymer_library_binding = set(glob.glob(merge_output_directory + "/stats_analysis_output_mean_*")) - set(glob.glob(merge_output_directory + "/stats_analysis_output_mean_all_*"))

        # significant and zero peaks
        polymer_library_all = glob.glob(merge_output_directory + "/stats_analysis_output_mean_all_*")

        polymer_library_replicates = glob.glob(merge_output_directory + "/stats_analysis_output_replicate_*")

        merged_bind_dataset = pd.read_excel(merge_output_directory + "/merged_binding_dataset.xlsx")

        # Define a custom output directory for formal figures

        output_directory = '{}/publications'.format(global_output_directory)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        i = i + 1

def grab_polymer_name(full_filepath, common_filepath):
    '''Grabs the polymer name from file path.

    Parameters:
    -----------
    full_filepath: string
        path to the datasheet for that polymer

    common_filepath: string
        portion of the filepath that is shared between all polymer inputs, excluding their custom names

    Returns:
    -------
    polymer_name: string
        the custom portion of the filepath with the polymer name and any other custom info
    '''

    #Necessary for some windows operating systems
    for char in full_filepath:
        if char == "\\":
            full_filepath = full_filepath.replace("\\", "/")

    for char in common_filepath:
        if char == "\\":
            common_filepath = full_filepath.replace("\\", "/")

    polymer_name = full_filepath.split(common_filepath)[1]
    polymer_name = polymer_name[:-5] # remove the .xlsx

    return polymer_name


if i == 8:

    st.success("Directories created, now preparing figures.")

    st.info("Generating buildup curves:")

    with st.spinner("Buildup curves being generated"):
        # plot DISCO Effect build up curves with only significant peaks
        for polymer in polymer_library_binding:

            binding_directory = f"{output_directory}/binding"

            if not os.path.exists(binding_directory):
                os.makedirs(binding_directory)

            polymer_name = grab_polymer_name(full_filepath = polymer,
            common_filepath= merge_output_directory + "/stats_analysis_output_mean_")

            # read polymer datasheet
            polymer_df = pd.read_excel(polymer, index_col=[0, 1, 2, 3], header=[0, 1])

            generate_buildup_curve(polymer_df, polymer_name, binding_directory)


        # plot DISCO Effect build up curves with insignificant and significant peaks overlaid
        for polymer in polymer_library_all:
            binding_directory2 = f"{output_directory}/all_peaks"

            if not os.path.exists(binding_directory2):
                os.makedirs(binding_directory2)

            polymer_name = grab_polymer_name(full_filepath=polymer,
                                             common_filepath= merge_output_directory + "/stats_analysis_output_mean_all_")

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

        i += 1

if i == 9:
    sht.make_archive(os.path.abspath(output_directory), "zip", global_output_directory, os.path.abspath(output_directory))
    with open(output_directory + ".zip", "rb") as f:
        st.download_button("Press to download figures", f, file_name = "publications"+ ".zip")
        i += 1


#Well sailors, it be Monday...
list_of_buildup_curves = []
list_of_fingerprints = []
list_of_curves = []

if i == 10:

    list_of_curves = glob.glob(binding_directory + "/*")

    if len(list_of_curves) > 0:
        for curve in list_of_curves:
            if "fingerprint" in curve:
                list_of_fingerprints.append(curve)
            else:
                list_of_buildup_curves.append(curve)

    if len(list_of_fingerprints) > 0 and len(list_of_buildup_curves) > 0:
        i += 1

if i == 11:
    st.info("The following polymers exhibit binding, please select from the list to view plots!")
    option  = st.radio("Buildup curves and fingerprints available, for which polymer would you like to see these plots?", unique_bind_polymers)

    for curve in list_of_buildup_curves:
        if option in curve:
            build_address = curve
    for curve in list_of_fingerprints:
        if option in curve:
            fingerprint_address = curve

    build_image = Image.open(build_address)
    fingerprint_image = Image.open(fingerprint_address)

    st.image(fingerprint_image, use_column_width = True)
    st.image(build_image, use_column_width = True)
