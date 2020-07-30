import sys
import os
import numpy as np
import pandas as pd

"""
Note:
1. All functions start with a prefix `f_xxx` deals with an opened qm4d output
file directly by a file pointer. Those functions are used for searching and
extracting information based some searching partterns. They will look up the
file forward starting from the current position of the file pointer and
terminate IMMEDIATELY after the needed information is obtained.

SO KEEP IN MIND: the position of the input file pointer will be moved around
in these function ('f_xxx') during the function calling.
See each function for the termination specification.

2. file.tell() function is used explicitly in this module. So do not pass the
file object whose file.next() function is used implicitly/explicitly to the
functions in this module.
"""

_post_losc_eig_names = tuple('eig_dfa eig_proj eig_direct eig_diag'.split())


class QM4D_Output_No_Results_Found(Exception):
    def __init__(self, qm4d_out, start, message):
        self.qm4d_out = qm4d_out
        self.start = start
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return (f'\nError type: {self.__class__.__name__}\n' +
                f'QM4D output file: {self.qm4d_out}\n'
                + f'File starting position of searching: {self.start}\n' +
                f'Error message: {self.message}')


def _print_err(*args, **kargs):
    print(file=sys.stderr, *args, **kargs)


def f_electron_numbers(f_qm4d_out):
    """
    Get electron number for alpha and beta.

    @return tuple(aelec, belec): alpha and beta electron numbers in float.

    @note
    1. The searching pattern is "Alpha electrons =".
    2. In exit, the file pointer is at the end of the matched line.
    """
    start = f_qm4d_out.tell()
    line = f_qm4d_out.readline()
    while line:
        if line.startswith('Alpha electrons ='):
            line = line.strip().replace('=', ' ').split()
            num = (float(line[2]), float(line[-1]))
            return num
        line = f_qm4d_out.readline()
    raise QM4D_Output_No_Results_Found(f_qm4d_out.name, start,
                                       'Cannot get electron number')


def f_post_losc_eig_raw_lines(f_qm4d_out):
    """
    Get the all the raw lines of eigenvalues from an opened qm4d output
    file for post-SCF-LOSC calculation.

    @return eig_lines: list. The elements are the raw lines extracted
    in order. The raw lines are striped.

    @note
    1. Searching partterns: ['is=', 'eig_dfa', 'eig_proj'].
    2. The eigenvalue lines are assumed to be continuous.
    3. In exit, the file pointer is at the end of the matched line.
    """
    def is_eig_line(line):
        return (line.startswith('is=') and
                'eig_dfa' in line and
                'eig_proj' in line)
    start = f_qm4d_out.tell()
    out_name = f_qm4d_out.name
    visited_eigs = False
    eig_lines = []
    line = f_qm4d_out.readline()
    while line:
        if is_eig_line(line):
            eig_lines.append(line.strip())
            visited_eigs = True
        line = f_qm4d_out.readline()
        # check if we should exit reading eigenvalue lines.
        if visited_eigs and not is_eig_line(line):
            f_qm4d_out.seek(f_qm4d_out.tell() - len(line))
            break
    if eig_lines:
        return eig_lines
    else:
        raise QM4D_Output_No_Results_Found(out_name, start,
                                           'Cannot find raw lines for post-LOSC eigenvalues')


