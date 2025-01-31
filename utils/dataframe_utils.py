import holidays
import pandas as pd
import xarray as xr
import numpy as np
from typing import Union

def convert_to_dataframe(datasets: Union[xr.Dataset, pd.DataFrame], variables: list = None) -> pd.DataFrame:
    """
    Converts a combined xarray Dataset or pandas DataFrame to a pandas DataFrame, including specified variables.

    Parameters:
    datasets (Union[xr.Dataset, pd.DataFrame]): The combined xarray Dataset or pandas DataFrame.
    variables (list, optional): A list of variable names to include in the DataFrame. 
                                If None, include all variables in the dataset.

    Usage:
    df = convert_to_dataframe(combined_ds, variables=['tcc', 'hcc'])

    Returns:
    pd.DataFrame: A DataFrame containing the specified variables, with the index reset.
    """
    if isinstance(datasets, xr.Dataset):
        if not variables:
            variables = list(datasets.data_vars)

        print(f"[DEBUG] Dataset variables: {list(datasets.data_vars)}")
        print(f"[DEBUG] Requested variables: {variables}")

        # Check if variables are in the dataset
        if not all(var in datasets for var in variables):
            raise ValueError("[ERROR] One or more variables are not in the dataset")
        
        df = datasets[variables].to_dataframe().reset_index()
    elif isinstance(datasets, pd.DataFrame):
        print(f"[DEBUG] DataFrame columns: {list(datasets.columns)}")
        print(f"[DEBUG] Requested variables: {variables}")

        if variables:
            df = datasets[variables].copy()
        else:
            df = datasets.copy()
    else:
        raise ValueError("[ERROR] Unsupported data type. Expecting xarray.Dataset or pandas.DataFrame.")
    
    print(f"[INFO] Converted dataset to DataFrame. Showing in format [column title] [row counts]:\n{df.count()}")
    return df

def convert_to_datetime(df: pd.DataFrame, column: str = 'time', format: str = None) -> pd.DataFrame:
    """
    Converts a specified column in a DataFrame to datetime format.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the column to convert.
    column (str): Optional. The name of the column to convert to datetime.
    format (str): Optional. The format to use for conversion. If None, it will infer the format.

    Usage:
    df = convert_to_datetime(df, column='time', format='%Y-%m-%d %H:%M:%S')

    Returns:
    pd.DataFrame: The DataFrame with the specified column converted to datetime.
    """
    try:
        if format:
            df[column] = pd.to_datetime(df[column], format=format, errors='coerce')
        else:
            df[column] = pd.to_datetime(df[column], errors='coerce')
        
        successful_conversions = df[column].notna().sum()
        failed_conversions = df[column].isna().sum()
        
        print(f"[INFO] Successfully converted {successful_conversions} entries to datetime format.")
        if failed_conversions > 0:
            print(f"[WARNING] Failed to convert {failed_conversions} entries to datetime format.")
        
    except Exception as e:
        print(f"[ERROR] An error occurred while converting column '{column}' to datetime: {e}")
    
    return df

