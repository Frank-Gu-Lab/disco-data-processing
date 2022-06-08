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