def f_post_losc_eigs(f_qm4d_out):
    """
    Get all the eigenvalues from a post-SCF-LOSC an opened qm4d output file.

    @return df: pd.DataFrame. post-LOSC eigenvalues.
            Columns are:
            'is': spin of the orbital. dtype=int.
            'i': index of the orbital energy starting from 0. dtype=int.
            'eig_dfa': SCF eigenvalue from the parent DFA. dtype=float.
            'eig_proj': post-LOSC eigenvalue from the projection. dtype=float.
            'eig_direct': post-LOSC eigenvalue from direct correction. dtype=float.
            'eig_diag': post-LOSC eigenvalue from diagonization. dtype=float.

    @note
    1. Internally, use `f_post_losc_eig_raw_lines()` to extract the eigenvalues
       information. See `f_post_losc_eig_raw_lines()` for the file pointer
       position at exit.
    """
    try:
        eig_lines = f_post_losc_eig_raw_lines(f_qm4d_out)
        line0 = eig_lines[0].replace('=', ' ').split()
        df = pd.DataFrame(columns=line0[::2])
        for line in eig_lines:
            line = line.replace('=', ' ').split()
            line_dict = dict(zip(line[::2], line[1::2]))
            df = df.append(line_dict, ignore_index=True)

        # convert into float
        float_col = [x for x in df.columns if x.startswith('eig')]
        int_col = list(set(df.columns) - set(float_col))
        df[float_col] = df[float_col].astype('float64')
        df[int_col] = df[int_col].astype(int)
        return df
    except QM4D_Output_No_Results_Found as e:
        raise e
    except Exception as e:
        raise Exception(
            f'Fail to store all post-LOSC eigenvalues in pd.DataFrame: {e}')


def f_scf_eig_raw_lines(f_qm4d_out):
    """
    Get the all the raw lines of SCF eigenvalues a qm4d output file.

    @return eig_lines: [[line, ...], ...]. The elements are the raw lines
    extracted in order. The raw lines are striped.

    @note
    1. Searching parttern is ['Eigenvalues of spin=  0 :',
       'Eigenvalues of spin=  1 :'].
    2. At exit, the file pointer position is at the end of the line starting
       with 'Total electron number:'.
    """
    def append_eigs(eig_lines, f):
        line = f.readline()
        while line:
            if not line.startswith('Total electron number:'):
                eig_lines.append(line.strip())
            else:
                break
            line = f.readline()

    start = f_qm4d_out.tell()
    out_name = f_qm4d_out.name
    eig_lines = []
    line = f_qm4d_out.readline()
    while line:
        if line.startswith('Eigenvalues of spin=  0 :'):
            f_qm4d_out.readline()
            t = []
            append_eigs(t, f_qm4d_out)
            eig_lines.append(t)
        elif line.startswith('Eigenvalues of spin=  1 :'):
            f_qm4d_out.readline()
            t = []
            append_eigs(t, f_qm4d_out)
            eig_lines.append(t)
            break
        line = f_qm4d_out.readline()
    if eig_lines:
        return eig_lines
    else:
        raise QM4D_Output_No_Results_Found(out_name, start,
                                           f'Find NO raw lines for SCF eigenvalues.')


def f_scf_eigs(f_qm4d_out):
    """
    Get all the SCF eigenvalues from the opened qm4d output file.

    @return df_eigs: pd.DataFrame. SCF eigenvalues.
            Columns are:
            'is': spin of the orbital. dtype=int.
            'i': index of the orbital energy starting from 0. dtype=int.
            'eig_dfa': SCF eigenvalue from the DFA. dtype=float.
            'occ': occupation number. dtype=float.

    @note
    1. Internally, use `f_scf_eig_raw_lines()` to extract the eigenvalues
       information. See `f_scf_eig_raw_lines()` for the file pointer
       position at exit.
    """
    try:
        eig_lines = f_scf_eig_raw_lines(f_qm4d_out)
        columns = 'is i eig_dfa occ'.split()
        df = pd.DataFrame(columns=columns)

        spin = 0
        for eigs in eig_lines:
            for line in eigs:
                line = line.replace(':', ' ').split()
                idx = int(line[0]) - 1
                eig_val = float(line[2])
                occ = float(line[-1])
                info = [spin, idx, eig_val, occ]
                line_dict = dict(zip(columns, info))
                df = df.append(line_dict, ignore_index=True)

            spin += 1
        df['is'] = df['is'].astype(int)
        df['i'] = df['i'].astype(int)
        return df
    except QM4D_Output_No_Results_Found as e:
        raise e
    except Exception as e:
        raise Exception(
            f'Fail to store all SCF eigenvalues in pd.DataFrame: {e}')


