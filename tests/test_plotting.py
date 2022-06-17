import pytest
import sys
import os
import re
import glob
import shutil

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import numpy as np

from contextlib import contextmanager

from matplotlib.ticker import FormatStrFormatter

sys.path.append(os.getcwd() + '/../src')

from discoprocess.plotting_helpers import annotate_sig_buildup_points
from discoprocess.wrangle_data import flatten_multicolumns, calculate_abs_buildup_params

from discoprocess.plotting import *

from matplotlib.testing.compare import compare_images

# global testing directories
path = os.path.dirname(__file__) + "/test-files/test_plotting"
input_path = path + "/input"
expected_path = path + "/expected"
output_directory = path + "/output"

#high mw CMC
high_cmc_mean_all = pd.read_excel(input_path + "/stats_analysis_output_mean_all_CMC_131k_20uM.xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()
high_cmc_mean_bindingonly = pd.read_excel(input_path + "/stats_analysis_output_mean_CMC_131k_20uM.xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()
high_cmc_replicate_all = pd.read_excel(input_path + "/stats_analysis_output_replicate_all_CMC_131k_20uM.xlsx", index_col=[0], header=[0]).reset_index(drop=True)
high_cmc_replicate_bindingonly = pd.read_excel(input_path + "/stats_analysis_output_replicate_CMC_131k_20uM.xlsx", index_col=[0], header=[0]).reset_index(drop=True)

#low mw CMC
low_cmc_mean_all = pd.read_excel(input_path + "/stats_analysis_output_mean_all_CMC_90k_20uM.xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()
low_cmc_mean_bindingonly = pd.read_excel(input_path + "/stats_analysis_output_mean_CMC_90k_20uM.xlsx", index_col=[0, 1, 2, 3], header=[0, 1]).reset_index()
low_cmc_replicate_all = pd.read_excel(input_path + "/stats_analysis_output_replicate_all_CMC_90k_20uM.xlsx", index_col=[0], header=[0]).reset_index(drop=True)
low_cmc_replicate_all = pd.read_excel(input_path + "/stats_analysis_output_replicate_CMC_90k_20uM.xlsx", index_col=[0], header=[0]).reset_index(drop=True)


@contextmanager
def assert_plot_added():

    ''' Context manager that checks whether a plot was created (by Matplotlib) by comparing the total number of figures before and after. Referenced from [1].

        References
        ----------
        [1] https://towardsdatascience.com/unit-testing-python-data-visualizations-18e0250430
    '''

    plots_before = plt.gcf().number
    yield
    plots_after = plt.gcf().number
    assert plots_before < plots_after, "Error! Plot was not successfully created."

def test_add_fingerprint_toax():

    with assert_plot_added():

        mosaic = """
        AA
        BB
        """

        gs_kw = dict(width_ratios=[1, 1.5], height_ratios=[1, 1.5])

        fig, axd = plt.subplot_mosaic(mosaic, gridspec_kw=gs_kw, figsize=(3.3, 4), constrained_layout=False, dpi=150)

        add_fingerprint_toax(high_cmc_replicate_bindingonly, axd['B'])
        axd['B'].set_ylabel("DISCO AFo")
        axd['B'].set_xlabel("1H Chemical Shift (Δ ppm)")
        axd['B'].axhline(y =0.0, color = "0.8", linestyle = "dashed")
        axd['B'].yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        axd['B'].tick_params(axis = 'x', labelsize = 6)
        axd['B'].tick_params(axis = 'y', labelsize = 6)


        props = dict(facecolor = "white", linewidth = 0.3)
        output_filename = f"{output_directory}/CMC_131k_20uM_fingerprint.png"
        plt.tight_layout()
        fig.patch.set_facecolor('white')
        fig.savefig(output_filename, dpi = 500, transparent = False)

        expected_filename = f"{expected_path}/CMC_131k_20uM_fingerprint_expected.png"

        assert compare_images(output_filename, expected_filename, tol=0.1) is None
