import pytest
import sys
import os
import glob
import shutil
import matplotlib.pyplot as plt

# appending path to access sibling directory - uncomment if local package setup doesn't work
#sys.path.append(os.getcwd() + '/../src')

from discoprocess.data_wrangling_functions import *
from matplotlib.testing.compare import compare_images

# global testing directories
path = "./test-files/test_wrangling"
input_path = path + "/input"
expected_path = path + "/expected"

@pytest.fixture(scope='function')
def remove():
    
    output_dir = path + "/output"
    os.mkdir(output_dir)
    
    yield output_dir
    
    shutil.rmtree(output_dir)

class TestDataFrameConversion:
    """This class contains all the unit tests relating to the dataframe conversion functions, batch_to_dataframe and book_to_dataframe."""
    
    def test_batch_to_dataframe(self, mocker):
    
        b = input_path + "/batch_to_dataframe_input.xlsx"
    
        def mock_initialize_excel_batch_replicates():
            
            unique_polymers = ['CMC', 'CMC_ours', 'HEMAcMPC', 'HPMC E3', 'HPMC E4M', 'PDMA', 'PDMAcd', 'PEGHCO', 'PTA']
            unique_polymer_replicates = [3.0, 1.0, 4.0, 3.0, 3.0, 3.0, 3.0, 1.0, 3.0]
            name_sheets = ['CMC (2)', 'CMC (3)', 'CMC (4)', 'CMC_ours', 'HEMAcMPC (1)', 'HEMAcMPC (2)', 'HEMAcMPC (3)', 'HEMAcMPC (4)', 'HPMC E3', 
                           'HPMC E3 (2)', 'HPMC E3 (3)', 'HPMC E4M', 'HPMC E4M (2)', 'HPMC E4M (3)', 'PDMA (1)', 'PDMA (2)', 'PDMA (3)', 'PDMAcd (1)',
                           'PDMAcd (2)', 'PDMAcd (3)', 'PEGHCO', 'PTA (1)', 'PTA (2)', 'PTA (3)']
            
            return unique_polymers, unique_polymer_replicates, name_sheets
    
        mock1 = mocker.patch("discoprocess.data_wrangling_functions.initialize_excel_batch_replicates", return_value=mock_initialize_excel_batch_replicates())
        mock2 = mocker.patch("discoprocess.data_wrangling_functions.wrangle_batch")
        
        mocks = [mock1, mock2]
        
        batch_to_dataframe(b)
        
        for mock in mocks:
            mock.assert_called_once()
            
        # check that replicate_index was properly created
        actual = mock2.call_args_list[0][0][-1]
        expected = [1, 2, 3, 1, 1, 2, 3, 4, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 1, 2, 3]
        
        assert actual == expected, "Replicate index list was not properly created!"
    
    def test_book_to_dataframe(self, mocker):
        
        b = input_path + "/KHA.xlsx"
        
        def mock_count_sheets():
            
            num_samples = 3
            num_controls = 3
            sample_control_initializer = ['sample', 'sample', 'sample', 'control', 'control', 'control']
            sample_replicate_initializer = [1, 2, 3]
            control_replicate_initializer = [1, 2, 3]
            
            return num_samples, num_controls, sample_control_initializer, sample_replicate_initializer, control_replicate_initializer
        
        mock1 = mocker.patch("discoprocess.data_wrangling_functions.count_sheets", return_value=mock_count_sheets())
        mock2 = mocker.patch("discoprocess.data_wrangling_functions.wrangle_book")
        mock3 = mocker.patch("discoprocess.data_wrangling_functions.clean_book_list", return_value=pd.read_excel(expected_path + "/book_to_dataframe_output.xlsx", index_col=0))
        
        mocks = [mock1, mock2]
        
        actual = book_to_dataframe(b)
        
        for mock in mocks:
            mock.assert_called_once()
        
        expected = ("KHA", pd.read_excel(expected_path + "/book_to_dataframe_output.xlsx", index_col=0))
        
        assert actual[0] == expected[0], "Book name was not properly extracted! Actual: {}, Expected: KHA".format(actual[0])
        pd.testing.assert_frame_equal(actual[1], expected[1])
        
        # total_replicate_index
        actual_index = mock2.call_args_list[0][0][-1]
        expected_index = [1, 2, 3, 1, 2, 3]
        
        assert actual_index == expected_index, "Replicate index list was not properly created!"
            
    # testing assertions for book_to_dataframe
    def test_book_to_dataframe_unequal(self, mocker):
        ''' Checks whether a ValueError is raised when the number of samples and controls do not match. 
        
        Notes
        -----
        Mocker modifies the output for count_sheets from num_controls = 3 to num_controls = 2.
        '''
        
        book = input_path + "/KHA.xlsx"
        
        def return_mock_count():
            
            num_samples = 3
            num_controls = 2
            
            sample_control_initializer = ['sample', 'sample', 'sample', 'control', 'control', 'control']

            sample_replicate_initializer = [1, 2, 3]
            
            control_replicate_initializer = [1, 2, 3]
                    
            return num_samples, num_controls, sample_control_initializer, sample_replicate_initializer, control_replicate_initializer

        mocker.patch("discoprocess.data_wrangling_functions.count_sheets", return_value=return_mock_count())
        
        with pytest.raises(ValueError) as e:
            book_to_dataframe(book)
        
        assert e.match('ERROR: The number of sample sheets is not equal to the number of control sheets in {} please confirm the data in the book is correct.'.format(book))
         
