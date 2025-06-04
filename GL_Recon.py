# Import Libraries
import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog

# select the file
def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename()
    return file_path

#1.	The process should be system agnostic by taking in excel data
#4.	The process should be able to compare either 2 files or 3 files in the event that we want to match legacy to pre-load to post-load files
# Function to get file paths from user
def get_file_paths():
    # Get the file paths from the user
    print("Select the first file to compare:")
    file1 = select_file()
    # check if file exists
    #while not os.path.exists(file1):
    #    print("File does not exist. Please try again.")
    #    file1 = input("Enter the path of the legacy file to compare: ")

    print("Select the path of the second file to compare: ")
    file2 = select_file()
    # check if file exists
    #while not os.path.exists(file2):
    #    print("File does not exist. Please try again.")
    #    file2 = input("Enter the path of the converted file to compare: ")
    
    print("Select the thrid file, if there is no file then please hit cancel: ")
    file3 = select_file()
    
    # check if file exists
    #while file3 and not os.path.exists(file3):
        #print("File does not exist. Please try again.")
        #file3 = input("Enter the path of the third file to compare (optional, press Enter to skip): ").strip()
    
    # if file 3 is blank then set to None
    if not file3:
        file3 = None

    return file1, file2, file3 if file3 else None

# Function to read the contents of the files
def read_files(file1, file2,file3):
    try:
        content1 = pd.read_excel(file1)
        print("Extracted data from First file")
        content2 = pd.read_excel(file2)
        print("Extracted data from Second file")
        content3 = None
        if file3 is not None:
            content3 = pd.read_excel(file3)
            print("Extracted data from Third file")

        return content1, content2, content3
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None
    
