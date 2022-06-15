import pytest
import sys
import os
import re
import glob
import shutil
import matplotlib.pyplot as plt


import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.stats import t
import pingouin as pg

# appending path to access sibling directory - uncomment if local package setup doesn't work
sys.path.append(os.getcwd() + '/../src')

from discoprocess.wrangle_data import *
from matplotlib.testing.compare import compare_images

# global testing directories
path = os.path.dirname(__file__) + "/test-files/test_wrangle_data"
input_path = path + "/input"
expected_path = path + "/expected"

def test_flatten_multicolumns():

    mean_df =  pd.read_excel(input_path + "/stats_analysis_output_mean_" + "CMC_90k_20uM" + ".xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()

    mean_df_ex = pd.read_excel(input_path + "/stats_analysis_output_mean_" + "CMC_90k_20uM" + ".xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()

    colnames = mean_df.columns.get_level_values(0).values
    mean_df = mean_df.droplevel(1, axis=1)
    colnames[4] = "corr_%_attenuation_mean"
    colnames[5] = "corr_%_attenuation_std"
    mean_df.columns = colnames

    mean_df_ex = flatten_multicolumns(mean_df_ex)

    pd.testing.assert_frame_equal(mean_df_ex, mean_df)


def test_calculate_abs_buildup_params():

    mean_df =  pd.read_excel(input_path + "/stats_analysis_output_mean_" + "CMC_90k_20uM" + ".xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()

    colnames = mean_df.columns.get_level_values(0).values
    mean_df = mean_df.droplevel(1, axis=1)
    colnames[4] = "corr_%_attenuation_mean"
    colnames[5] = "corr_%_attenuation_std"
    mean_df.columns = colnames

    actual_1 = mean_df['sat_time'].values
    actual_2 = abs(mean_df['corr_%_attenuation_mean'].values)
    std = abs(mean_df['corr_%_attenuation_std'].values)
    n = mean_df['sample_size'].values
    std_err = std/np.sqrt(n)

    actual_3 = np.subtract(actual_2, std_err)
    actual_4 = np.add(actual_2, std_err)

    expected_1, expected_2, expected_3, expected_4 = calculate_abs_buildup_params(mean_df)

    np.testing.assert_array_equal(actual_1, expected_1)
    np.testing.assert_array_equal(actual_2, expected_2)
    np.testing.assert_array_equal(actual_3, expected_3)
    np.testing.assert_array_equal(actual_4, expected_4)

def test_calculate_buildup_params():

    pass

def test_shapiro_wilk():

    pass

def test_barlett():

    pass

def test_change_significance():

    pass

def test_generate_subset_sattime_df():

    pass

def test_generate_disco_effect_mean_diff_df():

    pass