class TestCleanBatch:
    """ This class contains all the unit tests relating to the function test_clean_batch_list. """
    
    def test_clean_the_batch_list(self):
        """ This function recreates the input dataframe list and checks whether the resulting cleaned dataframes match the expected results. 
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-5 and ignores datatype matching.
        """
        
        input_list = glob.glob(input_path + "/clean_batch_input/*")
        
        # recreating input list
        clean_dfs = []
        
        for file in input_list:
            
            name = os.path.basename(file)
            name = name.split(sep=".")
            name = name[0]       
            
            df = pd.read_excel(file, index_col=0)
            
            clean_dfs.append((name, df))
            
        clean_dfs = [clean_dfs]
        
        actual = clean_the_batch_tuple_list(clean_dfs)
        
        output_list = glob.glob(expected_path + "/clean_batch_output/*")
        
        msg1 = "Too many or too few dataframes were cleaned and exported."
        assert len(actual) == len(output_list)
        
        # loop through and check dataframe equality
        for i in range(len(actual)):
            actual_df = actual[i]
            expected_df = pd.read_excel(output_list[i], index_col=0)
            pd.testing.assert_frame_equal(actual_df, expected_df, check_dtype=False)

class TestExport:
    
    def test_export_clean_books(self, remove):
        
        name = 'test'
        df = pd.DataFrame({'a':1, 'b':2}, index=['a','b'])
        output_dir = remove
        
        export_clean_books(name, df, output_dir)
        
        assert os.path.isfile(output_dir + "/" + name + "/" + "test_clean_raw_df.xlsx"), "Exported file could not be found."