#2.	The process should produce an output report showing each record, whether it matched or not and the $ and % variances.
#3.	The process should give the end-user the flexibility to pick which columns they want to summarize for comparison 
# (i.e. Client A might want to reconcile just at the business unit and account level, but Client B might want to reconcile at the business unit, account, and location level).
#7.	The column to be summarized should be selected as an input as well.
def compare_files(content1, content2,content3):
    if content1 is not None and content2 is not None:
        # Check if the third file is provided
        if content3 is not None:
            x_third_file = "yes"
        else:
            x_third_file = "no"

        # Compare the contents of the files
        comparison_result = content1.equals(content2)
        comparison_result2 = content2.equals(content3)

        if comparison_result and ((x_third_file == "yes" and comparison_result2) or x_third_file == "no"):
            print("The files are identical.")
            # Ask the user if they want to compare the files anyway
            compare_anyway = input("Do you want to compare the files anyway? (yes/no): ").strip().lower()
        
        if not comparison_result or (x_third_file == "yes" and not comparison_result2) or (compare_anyway == 'yes'):
            # only compare the first two files
            if x_third_file == "no" or comparison_result2:
                print("The files are different.")
                
                # Ask the user for the primary key columns and the column to match against
                columns = list(content1.columns)
                print("Select the primary key columns (First File) (comma-separated numbers):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                primary_key_columns_leg_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                primary_key_columns_leg = [columns[int(index) - 1] for index in primary_key_columns_leg_indices]

                # Check if the primary key columns are valid
                while not all(col in content1.columns for col in primary_key_columns_leg):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_leg_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                    primary_key_columns_leg = [columns[int(index) - 1] for index in primary_key_columns_leg_indices]

                columns = list(content2.columns)
                print("Select the primary key columns (Second File) (comma-separated numbers):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                primary_key_columns_conv_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                primary_key_columns_conv = [columns[int(index) - 1] for index in primary_key_columns_conv_indices]

                # Check if the primary key columns are valid
                while not all(col in content2.columns for col in primary_key_columns_conv):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_conv_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                    primary_key_columns_conv = [columns[int(index) - 1] for index in primary_key_columns_conv_indices]

                # Ask the user for the column to match against
                columns = list(content1.columns)
                print("Select the column to match against (First File):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                match_column_leg_index = int(input("Enter the number corresponding to the column: ")) - 1
                match_column_leg = columns[match_column_leg_index]

                while not match_column_leg in content1.columns:
                    print("The match column is not valid. Please try again.")
                    match_column_leg_index = int(input("Enter the number corresponding to the column: ")) - 1
                    match_column_leg = columns[match_column_leg_index]
                
                columns = list(content2.columns)
                print("Select the column to match against (Second File):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                match_column_conv_index = int(input("Enter the number corresponding to the column: ")) - 1
                match_column_conv = columns[match_column_conv_index]

                while not match_column_conv in content2.columns:
                    print("The match column is not valid. Please try again.")
                    match_column_conv_index = int(input("Enter the number corresponding to the column: ")) - 1
                    match_column_conv = columns[match_column_conv_index]
                
                '''
                columns = list(content1.columns)
                print("Select the column to match against (First File):")
                for i, col in enumerate(columns):
                    print(f"{chr(65 + i)}. {col}")
                match_column_leg = input("Enter the letter corresponding to the column: ").strip().upper()
                match_column_leg = columns[ord(match_column_leg) - 65]



                columns = list(content2.columns)
                print("Select the column to match against (Second File):")
                for i, col in enumerate(columns):
                    print(f"{chr(65 + i)}. {col}")
                match_column_conv = input("Enter the letter corresponding to the column: ").strip().upper()
                match_column_conv = columns[ord(match_column_conv) - 65]
                '''
                '''
                primary_key_columns_leg = input("Enter the primary key column names (First File) for (comma-separated): ").split(',')

                # Check if the primary key columns are valid
                while not all(col in content1.columns for col in primary_key_columns_leg):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_leg = input("Enter the primary key column names (First File) for (comma-separated): ").split(',')

                # Ask the user for the primary key columns and the column to match against
                primary_key_columns_conv = input("Enter the primary key column names (Second File) for (comma-separated): ").split(',')

                # Check if the primary key columns are valid
                while not all(col in content2.columns for col in primary_key_columns_conv):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_conv = input("Enter the primary key column names (Second File) for (comma-separated): ").split(',')

                match_column_leg = input("Enter the column name to match against (First File): ")

                # Check if the match column is valid
                while match_column_leg not in content1.columns:
                    print("The match column name is not valid. Please try again.")
                    match_column_leg = input("Enter the column name to match against (First File): ")

                match_column_conv = input("Enter the column name to match against (Second File): ")

                # Check if the match column is valid
                while match_column_conv not in content2.columns:
                    print("The match column name is not valid. Please try again.")
                    match_column_conv = input("Enter the column name to match against (Second File): ")
                '''
                
                ##5.	The process should allow for the end-user to input a tolerance for an accepted match. 
                # (ex. if difference is within a certain dollar ammount or % which would be considered a match, this is optional)
                tolerance = input("Do you want to input a tolerance for an accepted match? (yes/no): ").strip().lower()

                # Check if the tolerance is valid
                while tolerance not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    tolerance = input("Do you want to input a tolerance for an accepted match? (yes/no): ").strip().lower()

                type_tolerance = None
                tolerance_value = None
                if tolerance == 'yes':
                    type_tolerance = input("Enter the type of tolerance ($ or %): ").strip().lower()
                    # Check if the type of tolerance is valid
                    while type_tolerance not in ['$', '%']:
                        print("Invalid input. Please enter '$' or '%'.")
                        type_tolerance = input("Enter the type of tolerance ($ or %): ").strip().lower()

                    tolerance_value = float(input("Enter the tolerance value: "))
                    # Check if the tolerance value is valid
                    while tolerance_value < 0:
                        print("Invalid input. Please enter a positive number.")
                        tolerance_value = float(input("Enter the tolerance value: "))

                # Check if primary key columns have unique values
                #if (content1.groupby(primary_key_columns_leg).size().reset_index(name='count').shape[0] != content1.shape[0]) or (content2.groupby(primary_key_columns_conv).size().reset_index(name='count').shape[0] != content2.shape[0]):
                #    print("Primary key columns do not have unique values in the files. Recommended to use distinct list based on the primary key and the column being used to match summed up together.")


                # Ask the user if they want the column to be a distinct list based on the primary key and t he column being used to match summed up together
                distinct_list = 'yes' #input("Do you want the column to be a distinct list based on the primary key and the column being used to match summed up together? (yes/no): ").strip().lower()
                
                # Check if the distinct list is valid
                while distinct_list not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    distinct_list = input("Do you want the column to be a distinct list based on the primary key and the column being used to match summed up together? (yes/no): ").strip().lower()

                if distinct_list == 'yes':
                    # Group by primary key columns and sum the match column
                    content1 = content1.groupby(primary_key_columns_leg)[match_column_leg].sum().reset_index()
                    content2 = content2.groupby(primary_key_columns_conv)[match_column_conv].sum().reset_index()

                # Merge the dataframes on the primary key columns
                merged_df = pd.merge(content1, content2, left_on=primary_key_columns_leg, right_on=primary_key_columns_conv, suffixes=('_legacy', '_converted'))

                # Create a column with the differences
                if tolerance == 'yes':
                    if type_tolerance == '$':
                        merged_df['Difference'] = merged_df.apply(lambda row: abs(row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"]) > tolerance_value, axis=1)
                        merged_df['Dollar Difference'] = merged_df.apply(lambda row: row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"], axis=1)
                        merged_df['Percentage Difference'] = merged_df.apply(lambda row: abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"])) / abs(row[f"{match_column_leg}_legacy"]) * 100 if row[f"{match_column_leg}_legacy"] != 0 else None, axis=1)
                    elif type_tolerance == '%':
                        merged_df['Difference'] = merged_df.apply(lambda row: abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"]) / row[f"{match_column_leg}_legacy"]) > tolerance_value if row[f"{match_column_leg}_legacy"] != 0 else abs(row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"]) > tolerance_value, axis=1)
                        merged_df['Dollar Difference'] = merged_df.apply(lambda row: row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"], axis=1)
                        merged_df['Percentage Difference'] = merged_df.apply(lambda row: abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"])) / abs(row[f"{match_column_leg}_legacy"]) * 100 if row[f"{match_column_leg}_legacy"] != 0 else None, axis=1)
                else:
                    merged_df['Difference'] = merged_df.apply(lambda row: row[f"{match_column_leg}_legacy"] != row[f"{match_column_conv}_converted"], axis=1)
                    merged_df['Dollar Difference'] = merged_df.apply(lambda row: row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"], axis=1)
                    merged_df['Percentage Difference'] = merged_df.apply(lambda row: abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"])) / abs(row[f"{match_column_leg}_legacy"]) * 100 if row[f"{match_column_leg}_legacy"] != 0 else None, axis=1)

                # Print the summary
                total_records = len(merged_df)
                matched_records = len(merged_df[~merged_df['Difference']])
                matched_percentage = (matched_records / total_records) * 100

                # Ask if the column name for the primary key needs to be changed in the output file
                change_primary_key_name = input("Do you want to change the primary key column names in the output file? (yes/no): ").strip().lower()

                # Check if the input is valid
                while change_primary_key_name not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    change_primary_key_name = input("Do you want to change the primary key column names in the output file? (yes/no): ").strip().lower()

                if change_primary_key_name == 'yes':
                    new_primary_key_names = input("Enter the new primary key column names (comma-separated): ").split(',')
                    if len(new_primary_key_names) == len(primary_key_columns_leg):
                        for old_name, new_name in zip(primary_key_columns_leg, new_primary_key_names):
                            merged_df.rename(columns={old_name: new_name}, inplace=True)
                    else:
                        print("The number of new primary key column names does not match the number of primary key columns. Skipping renaming.")

                # Ask if the column name for the match key needs to be changed in the output file for the legacy file
                change_match_key_names_legacy = input("Do you want to update the match key column name for the first file in the output file? (yes/no): ").strip().lower()

                # Check if the input is valid
                while change_match_key_names_legacy not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    change_match_key_names_legacy = input("Do you want to update the match key column name for the first file in the output file? (yes/no): ").strip().lower()
                
                if change_match_key_names_legacy == 'yes':
                    new_match_key_names_legacy = input("Enter the new match key column name for the first file: ").strip()
                    if new_match_key_names_legacy:
                        merged_df.rename(columns={f"{match_column_leg}_legacy": new_match_key_names_legacy}, inplace=True)
                    else:
                        print("No new match key column name provided. Skipping renaming.")
                
                # Ask if the column name for the match key needs to be changed in the output file for the converted file
                change_match_key_names_converted = input("Do you want to update the match key column name for the second file in the output file? (yes/no): ").strip().lower()

                # Check if the input is valid
                while change_match_key_names_converted not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    change_match_key_names_converted = input("Do you want to update the match key column name for the second file in the output file? (yes/no): ").strip().lower()
                
                if change_match_key_names_converted == 'yes':
                    new_match_key_names_converted = input("Enter the new match key column name for the second file: ").strip()
                    if new_match_key_names_converted:
                        merged_df.rename(columns={f"{match_column_conv}_converted": new_match_key_names_converted}, inplace=True)
                    else:
                        print("No new match key column name provided. Skipping renaming.")

                # Print the rows with differences
                differences = merged_df[merged_df['Difference']]
                if not differences.empty:
                    print("Differences found:")
                    print(differences)
                    print(f"Total records: {total_records}")
                    print(f"Matched records: {matched_records} ({matched_percentage:.2f}%)")
                    # Write the output to a new file
                    output_file = "Output.xlsx"
                    writer = pd.ExcelWriter(output_file)
                    #differences.to_excel(writer, index=False)
                    merged_df.to_excel(writer, index=False)
                    writer._save()
                    print(f"Output written to {output_file}")
                else:
                    print("No differences found in the specified column.")
            else:
                print("The files are different.")

                # Ask the user for the primary key columns and the column to match against
                columns = list(content1.columns)
                print("Select the primary key columns (First File) (comma-separated numbers):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                primary_key_columns_leg_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                primary_key_columns_leg = [columns[int(index) - 1] for index in primary_key_columns_leg_indices]

                # Check if the primary key columns are valid
                while not all(col in content1.columns for col in primary_key_columns_leg):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_leg_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                    primary_key_columns_leg = [columns[int(index) - 1] for index in primary_key_columns_leg_indices]

                columns = list(content2.columns)
                print("Select the primary key columns (Second File) (comma-separated numbers):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                primary_key_columns_conv_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                primary_key_columns_conv = [columns[int(index) - 1] for index in primary_key_columns_conv_indices]

                # Check if the primary key columns are valid
                while not all(col in content2.columns for col in primary_key_columns_conv):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_conv_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                    primary_key_columns_conv = [columns[int(index) - 1] for index in primary_key_columns_conv_indices]

                # Ask the user for the column to match against
                columns = list(content1.columns)
                print("Select the column to match against (First File):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                match_column_leg_index = int(input("Enter the number corresponding to the column: ")) - 1
                match_column_leg = columns[match_column_leg_index]

                while not match_column_leg in content1.columns:
                    print("The match column is not valid. Please try again.")
                    match_column_leg_index = int(input("Enter the number corresponding to the column: ")) - 1
                    match_column_leg = columns[match_column_leg_index]
                
                columns = list(content2.columns)
                print("Select the column to match against (Second File):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                match_column_conv_index = int(input("Enter the number corresponding to the column: ")) - 1
                match_column_conv = columns[match_column_conv_index]

                while not match_column_conv in content2.columns:
                    print("The match column is not valid. Please try again.")
                    match_column_conv_index = int(input("Enter the number corresponding to the column: ")) - 1
                    match_column_conv = columns[match_column_conv_index]
                
                columns = list(content3.columns)
                print("Select the primary key columns (Third File) (comma-separated numbers):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                primary_key_columns_loaded_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                primary_key_columns_loaded = [columns[int(index) - 1] for index in primary_key_columns_loaded_indices]

                # Check if the primary key columns are valid
                while not all(col in content3.columns for col in primary_key_columns_loaded):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_loaded_indices = input("Enter the numbers corresponding to the columns (comma-separated numbers): ").split(',')
                    primary_key_columns_loaded = [columns[int(index) - 1] for index in primary_key_columns_loaded_indices]

                print("Select the column to match against (Third File):")
                for i, col in enumerate(columns):
                    print(f"{i + 1}. {col}")
                match_column_loaded_index = int(input("Enter the number corresponding to the column: ")) - 1
                match_column_loaded = columns[match_column_loaded_index]

                while not match_column_loaded in content3.columns:
                    print("The match column is not valid. Please try again.")
                    match_column_loaded_index = int(input("Enter the number corresponding to the column: ")) - 1
                    match_column_loaded = columns[match_column_loaded_index]

                '''
                # Ask the user for the primary key columns and the column to match against
                primary_key_columns_leg = input("Enter the primary key column names (First File) for (comma-separated): ").split(',')

                # Check if the primary key columns are valid
                while not all(col in content1.columns for col in primary_key_columns_leg):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_leg = input("Enter the primary key column names (First File) for (comma-separated): ").split(',')

                # Ask the user for the primary key columns and the column to match against
                primary_key_columns_conv = input("Enter the primary key column names (Second File) for (comma-separated): ").split(',')

                # Check if the primary key columns are valid
                while not all(col in content2.columns for col in primary_key_columns_conv):
                    print("One or more primary key columns are not valid. Please try again.")
                    primary_key_columns_conv = input("Enter the primary key column names (Second File) for (comma-separated): ").split(',')

                match_column_leg = input("Enter the column name to match against (First File): ")

                # Check if the match column is valid
                while match_column_leg not in content1.columns:
                    print("The match column is not valid. Please try again.")
                    match_column_leg = input("Enter the column name to match against (First File): ")

                match_column_conv = input("Enter the column name to match against (Second File): ")

                # Check if the match column is valid
                while match_column_conv not in content2.columns:
                    print("The match column is not valid. Please try again.")
                    match_column_conv = input("Enter the column name to match against (Second File): ")

                if x_third_file == "yes":
                    primary_key_columns_loaded = input("Enter the primary key column names (Third File) for (comma-separated): ").split(',')

                    # Check if the primary key columns are valid
                    while not all(col in content3.columns for col in primary_key_columns_loaded):
                        print("One or more primary key column names are not valid. Please try again.")
                        primary_key_columns_loaded = input("Enter the primary key column names (Third File) for (comma-separated): ").split(',')

                    match_column_loaded = input("Enter the column name to match against (Third File): ")

                    # Check if the match column is valid
                    while match_column_loaded not in content3.columns:
                        print("The match column name is not valid. Please try again.")
                        match_column_loaded = input("Enter the column name to match against (Third File): ")
                '''

                ##5. The process should allow for the end-user to input a tolerance for an accepted match. 
                # (ex. if difference is within a certain dollar amount or % which would be considered a match, this is optional)
                tolerance = input("Do you want to input a tolerance for an accepted match? (yes/no): ").strip().lower()

                # Check if the tolerance is valid
                while tolerance not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    tolerance = input("Do you want to input a tolerance for an accepted match? (yes/no): ").strip().lower()

                type_tolerance = None
                tolerance_value = None
                if tolerance == 'yes':
                    type_tolerance = input("Enter the type of tolerance ($ or %): ").strip().lower()
                    # Check if the type of tolerance is valid
                    while type_tolerance not in ['$', '%']:
                        print("Invalid input. Please enter '$' or '%'.")
                        type_tolerance = input("Enter the type of tolerance ($ or %): ").strip().lower()

                    tolerance_value = float(input("Enter the tolerance value: "))
                    # Check if the tolerance value is valid
                    while tolerance_value < 0:
                        print("Invalid input. Please enter a positive number.")
                        tolerance_value = float(input("Enter the tolerance value: "))

                # Ask the user if they want the column to be a distinct list based on the primary key and the column being used to match summed up together
                distinct_list = 'yes' #input("Do you want the column to be a distinct list based on the primary key and the column being used to match summed up together? (yes/no): ").strip().lower()
                    
                # Check if the distinct list is valid
                while distinct_list not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    distinct_list = input("Do you want the column to be a distinct list based on the primary key and the column being used to match summed up together? (yes/no): ").strip().lower()

                if distinct_list == 'yes':
                    # Group by primary key columns and sum the match column
                    content1 = content1.groupby(primary_key_columns_leg)[match_column_leg].sum().reset_index()
                    content2 = content2.groupby(primary_key_columns_conv)[match_column_conv].sum().reset_index()
                    if content3 is not None:
                        content3 = content3.groupby(primary_key_columns_loaded)[match_column_loaded].sum().reset_index()

                # Merge the dataframes on the primary key columns
                merged_df = pd.merge(content1, content2, left_on=primary_key_columns_leg, right_on=primary_key_columns_conv, suffixes=('_legacy', '_converted'))
                if content3 is not None:
                    merged_df = pd.merge(merged_df, content3, left_on=primary_key_columns_conv, right_on=primary_key_columns_loaded, suffixes=('', '_loaded'))
                
                # Create a column with the differences
                if tolerance == 'yes':
                    if type_tolerance == '$':
                        merged_df['Difference'] = merged_df.apply(
                            lambda row: abs(row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"]) > tolerance_value or 
                                        (content3 is not None and abs(row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"]) > tolerance_value), axis=1)
                        merged_df['Dollar Difference (First Vs Second)'] = merged_df.apply(
                            lambda row: row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"], axis=1)
                        merged_df['Percentage Difference (First Vs Second)'] = merged_df.apply(
                            lambda row: abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"])) / abs(row[f"{match_column_leg}_legacy"]) * 100 if row[f"{match_column_leg}_legacy"] != 0 else None, axis=1)
                        if content3 is not None:
                            merged_df['Dollar Difference (Second Vs Third)'] = merged_df.apply(
                                lambda row: row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"], axis=1)
                            merged_df['Percentage Difference (Second Vs Third)'] = merged_df.apply(
                                lambda row: abs((row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"])) / abs(row[f"{match_column_conv}_converted"]) * 100 if row[f"{match_column_conv}_converted"] != 0 else None, axis=1)
                    elif type_tolerance == '%':
                        merged_df['Difference'] = merged_df.apply(
                            lambda row: (abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"]) / row[f"{match_column_leg}_legacy"]) > tolerance_value if row[f"{match_column_leg}_legacy"] != 0 else abs(row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"]) > tolerance_value) or 
                                        (content3 is not None and (abs((row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"]) / row[f"{match_column_conv}_converted"]) > tolerance_value if row[f"{match_column_conv}_converted"] != 0 else abs(row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"]) > tolerance_value)), axis=1)
                        merged_df['Dollar Difference (First Vs Second)'] = merged_df.apply(
                            lambda row: row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"], axis=1)
                        merged_df['Percentage Difference (First Vs Second)'] = merged_df.apply(
                            lambda row: abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"])) / abs(row[f"{match_column_leg}_legacy"]) * 100 if row[f"{match_column_leg}_legacy"] != 0 else None, axis=1)
                        if content3 is not None:
                            merged_df['Dollar Difference (Second Vs Third)'] = merged_df.apply(
                                lambda row: row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"], axis=1)
                            merged_df['Percentage Difference (Second Vs Third)'] = merged_df.apply(
                                lambda row: abs((row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"])) / abs(row[f"{match_column_conv}_converted"]) * 100 if row[f"{match_column_conv}_converted"] != 0 else None, axis=1)
                else:
                    merged_df['Difference'] = merged_df.apply(
                        lambda row: row[f"{match_column_leg}_legacy"] != row[f"{match_column_conv}_converted"] or 
                                    (content3 is not None and row[f"{match_column_conv}_converted"] != row[f"{match_column_loaded}"]), axis=1)
                    merged_df['Dollar Difference (First Vs Second)'] = merged_df.apply(
                        lambda row: row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"], axis=1)
                    merged_df['Percentage Difference (First Vs Second)'] = merged_df.apply(
                        lambda row: abs((row[f"{match_column_leg}_legacy"] - row[f"{match_column_conv}_converted"])) / abs(row[f"{match_column_leg}_legacy"]) * 100 if row[f"{match_column_leg}_legacy"] != 0 else None, axis=1)
                    if content3 is not None:
                        merged_df['Dollar Difference (Second Vs Third)'] = merged_df.apply(
                            lambda row: row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"], axis=1)
                        merged_df['Percentage Difference (Second Vs Third)'] = merged_df.apply(
                            lambda row: abs((row[f"{match_column_conv}_converted"] - row[f"{match_column_loaded}"])) / abs(row[f"{match_column_conv}_converted"]) * 100 if row[f"{match_column_conv}_converted"] != 0 else None, axis=1)

                # Print the summary
                total_records = len(merged_df)
                matched_records = len(merged_df[~merged_df['Difference']])
                matched_percentage = (matched_records / total_records) * 100

                # Ask if the column name for the primary key needs to be changed in the output file
                change_primary_key_name = input("Do you want to change the primary key column names in the output file? (yes/no): ").strip().lower()

                # Check if the input is valid
                while change_primary_key_name not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    change_primary_key_name = input("Do you want to change the primary key column names in the output file? (yes/no): ").strip().lower()

                if change_primary_key_name == 'yes':
                    new_primary_key_names = input("Enter the new primary key column names (comma-separated): ").split(',')
                    if len(new_primary_key_names) == len(primary_key_columns_leg):
                        for old_name, new_name in zip(primary_key_columns_leg, new_primary_key_names):
                            merged_df.rename(columns={old_name: new_name}, inplace=True)
                    else:
                        print("The number of new primary key column names does not match the number of primary key columns. Skipping renaming.")

                # Ask if the column name for the match key needs to be changed in the output file for the first file
                change_match_key_names_legacy = input("Do you want to update the match key column name for the first file in the output file? (yes/no): ").strip().lower()

                # Check if the input is valid
                while change_match_key_names_legacy not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    change_match_key_names_legacy = input("Do you want to update the match key column name for the first file in the output file? (yes/no): ").strip().lower()
                
                if change_match_key_names_legacy == 'yes':
                    new_match_key_names_legacy = input("Enter the new match key column name for the first file: ").strip()
                    if new_match_key_names_legacy:
                        merged_df.rename(columns={f"{match_column_leg}_legacy": new_match_key_names_legacy}, inplace=True)
                    else:
                        print("No new match key column name provided. Skipping renaming.")
                
                # Ask if the column name for the match key needs to be changed in the output file for the second file
                change_match_key_names_converted = input("Do you want to update the match key column name for the second file in the output file? (yes/no): ").strip().lower()

                # Check if the input is valid
                while change_match_key_names_converted not in ['yes', 'no']:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    change_match_key_names_converted = input("Do you want to update the match key column name for the second file in the output file? (yes/no): ").strip().lower()
                
                if change_match_key_names_converted == 'yes':
                    new_match_key_names_converted = input("Enter the new match key column name for the second file: ").strip()
                    if new_match_key_names_converted:
                        merged_df.rename(columns={f"{match_column_conv}_converted": new_match_key_names_converted}, inplace=True)
                    else:
                        print("No new match key column name provided. Skipping renaming.")
                
                # Ask if the column name for the match key needs to be changed in the output file for the third file
                if content3 is not None:
                    change_match_key_names_loaded = input("Do you want to update the match key column name for the third file in the output file? (yes/no): ").strip().lower()

                    # Check if the input is valid
                    while change_match_key_names_loaded not in ['yes', 'no']:
                        print("Invalid input. Please enter 'yes' or 'no'.")
                        change_match_key_names_loaded = input("Do you want to update the match key column name for the third file in the output file? (yes/no): ").strip().lower()
                    
                    if change_match_key_names_loaded == 'yes':
                        new_match_key_names_loaded = input("Enter the new match key column name for the third file: ").strip()
                        if new_match_key_names_loaded:
                            merged_df.rename(columns={f"{match_column_loaded}": new_match_key_names_loaded}, inplace=True)
                        else:
                            print("No new match key column name provided. Skipping renaming.")

                # Print the rows with differences
                differences = merged_df[merged_df['Difference']]
                if not differences.empty:
                    print("Differences found:")
                    print(differences)
                    print(f"Total records: {total_records}")
                    print(f"Matched records: {matched_records} ({matched_percentage:.2f}%)")
                    # Write the output to a new file
                    output_file = "Output.xlsx"
                    writer = pd.ExcelWriter(output_file)
                    merged_df.to_excel(writer, index=False)
                    writer._save()
                    print(f"Output written to {output_file}")
                else:
                    print("No differences found in the specified column.")

# Main function
def main():

    # Get file paths from user
    file1, file2,file3= get_file_paths()

    # Read the contents of the files
    content1, content2,content3 = read_files(file1, file2,file3 if file3 else None)

    # Compare the contents of the files
    compare_files(content1, content2,content3)

    print("Files read successfully.")

if __name__ == "__main__":
    main()




#6.	The process should show summarized data off the output report (i.e. % of records matched, % of records not matched)
#8.	The initial output should be a report showing a record for each distinct combination and the $ amount of the variation.
