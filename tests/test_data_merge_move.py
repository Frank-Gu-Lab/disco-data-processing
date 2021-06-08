import pytest
import sys
import os
import shutil
import glob
import pandas as pd

# appending path to access sibling directory
sys.path.append(os.getcwd() + '\\..\\src')

from data_merging import *

class TestMove:
    """This class contains all the unit tests relating to the move function."""
    
    def test_move(self):
        """Testing overall functionality, this function takes files from src_path and moves them to dst_path. The function then asserts whether
        the files exist in dst_path, subsequently removing the files as part of teardown."""
        
        # SETUP
        src_path = ".\\test-files\\test_move\\*"
        dst_path = ".\\test-files\\output"
        
        # grab file names from src
        directories = glob.glob(src_path)
        filenames = [glob.glob("{}/*".format(dir)) for dir in directories] # list of lists, each inner list represents files in a directory
        
        os.mkdir(dst_path)

        try:
            
            move(src_path, dst_path)
            
            for i in range(len(filenames)):
                for file in filenames[i]: # file = absolute path
                    filename = os.path.basename(file)
                    msg = "{} could not be found in {}!".format(filename, dst_path)
                    assert os.path.isfile(dst_path + "\\" + filename), msg
            
        finally:
            
            # TEARDOWN
            shutil.rmtree(dst_path)