class TestAttenuation:
    """This class contains all the unit tests relating to the add_attenuation and add_corr_attenuation functions."""
    
    @pytest.mark.parametrize('path', ['book', 'batch'])
    def test_add_attenuation(self, path, mocker):
        """ Checks for expected attenuation calculations applied for both book and batch paths.
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-5.
        The function attenuation_calc_equality_checker is mocked to return True.
        """
        
        df = pd.read_excel(input_path + "/att_" + path + "_input.xlsx", index_col=0)
           
        mocker.patch("discoprocess.data_wrangling_functions.attenuation_calc_equality_checker", return_value=True)
        
        actual_true, actual_false = add_attenuation(df, path)
        
        expected_true = pd.read_excel(expected_path + "/att_" + path + "_true_output.xlsx", index_col=0)
        expected_false = pd.read_excel(expected_path + "/att_" + path + "_false_output.xlsx", index_col=0)
                
        pd.testing.assert_frame_equal(actual_true, expected_true)
        pd.testing.assert_frame_equal(actual_false, expected_false)
    
    @pytest.mark.parametrize('path', ['book', 'batch'])
    def test_add_corr_attenuation(self, path, mocker):
        """ Checks for expected corrected attenuation calculations applied for both the book and batch paths.
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-5.
        The function corrected_attenuation_calc_equality_checker is mocked to return True.
        """  
        
        df_true = pd.read_excel(input_path + "/corr_att_" + path + "_true_input.xlsx", index_col=0)
        df_false = pd.read_excel(input_path + "/corr_att_" + path + "_false_input.xlsx", index_col=0)
        
        mocker.patch("discoprocess.data_wrangling_functions.corrected_attenuation_calc_equality_checker", return_value=True)
               
        actual = add_corr_attenuation(df_true, df_false, path)
        expected = pd.read_excel(expected_path + "/corr_att_" + path + "_output.xlsx", index_col=0)
        
        pd.testing.assert_frame_equal(actual, expected)

    # testing assertions
    def test_add_attenuation_assertion(self, mocker):
        ''' Checks that a ValueError is raised when the equality checker returns False. '''
        
        df = pd.read_excel(input_path + "/att_book_input.xlsx", index_col=0)
        
        mocker.patch("discoprocess.data_wrangling_functions.attenuation_calc_equality_checker", return_value=False)
        
        with pytest.raises(ValueError) as e:
            add_attenuation(df)
            
        assert e.match("Error, intensity_irrad true and false dataframes are not equal, cannot compute signal attenutation in a one-to-one manner.")

    def test_add_corr_attenuation_assertion(self, mocker):
        ''' Checks that a ValueError is raised when the equality checker returns False. '''
        
        df_true = pd.read_excel(input_path + "/corr_att_book_true_input.xlsx", index_col=0)
        df_false = pd.read_excel(input_path + "/corr_att_book_false_input.xlsx", index_col=0)
        
        mocker.patch("discoprocess.data_wrangling_functions.corrected_attenuation_calc_equality_checker", return_value=False)
        
        with pytest.raises(ValueError) as e:
            add_corr_attenuation(df_true, df_false)
            
        e.match("Error, input dataframes are not equal, cannot compute corrected signal attenutation in a one-to-one manner.")   

class TestPrep:
    """ This class contains all the unit tests relating to the prep functions. """
    
    @pytest.mark.parametrize('path', ['book', 'batch'])
    def test_prep_mean(self, path):
        """ Checks whether an Excel book is prepped for statistical analysis on a "mean" basis.
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-5 and ignores datatype matching.
        """
        
        input_mean = pd.read_excel(input_path + "/prep_mean_" + path + "_input.xlsx", index_col=0)
        
        actual = prep_mean(input_mean, path)
        
        # preserve multi-index when reading in Excel file
        if path == 'book':
            expected_mean_left = pd.read_excel(expected_path + "/prep_mean_book_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
            expected_mean_right = pd.read_excel(expected_path + "/prep_mean_book_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
            expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
            expected = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))
        
        else:
            expected_mean_left = pd.read_excel(expected_path + "/prep_mean_batch_output.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
            expected_mean_right = pd.read_excel(expected_path + "/prep_mean_batch_output.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
            expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
            expected = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))

        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
    
    @pytest.mark.parametrize('path', ['book', 'batch'])
    def test_prep_replicate(self, path):
        """ Checks whether an Excel book is prepped for statistical analysis per replicate.
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-5.
        """

        input_replicate = pd.read_excel(input_path + "/prep_replicate_" + path + "_input.xlsx", index_col=0)
        
        actual = prep_replicate(input_replicate, path)
        
        expected = pd.read_excel(expected_path + "/prep_replicate_" + path + "_output.xlsx", index_col=0)

        pd.testing.assert_frame_equal(actual, expected)
    
class TestT:
    """ This class contains all the unit tests relating to the t-test analysis function. """
    
    def test_t_test(self):
        """ Performa a sample t-test and checks whether the expected results were appended to the inputted dataframe.
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-5. 
        """
        
        # preserve multi-index when reading in Excel file
        df = pd.read_excel(input_path + "/t_test_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        df_other = pd.read_excel(input_path + "/t_test_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        df_other.columns = pd.MultiIndex.from_product([df_other.columns, ['']])
        input_df = pd.merge(df, df_other, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))
        
        actual = t_test(input_df)

        # preserve multi-index when reading in Excel file
        expected_left = pd.read_excel(expected_path + "/t_test_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        expected_right = pd.read_excel(expected_path + "/t_test_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        expected_right.columns = pd.MultiIndex.from_product([expected_right.columns, ['']])
        expected = pd.merge(expected_left, expected_right, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))

        pd.testing.assert_frame_equal(actual, expected)
    
