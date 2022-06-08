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

merge_output_directory = ""

if global_output_directory_1 != None and global_output_directory_1 != "":
    global_output_directory = "../data/output/" + global_output_directory_1
    if not os.path.exists(global_output_directory):
        os.makedirs(global_output_directory)
    # makes a global ouput directory for merged data if not existing
    merge_output_directory = "{}/merged".format(global_output_directory)

    if not os.path.exists(merge_output_directory):
        os.makedirs(merge_output_directory)
    # define data source path and data destination path to pass to data merging function
    source_path = '{}/*/tables_*'.format(global_output_directory)
    destination_path = '{}'.format(merge_output_directory)

list_of_raw_books = []

choice = None

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

if len(global_output_directory_1) > 0:

    choice = st.radio("Would you like to upload data for data analysis, or plot data from the directory specified?", ["Upload and analyze", "Plot existing data"])

if choice == "Upload and analyze":

    st.info("Please upload your data files to begin data processing!")
    list_of_raw_books = st.sidebar.file_uploader("Please provide input files", accept_multiple_files = True)

    i = 0


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

        try:

            replicate_summary_df = etl_per_replicate(source_path, destination_path)
            rep_sum = replicate_summary_df.to_excel(os.path.join(merge_output_directory, "merged_binding_dataset.xlsx"))

            quality_check_df = etl_per_sat_time(source_path, destination_path)
            qual_check = quality_check_df.to_excel(os.path.join(merge_output_directory, "merged_fit_quality_dataset.xlsx"))

            proton_summary_df = etl_per_proton(quality_check_df)
            prot_sum = proton_summary_df.to_excel(os.path.join(merge_output_directory, "proton_binding_dataset.xlsx"))

            sht.make_archive(os.path.abspath(merge_output_directory), "zip", global_output_directory, os.path.abspath(merge_output_directory))
            with open(merge_output_directory + ".zip", "rb") as f:
                st.download_button("Download Zip with Merged Datesets", f, file_name = "merged" + ".zip")
                i = i + 1
        except ValueError:
            st.info("There were no binding polymers, please rerun with a new dataset to try other samples! (simply upload more to begin the process)")

    if i == 7:
        st.info("Data analysis is complete.  If you would like to plot figures, please select the radio button above.")

