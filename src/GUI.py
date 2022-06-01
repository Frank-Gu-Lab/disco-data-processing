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

if len(list_of_raw_books) > 0:
    st.info("Checking names of polymers in datasets for correct formatting")

    if name_checker(list_of_raw_books, streamlit = True):
        st.success("Names are formatted correctly!")
        i += 1

    if resonance_and_column_checker(list_of_raw_books, streamlit = True):
        st.success("Data formatted correctly!")
        i += 1

    if range_checker(list_of_raw_books, streamlit = True):
        st.success("Data ranges are all correct!")
        i += 1

    if i == 3:
        st.info("Great! Now it is time for data analysis!")
        i += 1

batch_tuple_list = []

clean_batch_tuple_list = []
clean_batch_list = []


if i == 4:
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
        with st.spinner("Analyzing data..."):
            i += analyze_data(clean_batch_tuple_list, global_output_directory, streamlit = True)
    ######################################################

if i == 5:
    st.success("All polymers successfully analyzed")
    sht.make_archive(os.path.abspath('../data/output/' + global_output_directory_1), 'zip', '../data/output/',os.path.abspath(global_output_directory))
    with open('../data/output/' + global_output_directory_1 + '.zip', 'rb') as f:
       st.download_button('Download Zip with Analyzed Data', f, file_name=global_output_directory_1+'.zip')
