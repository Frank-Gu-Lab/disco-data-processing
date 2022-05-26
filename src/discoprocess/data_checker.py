# define functions used in data cleaning
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import t
import scipy.stats as stats
from scipy.optimize import curve_fit
import os
import glob

# import helpers
try:
    from data_wrangling_helpers import *
    from data_plot import *
except:
    from .data_wrangling_helpers import *
    from .data_plot import *

def name_checker(list_of_raw_books):
    '''
        This function checks to ensure that the polymer naming is consistent across input files and returns a descriptive error
        message for inconsistent naming

        Input:

            List of all raw books to be used for the data PROCESSING

        Output:

            Will return 1 if all data is input correctly, raise an error otherwise.
    '''

    for book in list_of_raw_books:

        unique_polymers, unique_polymer_replicates, name_sheets = initialize_excel_batch_replicates(book)

        for name in unique_polymers:

            list_of_name_parts = name.split("_")

            if list_of_name_parts[1][-1] != 'k':
                raise Exception("Please add a 'k' to the end of the molecular weight (for kilodaltons) for each polymer name")
                return 0
            if list_of_name_parts[2][-2:] != 'uM':
                raise Exception("Please add 'uM' to the end of the concentration in the polymer name")
                return 0
            if len(list_of_name_parts) != 3:
                raise Exception("Please format the name in the form: CMC_90k_20uM")
                return 0

    return 1
