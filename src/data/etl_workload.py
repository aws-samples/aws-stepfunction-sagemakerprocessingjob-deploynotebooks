import pandas as pd
import numpy as np
import os


class DataProcessor:
    def __init__(self, path_folder = "."):

        self.path_folder = path_folder

        # Path to input
        self.path_input_folder = path_folder
        self.path_input_states = os.path.join(self.path_input_folder,'USStates_Population.csv')

        # Path on which output tables are saved
        self.path_output_folder = path_folder
        self.path_output_states = os.path.join(self.path_output_folder ,'USStates_Population_processed.csv')

        # create dictionaries for read dtypes
        self.read_dtypes_states = {'StateOrTerritory':'category'}

        # create folders for output if not existent yet
        if not os.path.exists(self.path_output_folder):
            os.makedirs(self.path_output_folder) 


    def read_data_from_csv(self):

        self.states = pd.read_csv(self.path_input_states, dtype=self.read_dtypes_states)
        print("Completed Reading States Info from csv file")


    def preprocess_states_data(self, save_preprocess_states=True):

        self.preprocess_states_population_info()
        print("Computed the change in Population from 2010 to 202")
        if save_preprocess_states:
            self.states.to_csv(self.path_output_states, index=False)
            print("New Processed Info is written back")
        return self.states

    def preprocess_states_population_info(self):       
        self.states['Change(Absolute)'] = self.states['Population_2020']-self.states['Population_2010']


def main():

    datapreprocesssor = DataProcessor()
    datapreprocesssor.read_data_from_csv()
    datapreprocesssor.preprocess_states_data()
    print('ETL has been successfully completed !!')

if __name__ == '__main__':
    main()