def post_losc_EA_eigs(qm4d_out, based_on='eig_dfa'):
    """
    Get the all the orbital energies (eig_dfa, eig_direct, eig_proj, eig_diag)
    that are corresponding to EA.

    @param qm4d_out: string. path of qm4d output file
    @param based_on: string. eigenvalues' name that is used to determine
           all the corresponding orbital energies for EA. Default to 'eig_dfa'.
           Supported choices are specified in `_post_losc_eig_names`.
    @return pd.DataFrame. All the eigenvalues selected based on `based_on`.
            The returned DataFrame has the same format as the return values
            from function 'f_post_losc_eigs()'. If finding results fails, return
            'None'.
    """
    if based_on not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'based_on' are: {_post_losc_eig_names}'.")

    try:
        with open(qm4d_out) as f:
            # step1: get electron numbers
            aelec, belec = f_electron_numbers(f)
            if not aelec.is_integer() or not belec.is_integer():
                raise Exception(
                    f'Detect fractional electrons for qm4d output: {qm4d_out}')

            # step2: get electron numbers
            eigs = f_post_losc_eigs(f)
            a_lumo = aelec
            b_lumo = belec
            a_eig = eigs[(eigs['is'] == 0) & (eigs['i'] == a_lumo)
                         ].copy().reset_index(drop=True)
            b_eig = eigs[(eigs['is'] == 1) & (eigs['i'] == b_lumo)
                         ].copy().reset_index(drop=True)
            return a_eig if float(a_eig[based_on]) <= float(b_eig[based_on]) else b_eig
    except Exception as e:
        _print_err(f'Fail to get eigenvalues for EA from post-LOSC: {e}')
        return None


def post_losc_EA(qm4d_out, based_on='eig_dfa', selection='eig_proj'):
    """
    Get the orbital energy that is corresponding to EA.

    @param qm4d_out: string. path of qm4d output file
    @param based_on: string. the name of eigenvalue that is used to determine
           all the corresponding orbital energies for EA. Default to 'eig_dfa'.
           Supported choices are specified in `_post_losc_eig_names`.
    @param selection: string. the name of eigenvalue that is used to select the final
           one orbital energy from the determined eigenvalues for the EA.
           Default to 'eig_proj'.
           Supported choices are specified in `_post_losc_eig_names`.
    @return float. The corresponding eigenvalue for EA. If finding result fails,
            return `np.nan`
    """
    if selection not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'selection' are: {_post_losc_eig_names}'.")

    try:
        return float(post_losc_EA_eigs(qm4d_out, based_on=based_on)[selection])
    except Exception as e:
        _print_err(f'Fail to get the eigenvalue for EA: {e}')
        return np.nan


def post_losc_IP_eigs(qm4d_out, based_on='eig_dfa'):
    """
    Get the all the orbital energies (eig_dfa, eig_direct, eig_proj, eig_diag)
    that are corresponding to IP.

    @param qm4d_out: string. path of qm4d output file
    @param based_on: string. name of the eigenvalue that is used to determine
           all the corresponding orbital energies for IP. Default to 'eig_dfa'.
           Supported choices are specified in `_post_losc_eig_names`.
    @return pd.DataFrame. All the eigenvalues selected based on `based_on`.
            The returned DataFrame has the same format as the return values
            from function 'f_post_losc_eigs()'.
            If finding results fails, return `None`.
    """
    if based_on not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'based_on' are: {_post_losc_eig_names}'.")

    try:
        with open(qm4d_out) as f:
            aelec, belec = f_electron_numbers(f)
            if not aelec.is_integer() or not belec.is_integer():
                raise Exception(
                    f'Detect fractional electrons for qm4d output: {qm4d_out}')

            eigs = f_post_losc_eigs(f)
            a_homo = aelec - 1
            b_homo = belec - 1
            a_eig = eigs[(eigs['is'] == 0) & (eigs['i'] == a_homo)
                         ].copy().reset_index(drop=True)
            if b_homo < 0:
                return a_eig
            else:
                b_eig = eigs[(eigs['is'] == 1) & (eigs['i'] == b_homo)
                             ].copy().reset_index(drop=True)
                return (a_eig if float(a_eig[based_on]) >= float(b_eig[based_on])
                        else b_eig)
    except Exception as e:
        _print_err(f'Fail to get eigenvalues for IP for post-LOSC: {e}')
        return None