elif choice == "Plot existing data":

    try:
        i = 0

        st.info("Preparing supporting figures.")

        list_of_polymers = []

        with st.spinner("Establishing directories for supporting figures"):

            # for only the peaks with a significant disco effect
            polymer_library_binding = set(glob.glob(merge_output_directory + "/stats_analysis_output_mean_*")) - set(glob.glob(merge_output_directory + "/stats_analysis_output_mean_all_*"))

            # significant and zero peaks
            polymer_library_all = glob.glob(merge_output_directory + "/stats_analysis_output_mean_all_*")

            polymer_library_replicates = glob.glob(merge_output_directory + "/stats_analysis_output_replicate_*")

            polymber_replicate_libary_binding = set(glob.glob(merge_output_directory + "/stats_analysis_output_replicate_*")) - set(glob.glob(merge_output_directory + ".stats_analysis_output_replicate_all_*"))

            # Define a custom output directory for formal figures

            output_directory = '{}/publications'.format(global_output_directory)

            if not os.path.exists(output_directory):
                os.makedirs(output_directory)

            binding_directory2 = f"{output_directory}/all_peaks"

            if not os.path.exists(binding_directory2):
                os.makedirs(binding_directory2)

            if len(polymer_library_all) > 0:
                for polymer in polymer_library_all:

                    polymer_name = grab_polymer_name(full_filepath=polymer,
                                                     common_filepath= merge_output_directory + "/stats_analysis_output_mean_all_")

                    # read polymer datasheet
                    polymer_df = pd.read_excel(polymer, index_col=[0, 1, 2, 3], header=[0, 1])

                    generate_buildup_curve(polymer_df, polymer_name, binding_directory2)
            i += 1

        if i == 1:

            for polymer in polymer_library_all:
                list_of_polymers.append(grab_polymer_name(polymer, common_filepath = merge_output_directory + "/stats_analysis_output_mean_all_"))

            mean_all_list = []
            mean_bindonly_list = []
            replicate_all_list = []
            replicate_bindonly_list = []

            non_binding = []

            with st.spinner("Buildup curves being generated"):
                # plot DISCO Effect build up curves with only significant peaks
                for polymer in list_of_polymers:

                    mean_all = pd.read_excel(merge_output_directory + "/stats_analysis_output_mean_all_" + polymer+ ".xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()
                    mean_all_list.append(mean_all)

                    try:
                        mean_bindonly = pd.read_excel(merge_output_directory + "/stats_analysis_output_mean_" + polymer + ".xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()
                        mean_bindonly_list.append(mean_bindonly)
                    except FileNotFoundError:
                        print("No binding polymers detected")

                    replicate_all = pd.read_excel(merge_output_directory + "/stats_analysis_output_replicate_all_" + polymer + ".xlsx", index_col=[0], header=[0]).reset_index(drop=True)
                    replicate_all_list.append(replicate_all)

                    try:
                        replicate_bindonly= pd.read_excel(merge_output_directory + "/stats_analysis_output_replicate_" + polymer + ".xlsx", index_col=[0], header=[0]).reset_index(drop=True)
                        replicate_bindonly_list.append(replicate_bindonly)
                    except FileNotFoundError:
                        non_binding.append(polymer)
                        print("No binding polymers detected")
                i += 1

            if i == 2:
                st.success("Successfully read from merged datasets.")

                st.info("Please select a polymer to plot from the sidebar.")

                poly_choice = st.sidebar.radio("Please select a polymer to plot.", list_of_polymers)

                mosaic = """
                AA
                BB
                """

                print(poly_choice)

                gs_kw = dict(width_ratios=[1, 1.5], height_ratios=[1, 1.5])

                fig, axd = plt.subplot_mosaic(mosaic, gridspec_kw=gs_kw, figsize=(3.3, 4), constrained_layout=False, dpi=150)

                isBinding = 0

                with st.spinner("graphing polymers"):
                    for polymer in mean_bindonly_list:
                        if poly_choice in polymer:
                            isBinding += 1
                            add_buildup_toax(polymer, axd['A'])
                            axd['A'].set_ylabel("DISCO Effect", fontsize = 6)
                            axd['A'].set_xlabel("Saturation Time (s)", fontisize = 6)
                            axd['A'].axhline(y =0.0, color = "0.8", linestyle = "dashed")
                            axd['A'].xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
                            axd['A'].xaxis.set_ticks(np.arange(0.25, 2.0, 0.25))
                            axd['A'].tick_params(axis = 'x', labelsize = 6)
                            axd['A'].tick_params(axis = 'y', labelsize = 6)

                    for polymer in replicate_bindonly_list:
                        if poly_choice in polymer:
                            isBinding += 1
                            add_fingerprint_toax(polymer, axd['B'])
                            axd['B'].set_ylabel("DISCO AFo", fontsize = 6)
                            axd['B'].set_xlabel("Chemical Shift (Δ ppm)", fontisize = 6)
                            axd['B'].axhline(y =0.0, color = "0.8", linestyle = "dashed")
                            axd['B'].xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
                            axd['B'].xaxis.set_ticks(np.arange(0.25, 2.0, 0.25))
                            axd['B'].tick_params(axis = 'x', labelsize = 6)
                            axd['B'].tick_params(axis = 'y', labelsize = 6)

                    if isBinding >= 2:
                        props = dict(facecolor = "white", linewidth = 0.5)
                        legA = axd['A'].legend(loc = 'upper left', title = "Δ ppm", frameon = True, fontsize = 6, fancybox = False)
                        legA.get_frame().set_edgecolor('k')
                        legA.get_title().set_fontsize('6')
                        legA.get_frame().set_linewidth(0.5)

                        output_filename = f"{output_directory}{poly_choice}.png"
                        plt.tight_layout()
                        fig.patch.set_facecolor('white')
                        fig.savefig(output_filename, dpi = 500, transparent = False)

                        st.image(output_filename, use_column_width = True)

                    elif poly_choice in non_binding:
                        list_of_curves = glob.glob(binding_directory2 + "/*")

                        for curve in list_of_curves:
                            if poly_choice in curve:
                                st.image(curve, use_column_width = True)













    except FileNotFoundError:
        st.warning("You do not have any datafiles to graph!")
