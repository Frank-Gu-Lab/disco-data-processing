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
from discoprocess.plotting_helpers import annotate_sig_buildup_points
from discoprocess.wrangle_data import flatten_multicolumns, calculate_abs_buildup_params

from discoprocess.plotting import *
# appending path to access sibling directory - uncomment if local package setup doesn't work
sys.path.append(os.getcwd() + '/../src')

from matplotlib.testing.compare import compare_images

# global testing directories
path = os.path.dirname(__file__) + "/test-files/test_plotting"
input_path = path + "/input"
expected_path = path + "/expected"