class TestAF:
    """ This class contains all the unit tests relating to the function compute_af. """
    
    def test_compute_af(self):
        """ Checks whether the expected amplication factor was calculated and appended to the dataframe. """
         
        # preserve multi-index when reading in Excel file
        df_mean = pd.read_excel(input_path + "/af_mean_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        df_mean_other = pd.read_excel(input_path + "/af_mean_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        df_mean_other.columns = pd.MultiIndex.from_product([df_mean_other.columns, ['']])
        mean = pd.merge(df_mean, df_mean_other, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))
        
        df_replicate = pd.read_excel(input_path + "/af_replicates_input.xlsx", index_col=0)
        
        actual_mean, actual_replicates = compute_af(mean, df_replicate, 10)
        
        # preserve multi-index when reading in Excel file
        expected_mean_left = pd.read_excel(expected_path + "/af_mean_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        expected_mean_right = pd.read_excel(expected_path + "/af_mean_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
        expected_mean = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))

        expected_replicates = pd.read_excel(expected_path + "/af_replicates_output.xlsx", index_col=0)

        pd.testing.assert_frame_equal(actual_mean, expected_mean, check_exact=True)

        pd.testing.assert_frame_equal(actual_replicates, expected_replicates, check_exact=True)

class TestDropBadPeaks:
    """This class contains all the unit tests relating to the execute_curvefit function."""
    
    def test_drop_bad_peaks_book(self, remove):
        """ Checks whether the expected peaks were dropped and removes any generated files upon teardown. """
        
        # SETUP
        output_dir = remove
        df_title = "KHA"
        
        # Preserve multi-index when reading in Excel file
        df_mean = pd.read_excel(input_path + "/drop_mean_peaks_book_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        df_mean_other = pd.read_excel(input_path + "/drop_mean_peaks_book_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        df_mean_other.columns = pd.MultiIndex.from_product([df_mean_other.columns, ['']])
        mean = pd.merge(df_mean, df_mean_other, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))

        df_replicates = pd.read_excel(input_path + "/drop_replicates_peaks_book_input.xlsx", index_col=0)
        
        actual_mean, actual_replicates = drop_bad_peaks(mean, df_replicates, df_title, output_dir)
        
        # Preserve multi-index when reading in Excel file
        expected_mean_left = pd.read_excel(expected_path + "/drop_mean_peaks_book_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        expected_mean_right = pd.read_excel(expected_path + "/drop_mean_peaks_book_output.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
        expected_mean = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))

        expected_replicates = pd.read_excel(expected_path + "/drop_replicates_peaks_book_output.xlsx", index_col=0)

        pd.testing.assert_frame_equal(actual_mean, expected_mean, check_exact=True)
        
        pd.testing.assert_frame_equal(actual_replicates, expected_replicates, check_exact=True)
        
    def test_drop_bad_peaks_batch(self, remove):     
        
        # SETUP
        output_dir = remove
        
        df_title = "CMC"
        
        # Preserve multi-index when reading in Excel file
        df_mean = pd.read_excel(input_path + "/drop_mean_peaks_batch_input.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
        df_mean_other = pd.read_excel(input_path + "/drop_mean_peaks_batch_input.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
        df_mean_other.columns = pd.MultiIndex.from_product([df_mean_other.columns, ['']])
        mean = pd.merge(df_mean, df_mean_other, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))

        df_replicates = pd.read_excel(input_path + "/drop_replicates_peaks_batch_input.xlsx", index_col=0)
        
        actual_mean, actual_replicates = drop_bad_peaks(mean, df_replicates, df_title, output_dir, 'batch')
        
        # Preserve multi-index when reading in Excel file
        expected_mean_left = pd.read_excel(expected_path + "/drop_mean_peaks_batch_output.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
        expected_mean_right = pd.read_excel(expected_path + "/drop_mean_peaks_batch_output.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
        expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
        expected_mean = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))

        expected_replicates = pd.read_excel(expected_path + "/drop_replicates_peaks_batch_output.xlsx", index_col=0)

        pd.testing.assert_frame_equal(actual_mean, expected_mean, check_exact=True)
        
        pd.testing.assert_frame_equal(actual_replicates, expected_replicates, check_exact=True)

class TestCurveFit:
    """This class contains all the unit tests relating to the execute_curvefit function."""
    
    # can split to check for figures separately from df modification
    def test_execute_curvefit_batch(self, remove, mocker):
        """ Checks for whether the curvefit was executed as expected; batch path. Removes all generated plots during teardown.
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-3.
        """
        
        # SETUP
        output_dir = remove
        df_title = "CMC"
        output_curve = "{}/curve_fit_plots_from_{}".format(output_dir, df_title)
        output_table = "{}/data_tables_from_{}".format(output_dir, df_title)
        
        os.mkdir(output_curve)
        os.mkdir(output_table)
        
        mock1 = mocker.patch("discoprocess.data_wrangling_functions.generate_curvefit_plot")
        
        # Preserve multi-index when reading in Excel file
        df_mean_left = pd.read_excel(input_path + "/batch_curve_mean_input.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
        df_mean_right = pd.read_excel(input_path + "/batch_curve_mean_input.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
        df_mean_right.columns = pd.MultiIndex.from_product([df_mean_right.columns, ['']])
        df_mean = pd.merge(df_mean_left, df_mean_right, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))
                
        df_replicates = pd.read_excel(input_path + "/batch_curve_replicate_input.xlsx", index_col=0)
        # unique protons [3, 4, 5, 8, 9]
        # unique concentrations [9]
        # unique replicates [1, 2, 3]

        actual_mean, actual_replicates = execute_curvefit(df_mean, df_replicates, output_curve, output_table, df_title, 'batch')
                
        # Preserve multi-index when reading in Excel file
        expected_mean_left = pd.read_excel(expected_path + "/batch_curve_mean_output.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
        expected_mean_right = pd.read_excel(expected_path + "/batch_curve_mean_output.xlsx", header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
        expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
        expected_mean = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))

        expected_replicates = pd.read_excel(expected_path + "/batch_curve_replicate_output.xlsx", index_col=0)
    
        pd.testing.assert_frame_equal(df_mean, expected_mean, rtol=1e-3)
        pd.testing.assert_frame_equal(df_replicates, expected_replicates, rtol=1e-3)

        # checking if mocked function was called (mean, rep)
        assert mock1.call_count == 20 # 5 for mean, 15 for rep - no iterations were skipped
        
        for i in range(len(mock1.call_args_list)):
            if i % 4 == 0:
                assert mock1.call_args_list[i][-1]['mean_or_rep'] == 'mean'
            else:
                assert mock1.call_args_list[i][-1]['mean_or_rep'] == 'rep'

        # check if the same tables are generated (can only compare filepath/name)
        actual_table = glob.glob(output_table + "/*")
        expected_table = glob.glob(expected_path + "/data_tables_from_CMC/*")
        
        if len(actual_table) != len(expected_table):
            assert len(actual_table) == len(expected_table)
                
        for i in range(len(actual_table)):
            if "mean" in actual_table[i] and "mean" in expected_table[i]:
                # Preserve multi-index when reading in Excel file
                df_mean = pd.read_excel(actual_table[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
                df_mean_other = pd.read_excel(actual_table[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
                df_mean_other.columns = pd.MultiIndex.from_product([df_mean_other.columns, ['']])
                actual = pd.merge(df_mean, df_mean_other, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))

                # Preserve multi-index when reading in Excel file
                expected_mean_left = pd.read_excel(expected_table[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, :2]
                expected_mean_right = pd.read_excel(expected_table[i], header = [0, 1], index_col=[0, 1, 2, 3]).iloc[:, 2:].droplevel(1, axis=1)
                expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
                expected = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index", "ppm"), right_on=("concentration", "sat_time", "proton_peak_index", "ppm"))
    
                pd.testing.assert_frame_equal(actual, expected, rtol=1e-3)
                        
            elif "replicate" in actual_table[i] and "replicate" in expected_table[i]:
                actual_table[i] = pd.read_excel(actual_table[i], index_col=0)
                expected_table[i] = pd.read_excel(expected_table[i], index_col=0)
            
                pd.testing.assert_frame_equal(actual_table[i], expected_table[i], rtol=1e-3)
                
            else:
                msg4 = "Not all data tables were generated and exported."
                assert False, msg4
    
    def test_execute_curvefit_book(self, remove, mocker):  
        """ Checks for whether the curvefit was executed as expected; book path. Removes all generated plots during teardown.
        
        Notes
        -----
        Equality checking uses a relative tolerance of 1e-3. 
        Simply checks for filepath existence. 
        """
        
        # SETUP
        output_dir = remove
        df_title = "KHA"
        output_curve = "{}/curve_fit_plots_from_{}".format(output_dir, df_title)
        output_table = "{}/data_tables_from_{}".format(output_dir, df_title)
        
        os.mkdir(output_curve)
        os.mkdir(output_table)
        
        mock1 = mocker.patch("discoprocess.data_wrangling_functions.generate_curvefit_plot")
 
        # Preserve multi-index when reading in Excel file
        df_mean = pd.read_excel(input_path + "/book_mean_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        df_mean_other = pd.read_excel(input_path + "/book_mean_input.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        df_mean_other.columns = pd.MultiIndex.from_product([df_mean_other.columns, ['']])
        mean = pd.merge(df_mean, df_mean_other, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))
        
        df_replicates = pd.read_excel(input_path + "/book_replicates_input.xlsx", index_col=0)
        
        actual_mean, actual_replicates = execute_curvefit(mean, df_replicates, output_curve, output_table, df_title)
        
        # Preserve multi-index when reading in Excel file
        expected_mean_left = pd.read_excel(expected_path + "/book_meancurve.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
        expected_mean_right = pd.read_excel(expected_path + "/book_meancurve.xlsx", header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
        expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
        expected_mean = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))

        expected_replicates = pd.read_excel(expected_path + "/book_replicatescurve.xlsx", index_col=0)

        pd.testing.assert_frame_equal(actual_mean, expected_mean, rtol=1e-3)
        pd.testing.assert_frame_equal(actual_replicates, expected_replicates, rtol=1e-3)
        
        # checking if mocked function was called (mean, rep)
        for i in range(len(mock1.call_args_list)):
            print(mock1.call_args_list[i][-1])
        assert mock1.call_count == 35 # some iterations were skipped
        
        # check if the same plots are generated (can only compare filepath/name)
        actual_table = glob.glob(output_table + "/*")
        expected_table = glob.glob(expected_path + "/data_tables_from_KHA/*")
        
        if len(actual_table) != len(expected_table):
            msg2 = "Not all data tables were generated."
            assert len(actual_table) == len(expected_table), msg2

        for i in range(len(actual_table)):
            if "mean" in actual_table[i] and "mean" in expected_table[i]:
                # Preserve multi-index when reading in Excel file
                df_mean = pd.read_excel(actual_table[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
                df_mean_other = pd.read_excel(actual_table[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
                df_mean_other.columns = pd.MultiIndex.from_product([df_mean_other.columns, ['']])
                actual = pd.merge(df_mean, df_mean_other, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))

                # Preserve multi-index when reading in Excel file
                expected_mean_left = pd.read_excel(expected_table[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, :4]
                expected_mean_right = pd.read_excel(expected_table[i], header = [0, 1], index_col=[0, 1, 2]).iloc[:, 4:].droplevel(1, axis=1)
                expected_mean_right.columns = pd.MultiIndex.from_product([expected_mean_right.columns, ['']])
                expected = pd.merge(expected_mean_left, expected_mean_right, left_on=("concentration", "sat_time", "proton_peak_index"), right_on=("concentration", "sat_time", "proton_peak_index"))
    
                pd.testing.assert_frame_equal(actual, expected, rtol=1e-3)
                        
            elif "replicate" in actual_table[i] and "replicate" in expected_table[i]:
                actual_table[i] = pd.read_excel(actual_table[i], index_col=0)
                expected_table[i] = pd.read_excel(expected_table[i], index_col=0)
            
                pd.testing.assert_frame_equal(actual_table[i], expected_table[i], rtol=1e-3)
                
            else:
                msg4 = "Not all data tables were generated and exported."
                assert False, msg4
