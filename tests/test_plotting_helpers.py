import pytest
import sys
import os
import re
import glob
import shutil
import matplotlib.pyplot as plt

# appending path to access sibling directory - uncomment if local package setup doesn't work
sys.path.append(os.getcwd() + '/../src')

from discoprocess.plotting_helpers import *
from matplotlib.testing.compare import compare_images

# global testing directories
path = os.path.dirname(__file__) + "/test-files/test_plotting_helpers"
input_path = path + "/input"
expected_path = path + "/expected"