class TestClean:
    """ This class contains all unit tests relating to the clean function. """

    def test_clean_pos(self):
        
        # recreate input list
        path = "./test-files/test_merge"
        
        dfs = glob.glob(path + "/input/clean_pos_input/*")
        
        for i in range(len(dfs)):
            
            try: # ppm in index
                # Preserve multi-index when reading in Excel file
                df = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
                df_other = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
                df_other.columns = pd.MultiIndex.from_product([df_other.columns, ['']])
                dfs[i] = pd.merge(df, df_other, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))
        
            except: # ppm in column
                # Preserve multi-index when reading in Excel file
                df = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
                df_other = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
                df_other.columns = pd.MultiIndex.from_product([df_other.columns, ['']])
                dfs[i] = pd.merge(df, df_other, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))
        
        polymer_list = open(path + "/input/clean_pos_polymer.txt").readlines()
        polymer_list = [l.rstrip() for l in polymer_list]
        
        # call function --> original list is modified (mutable)
        clean(dfs, polymer_list, True)        
        
        # recreate output list
        expected_dfspaths = glob.glob(path + "/expected/clean_pos_output/*")
        expected_dfs = [pd.read_excel(df, index_col=[0, 1, 2, 3]) for df in expected_dfspaths]
        
        for i in range(len(expected_dfs)):
            if None in expected_dfs[i].index.names:
                expected_dfs[i] = pd.read_excel(expected_dfspaths[i], index_col=[0, 1, 2])
                expected_dfs[i] = expected_dfs[i].iloc[:, 1:] # removing extra column
        
        # compare
        assert len(dfs) == len(expected_dfs)

        for i in range(len(dfs)):
            pd.testing.assert_frame_equal(dfs[i], expected_dfs[i])
    
    @pytest.mark.xfail
    def test_clean_neg(self):

        # recreate input list
        path = "./test-files/test_merge"
        
        dfs = sorted(glob.glob(path + "/input/clean_neg_input/*"), key=lambda x : int(os.path.basename(x)[6:-5]))
        
        for i in range(len(dfs)):
            
            try: # ppm in index
                # Preserve multi-index when reading in Excel file
                df = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
                df_other = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
                df_other.columns = pd.MultiIndex.from_product([df_other.columns, ['']])
                dfs[i] = pd.merge(df, df_other, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))
        
            except: # ppm in column
                # Preserve multi-index when reading in Excel file
                df = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
                df_other = pd.read_excel(dfs[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
                df_other.columns = pd.MultiIndex.from_product([df_other.columns, ['']])
                dfs[i] = pd.merge(df, df_other, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))
        
        polymer_list = open(path + "/input/clean_neg_polymer.txt").readlines()
        polymer_list = [l.rstrip() for l in polymer_list]
        
        # call function --> original list is modified (mutable)
        clean(dfs, polymer_list, False)        
        
        # recreate output list
        expected_dfspaths = sorted(glob.glob(path + "/expected/clean_neg_output/*"), key=lambda x : int(os.path.basename(x)[6:-5]))
        expected_dfs = [pd.read_excel(df, index_col=[0, 1, 2, 3]) for df in expected_dfspaths]
        
        for i in range(len(expected_dfs)):
            if None in expected_dfs[i].index.names:
                expected_dfs[i] = pd.read_excel(expected_dfspaths[i], index_col=[0, 1, 2])
                expected_dfs[i] = expected_dfs[i].iloc[:, 1:] # removing extra column
        
        # compare
        assert len(dfs) == len(expected_dfs)
        
        for i in range(len(dfs)):
            pd.testing.assert_frame_equal(dfs[i], expected_dfs[i])

class TestReformat:

    def test_reformat_pos(self):
        
        path = "./test-files/test_merge"
        
        # recreating input list
        df_list = glob.glob(path + "/input/reformat_pos_input/*")
        df_list = [pd.read_excel(df, index_col=[0, 1, 2, 3]) for df in df_list]
        
        actual = reformat(df_list, True)
        
        expected = pd.read_excel(path + "/expected/reformat_pos_output.xlsx", index_col=0)
        
        assert actual.equals(expected)
        
    def test_reformat_neg(self):  

        path = "./test-files/test_merge"
        
        # recreating input list
        df_list = sorted(glob.glob(path + "/input/reformat_neg_input/*"), key=lambda x : int(os.path.basename(x)[6:-5]))
        df_list = [pd.read_excel(df, index_col=[0, 1, 2, 3]) for df in df_list]

        actual = reformat(df_list, False)

        expected = pd.read_excel(path + "/expected/reformat_neg_output.xlsx", index_col=0)
        expected.columns.name = 'index' # column.name attribute not saved when exported to Excel file

        assert actual.equals(expected)
        
class TestJoin:
    
    def test_join(self):
        """ Takes in two dataframes and joins them together. 
        
        Notes
        -----
        Equality checking ignores datatype matching.
        """
        
        path = "./test-files/test_merge"
        
        df1 = pd.read_excel(path + "/input/join_input1.xlsx", index_col=0)
        df2 = pd.read_excel(path + "/input/join_input2.xlsx", index_col=0)
        
        actual = join(df1, df2)
        
        expected = pd.read_excel(path + "/expected/join_output.xlsx", index_col=0)

        pd.testing.assert_frame_equal(actual, expected, check_exact=True, check_dtype=False)
        
class TestMerge:
    """This class contains all the unit tests relating to the merge function."""
    
    def test_merge_book(self):
        """Testing overall functionality. Takes all Excel sheets from src_path and moves to dst_path, from which the function concatenates all 
        sheets together into one Dataframe.
        
        Notes
        -----
        Equality checking ignores datatype matching.
        """
        
        #SETUP
        path = "./test-files/test_merge"
        src_path = path + "/input/KHA/data_tables_from_KHA"
        dst_path = path + "/output"

        os.mkdir(dst_path)

        try:

            actual = merge(src_path, dst_path)
            
            expected = pd.read_excel(path + "/expected/merged_binding_dataset.xlsx", index_col=0)
            expected.columns.name = 'index' # column.name attribute not saved when exported to Excel file

            pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=True)
        
        finally:
            
            # TEARDOWN
            shutil.rmtree(dst_path)
        
    def test_merge_batch(self):
        """Testing overall functionality. Takes all Excel sheets from src_path and moves to dst_path, from which the function concatenates all 
        sheets together into one Dataframe.
        
        Notes
        -----
        Equality checking ignores datatype matching.
        """
        
        #SETUP
        path = "./test-files/test_merge"
        src_path = path + "/input/merge_batch/*/data_tables_from_*"
        dst_path = path + "/output"

        os.mkdir(dst_path)

        try:

            actual = merge(src_path, dst_path)

            expected = pd.read_excel(path + "/expected/merge_batch_output.xlsx", index_col=0)
            expected.columns.name = 'index' # column.name attribute not saved when exported to Excel file

            pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=True)
        
        finally:
            
            # TEARDOWN
            shutil.rmtree(dst_path)  
        
            