def post_losc_IP(qm4d_out, based_on='eig_dfa', selection='eig_proj'):
    """
    Get the orbital energy that is corresponding to IP.

    @param qm4d_out: string. path of qm4d output file
    @param based_on: string. name of eigenvalue that is used to determine
           all the corresponding orbital energies for IP. Default to 'eig_dfa'.
           Supported choices are specified in `_post_losc_eig_names`.
    @param selection: string. name of eigenvalue that is used to select the final
           one orbital energy from the determined eigenvalues for the IP.
           Default to 'eig_proj'.
           Supported choices are specified in `_post_losc_eig_names`.
    @return float. The corresponding eigenvalue for IP. If no result is found,
            return `np.nan`
    """
    if selection not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'selection' are: {_post_losc_eig_names}'.")

    try:
        return float(post_losc_IP_eigs(qm4d_out, based_on=based_on)[selection])
    except Exception as e:
        _print_err(f'Fail to get the eigenvalue for EA: {e}')
        return np.nan


def scf_IP(qm4d_out):
    """
    Get the SCF orbital energy that is corresponding to IP.

    @param qm4d_out: string. path of qm4d output file
    @return float. The corresponding eigenvalue for IP. If no result is found,
            return 'np.nan'

    @note
    1. This function is exception free.
    """
    try:
        with open(qm4d_out) as f:
            aelec, belec = f_electron_numbers(f)
            if not aelec.is_integer() or not belec.is_integer():
                raise Exception('Detect fractional electron.')

            eigs = f_scf_eigs(f)
            a_homo = aelec - 1
            b_homo = belec - 1
            a_eig = eigs[(eigs['is'] == 0) & (eigs['i'] == a_homo)
                         ].copy().reset_index(drop=True)

            df_eig = None
            if b_homo < 0:
                df_eig = a_eig
            else:
                b_eig = eigs[(eigs['is'] == 1) & (eigs['i'] == b_homo)
                             ].copy().reset_index(drop=True)
                df_eig = a_eig if float(a_eig['eig_dfa']) >= float(
                    b_eig['eig_dfa']) else b_eig
            return float(df_eig['eig_dfa'])
    except Exception as e:
        _print_err(f'Fail to get the SCF eigenvalue for IP: {e}')
        return np.nan


def scf_EA(qm4d_out):
    """
    Get the SCF orbital energy that is corresponding to EA.

    @param qm4d_out: string. path of qm4d output file
    @return float. The corresponding eigenvalue for EA. If no result is found,
            return with 'np.nan'

    @note
    1. If alpha and beta orbital energy are degenerated, return the results
    from alpha.
    2. This function is exception free.
    """
    try:
        with open(qm4d_out) as f:
            aelec, belec = f_electron_numbers(f)
            if not aelec.is_integer() or not belec.is_integer():
                raise Exception('Detect fractional electron.')

            eigs = f_scf_eigs(f)
            a_lumo = aelec
            a_eig = eigs[(eigs['is'] == 0) & (eigs['i'] == a_lumo)
                         ].copy().reset_index(drop=True)
            b_lumo = belec
            b_eig = eigs[(eigs['is'] == 1) & (eigs['i'] == b_lumo)
                         ].copy().reset_index(drop=True)
            df_eig = a_eig if float(a_eig['eig_dfa']) <= float(
                b_eig['eig_dfa']) else b_eig
            return float(df_eig['eig_dfa'])
    except Exception as e:
        _print_err(f'Fail to get the SCF eigenvalue for EA: {e}')
        return np.nan
