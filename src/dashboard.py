import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
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

from discoprocess.wrangle_data import generate_disco_effect_mean_diff_df, generate_subset_sattime_df
from discoprocess.plotting import add_fingerprint_toax, add_buildup_toax, add_difference_plot_transposed, add_overlaid_buildup_toax_customlabels, add_difference_plot
from discoprocess.plotting_helpers import assemble_peak_buildup_df

from PIL import Image

#Setting up some stuff for the page
st.set_page_config(page_title = "DISCO Data Processing")

st.title("Welcome to the DISCO Data Processing Interactive GUI")

st.sidebar.markdown("## To begin your DISCO data processing, please enter a directory below where output files may be stored")
global_output_directory_1 = st.sidebar.text_input("Directory: ")

list_of_raw_books = []

if global_output_directory_1 != None:
    st.info("Would you like to upload data for data analysis, or plot data from the directory specified?")

    choice = st.radio(["Upload and analyze", "Plot existing data"])

if choice == "Upload and analyze":
    if global_output_directory_1 != None and global_output_directory_1 != "":
        global_output_directory = "../data/output/" + global_output_directory_1
        if not os.path.exists(global_output_directory):
            os.makedirs(global_output_directory)
        st.success("Thank you!  Please upload your data files to begin data processing!")
        list_of_raw_books = st.sidebar.file_uploader("Please provide input files", accept_multiple_files = True)

    i = 0
else:
    pass
