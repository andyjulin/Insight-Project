import numpy as np
import pandas as pd
import sqlite3


def date_columns(query):
    """If a date column is included in the query, parse it as a date in the
    dataframe."""
    dates = []
    fields = ["Collision_Date", "Process_Date"]
    if '*' in query:
        dates = fields
    else:
        for date in fields:
            if date in query:
                dates.append(date)

        if not dates:
            dates = None

    return dates


def run_sql(query, sql_file="../data/switrs.sqlite3"):
    with sqlite3.connect(sql_file) as con:
        df = pd.read_sql_query(query, con, parse_dates=date_columns(query))

        return df


def set_factorize(df, in_name, out_name = '', show = False):
    if out_name is '':
        out_name = in_name
        df[in_name + '_old'] = df[in_name]
    
    vals, cols = df[in_name].factorize()
    
    df[in_name] = vals
    
    if show:
        print df[in_name].value_counts()


def get_base_switrs_df(query = None):
    if not query:
        query = """
SELECT * FROM Collision
WHERE Longitude IS NOT NULL 
AND Latitude IS NOT NULL 
AND Primary_Road IS NOT NULL
AND Collision_Time IS NOT NULL
AND Caltrans_County IS NOT NULL
AND Postmile_Prefix IS NOT NULL
AND Postmile IS NOT NULL
AND Caltrans_County IS NOT NULL
"""

    return run_sql(query)


def get_switrs_df():
    df = get_base_switrs_df()

    df['Collision_Year']      = df.Collision_Date.dt.year
    df['Collision_Month']     = df.Collision_Date.dt.month
    df['Collision_Day']       = df.Collision_Date.dt.day
    df['Collision_DayOfWeek'] = df.Collision_Date.dt.dayofweek 

    df['Collision_Hour']   = get_time_col(df.Collision_Time)[0]
    df['Collision_Minute'] = get_time_col(df.Collision_Time)[1]

    df['Collision_Hours'] = df.Collision_Hour \
                          + df.Collision_Minute / 60.0

    df['Collision_Minutes'] = df.Collision_Hour * 60.0 \
                            + df.Collision_Minute

    df['Postmile_Code'] = df.Postmile_Prefix \
                        + df.Postmile.astype(str)

    return df


def get_time_col(df):
    return df.str.split(':', n=3, expand=True).apply(pd.Series).astype(int)
