#!/usr/bin/env python3

import pandas as pd


def error_summary(df, subset, ref):
    """
    Summarize the errors for a pd.DataFrame.

    @param df: pd.DataFrame. The input dataframe
    @param subset: list, array-like. The subset of columns in the input dataframe
        that will be used to calculate the errors.
    @param ref: string. The columns name that is used as the reference.

    @return df_summary: pd.DataFrame. The dataframe contains all the summarized
        error information. It includes:
        'mae': the mean absolute error
        'mse': the mean signed error
        'abs_min': the minimal absolute error
        'abs_max': the maximum absolute error
        'abs_min_idx': the index of the minimal absolute error
        'abs_max_idx': the index of the maximal absolute error
        'count': the number of cases
    """
    subset = list(subset)
    df_error = df[subset] - df[[ref]].values
    df_summary = pd.DataFrame(columns=df_error.columns)
    df_error_abs = df_error.abs()
    df_summary.loc['mae'] = df_error_abs.mean()
    df_summary.loc['mse'] = df_error.mean()
    df_summary.loc['abs_min'] = df_error_abs.min()
    df_summary.loc['abs_max'] = df_error_abs.max()
    df_summary.loc['abs_min_idx'] = df_error_abs.idxmin()
    df_summary.loc['abs_max_idx'] = df_error_abs.idxmax()
    df_summary.loc['count'] = df_error.count()
    return df_summary