def convert_columns_to_string(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Convert specified columns in a DataFrame to strings.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the columns to convert.
    columns (list): A list of column names to convert to strings.

    Usage:
    convert_columns_to_string(df, ["latitude", "longitude"])

    Returns:
    pd.DataFrame: The DataFrame with the specified columns converted to strings.
    """
    for column in columns:
        df[column] = df[column].astype(str)
        print(f"[INFO] Converted column '{column}' to string.")
    
    return df

def convert_columns_to_float(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Convert specified columns in a DataFrame to float.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the columns to convert.
    columns (list): A list of column names to convert to float.

    Usage:
    df = convert_columns_to_float(df, ["num_sold"])

    Returns:
    pd.DataFrame: The DataFrame with the specified columns converted to float.
    """
    for column in columns:
        df[column] = df[column].astype(float)
        print(f"[INFO] Converted column '{column}' to float.")
    
    return df

def add_weekend_feature(df: pd.DataFrame, time_column: str, count_friday: bool = False) -> pd.DataFrame:
    """
    Add a 'weekend' column to the DataFrame. The 'weekend' column will be 1 if the day is Saturday or Sunday, and 0 otherwise.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the data.
    time_column (str): The name of the time column in the DataFrame. The time column should be of datetime type.
    count_friday (bool): True if you want to add Friday as a weekend, else False. Default is False

    Returns:
    pd.DataFrame: The DataFrame with the added 'weekend' column.
    
    Example Usage:
    df = add_weekend_feature(df, 'time')
    """
    # Ensure the time column is of datetime type
    df[time_column] = pd.to_datetime(df[time_column])
    
    # Set the time column as the index
    df.set_index(time_column, inplace=True)
    
    # Determine weekend starting dayofweek
    weekend_date = 4 if count_friday else 5

    # Add the 'weekend' column
    df['weekend'] = (df.index.dayofweek > weekend_date).astype(int)
    
    # Reset the index to restore the original DataFrame structure
    df.reset_index(inplace=True)
    
    return df

def add_holidays_feature(df: pd.DataFrame, time_column: str, country_column: str) -> pd.DataFrame:
    """
    Add a 'holidays' column to the DataFrame. The 'holidays' column will be 1 if the date is a holiday in the specified country, and 0 otherwise.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the data.
    time_column (str): The name of the time column in the DataFrame. The time column should be of datetime type.
    country_column (str): The name of the country column in the DataFrame.

    Returns:
    pd.DataFrame: The DataFrame with the added 'holidays' column.
    
    Example Usage:
    df = add_holidays_feature(df, 'time', 'country')
    """
    # Ensure the time column is of datetime type
    df[time_column] = pd.to_datetime(df[time_column])
    
    # Set the time column as the index
    df.set_index(time_column, inplace=True)
    
    # Create a dictionary to store holiday dates per country
    holidays_dates_per_country = {}
    
    # Get unique countries
    unique_countries = df[country_column].unique()
    
    # Iterate over each country to get the holidays
    for country in unique_countries:
        # Get the holiday dates for the country
        country_holidays = getattr(holidays, country)(years=set(df.index.year))
        holidays_dates_per_country[country] = [pd.to_datetime(date) for date, _ in country_holidays.items()]
        
        # Mark holidays in the DataFrame
        df.loc[df[country_column] == country, 'holidays'] = df.loc[df[country_column] == country].index.isin(holidays_dates_per_country[country])
    
    # Convert the 'holidays' column to integer type
    df['holidays'] = df['holidays'].astype(int)
    
    # Reset the index to restore the original DataFrame structure
    df.reset_index(inplace=True)
    
    return df

def add_end_of_year_holidays(df: pd.DataFrame, time_column: str) -> pd.DataFrame:
    """
    Add an 'end-of-year holidays' column to the DataFrame. The 'newyear' column will be 1 if the date is between December 25 and December 31, and 0 otherwise.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the data.
    time_column (str): The name of the time column in the DataFrame. The time column should be of datetime type.

    Returns:
    pd.DataFrame: The DataFrame with the added 'newyear' column.
    
    Example Usage:
    df = add_end_of_year_holidays(df, 'time')
    """
    # Ensure the time column is of datetime type
    df[time_column] = pd.to_datetime(df[time_column])
    
    # Set the time column as the index
    df.set_index(time_column, inplace=True)
    
    # Initialize the 'newyear' column with 0
    df['newyear'] = 0
    
    # Mark end-of-year holidays
    for day in range(25, 32):
        df.loc[(df.index.month == 12) & (df.index.day == day), 'newyear'] = 1
    
    # Reset the index to restore the original DataFrame structure
    df.reset_index(inplace=True)
    
    return df

def split_year_date_hour(df: pd.DataFrame, time_column: str, new_hour_col_name: str = 'hour_id', new_date_col_name: str = 'date_id', new_year_col_name: str = 'year_id') -> pd.DataFrame:
    """
    Split and add the 'date', 'hour', and 'year' from 'time' column in the DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.
    time_column (str): The name of the time column to extract 'date', 'hour', and 'year' from.
    new_hour_col_name (str): The name of the new hour column. Default is 'hour'.
    new_date_col_name (str): The name of the new date column. Default is 'date'.
    new_year_col_name (str): The name of the new year column. Default is 'year'.

    Usage:
    df = split_date_hour_and_year(df, time_column='time')

    Returns:
    pd.DataFrame: The DataFrame with 'date', 'hour', and 'year' columns added.
    """
    df = df.copy()
    df.loc[:, new_date_col_name] = df[time_column].dt.date
    df.loc[:, new_hour_col_name] = df[time_column].dt.hour
    df.loc[:, new_year_col_name] = df[time_column].dt.year

    print(f"[INFO] Extracted 'date', 'hour', and 'year' from '{time_column}'.")
    return df

def add_cyclical_calendar_features(df: pd.DataFrame, calendar_cycles: dict, time_column: str) -> pd.DataFrame:
    """
    Add cyclical calendar features (sine and cosine transformations) to the DataFrame.

    Parameters:
    df (pd.DataFrame): Input DataFrame with a datetime index.
    calendar_cycles (dict): Dictionary defining the cycle lengths for different calendar features.
    time_column (str): The name of the time column in the DataFrame.

    Returns:
    pd.DataFrame: DataFrame with added cyclical features.
    """
    print(f"[INFO] Adding cyclical calendar features: {list(calendar_cycles.keys())}")
    df.set_index(time_column, inplace=True)

    for feat, cycle in calendar_cycles.items():
        if feat == 'week':
            values = df.index.isocalendar().week
        else:
            values = getattr(df.index, feat)
        
        df[f"{feat}_sin"] = np.sin(2 * np.pi * values / cycle)
        df[f"{feat}_cos"] = np.cos(2 * np.pi * values / cycle)

    df.reset_index(inplace=True)
    
    return df

def factorize_column(df: pd.DataFrame, column: str, new_column: str) -> pd.DataFrame:
    """
    Factorizes a specified column and creates a new column with incrementing count.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.
    column (str): The name of the column to factorize.
    new_column (str): The name of the new column to store the incrementing count.

    Usage:
    df = factorize_column(df, column='date', new_column='date_id')

    Returns:
    pd.DataFrame: The DataFrame with the new factorized column added.
    """
    df = df.copy()
    df.loc[:, new_column] = pd.factorize(df[column])[0]
    print(f"[INFO] Factorized column '{column}' into '{new_column}' with incrementing count.")
    return df

def drop_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Drops the specified column(s) from the DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.
    columns (list): A list of column names to drop.

    Usage:
    df = drop_columns(df, columns=['date', 'hour'])

    Returns:
    pd.DataFrame: The DataFrame with the specified column(s) dropped.
    """
    df = df.drop(columns, axis=1)
    print(f"[INFO] Dropped columns: {columns}")
    return df

def drop_duplicates_and_reset_index(df: pd.DataFrame, subset: list = None) -> pd.DataFrame:
    """
    Drops duplicate rows based on specified columns and resets the index.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.
    subset (list): Optional. A list of column names to consider for identifying duplicates.
                   If None, considers all columns.

    Usage:
    df = drop_duplicates_and_reset_index(df, subset=['time'])

    Returns:
    pd.DataFrame: The DataFrame with duplicates dropped and index reset.
    """
    if subset:
        df = df.drop_duplicates(subset=subset, ignore_index=True)
    else:
        df = df.drop_duplicates(ignore_index=True)
    
    print(f"[INFO] Dropped duplicates if there was any. Remaining rows: {len(df)}")
    return df

def check_and_handle_missing_values(df: pd.DataFrame, drop: bool = False) -> pd.DataFrame:
    """
    Checks for missing values in a DataFrame and optionally drops rows with missing values.

    Parameters:
    df (pd.DataFrame): The DataFrame to check for missing values.
    drop (bool): If True, drops all rows with missing values. Default is False.

    Usage:
    df = check_and_handle_missing_values(df, drop=True)

    Returns:
    pd.DataFrame: The DataFrame after handling missing values.
    """
    missing_info = df.isnull().sum()
    total_missing = missing_info.sum()
    
    if total_missing > 0:
        print(f"[INFO] DataFrame has {total_missing} missing values.")
        print(missing_info[missing_info > 0])
        
        if drop:
            df = df.dropna()
            print("[INFO] Dropped all rows with missing values.")
        else:
            print("[INFO] Missing values were not dropped.")
    else:
        print("[INFO] No missing values in the DataFrame.")
    
    return df

def consistency_check(df: pd.DataFrame, time_column: str = 'time_idx') -> None:
    """
    Checks for any missing value in time column of the DataFrame.
    Time column must be in increasing index order.

    Parameters:
    df (pd.DataFrame): The DataFrame to check for consistency.

    Usage:
    consistency_check(df)
    """
    # Check for missing time indices
    expected_time_idx = set(range(df[time_column].min(), df[time_column].max() + 1))
    actual_time_idx = set(df[time_column].unique())
    missing_time_idx = expected_time_idx - actual_time_idx

    if missing_time_idx:
        print(f"[DEBUG] Missing time indices: {sorted(missing_time_idx)}")
        raise ValueError(f"Missing time indices detected: {sorted(missing_time_idx)}")
    else:
        print("[DEBUG] No missing time indices detected.")

def merge_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, on: str, how: str = 'inner') -> pd.DataFrame:
    """
    Merges two DataFrames on a specified column.

    Parameters:
    df1 (pd.DataFrame): The first DataFrame.
    df2 (pd.DataFrame): The second DataFrame.
    on (str): The column name to merge on.
    how (str): How to perform the merge. Default is 'inner'. Options include 'left', 'right', 'outer', 'inner'.

    Usage:
    merged_df = merge_dataframes(df1, df2, on='time', how='inner')

    Returns:
    pd.DataFrame: The merged DataFrame.
    """
    merged_df = pd.merge(df1, df2, on=on, how=how)
    print(f"[INFO] Merged DataFrames on column '{on}' using '{how}' method.")
    return merged_df

def save_to_csv(df: pd.DataFrame, save_dir: str):
    """
    Saves a DataFrame to a CSV file.

    Parameters:
    df (pd.DataFrame): The DataFrame to save.
    save_dir (str): The directory path where the CSV file should be saved.

    Usage:
    save_to_csv(df, 'output/data.csv')
    """
    print(f'[INFO] Saving DataFrame...')
    df.to_csv(f'{save_dir}', index=False)
    print(f"[INFO] Saved DataFrame to {save_dir}")