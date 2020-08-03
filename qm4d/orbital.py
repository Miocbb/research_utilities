import sys
import os
from ..exception.exception import *

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


def _index(eig_dict, spin=0, idx=0):
    """
    @param eigs_dict: keys are the column names, and values are lists store the
           eigenvalues for each orbitals.
    """
    return next(x for x, val in enumerate(eig_dict['is'])
                if eig_dict['is'][x] == spin and eig_dict['i'][x] == idx)


def _IP(eigs_data, aelec, belec, based_on='eig_dfa'):
    """
    @param eigs_data: dict{('data': 2d-array), ('columns': list of column names)}
    """
    a_homo, b_homo = aelec - 1, belec - 1
    eig_dict = dict(zip(eigs_data['columns'], zip(*eigs_data['data'])))
    a_eig = eigs_data['data'][_index(eig_dict, spin=0, idx=a_homo)]
    a_eig_dict = dict(zip(eigs_data['columns'], a_eig))
    if b_homo < 0:
        return a_eig_dict
    elif len(set(eig_dict['is'])) == 1:
        return a_eig_dict
    else:
        b_eig = eigs_data['data'][_index(eig_dict, spin=1, idx=b_homo)]
        b_eig_dict = dict(zip(eigs_data['columns'], b_eig))
        return (a_eig_dict
                if float(a_eig_dict[based_on]) >= float(b_eig_dict[based_on])
                else b_eig_dict)


def _EA(eigs_data, aelec, belec, based_on='eig_dfa'):
    """
    @param eigs_data: dict{('data': 2d-array), ('columns': list of column names)}
    """
    a_lumo, b_lumo = aelec, belec
    eig_dict = dict(zip(eigs_data['columns'], zip(*eigs_data['data'])))
    a_eig = eigs_data['data'][_index(eig_dict, spin=0, idx=a_lumo)]
    a_eig_dict = dict(zip(eigs_data['columns'], a_eig))
    if len(set(eig_dict['is'])) == 1:
        return a_eig_dict
    else:
        b_eig = eigs_data['data'][_index(eig_dict, spin=1, idx=b_lumo)]
        b_eig_dict = dict(zip(eigs_data['columns'], b_eig))
        return (a_eig_dict
                if float(a_eig_dict[based_on]) <= float(b_eig_dict[based_on])
                else b_eig_dict)


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
    raise NoResultsFoundFromOutput(f_qm4d_out.name, start,
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
        raise NoResultsFoundFromOutput(out_name, start,
                                       'Cannot find raw lines for post-LOSC eigenvalues')


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
        raise NoResultsFoundFromOutput(out_name, start,
                                       f'Find NO raw lines for SCF eigenvalues.')


def f_post_losc_eigs(f_qm4d_out):
    """
    Get all the eigenvalues from a post-SCF-LOSC an opened qm4d output file.

    @return eig_data: dict. data for post-LOSC eigenvalues.
            keys are:
            'data': 2d array, type=float. Each row includes eigenvalues for one
                    orbital.
            'columns': list. The column names for `eig_dic['data']`.
    @note
    1. Internally, use `f_post_losc_eig_raw_lines()` to extract the eigenvalues
       information. See `f_post_losc_eig_raw_lines()` for the file pointer
       position at exit.
    """
    eig_lines = f_post_losc_eig_raw_lines(f_qm4d_out)
    line0 = eig_lines[0].replace('=', ' ').split()
    eig_data = {
        'data': [],
        'columns': line0[::2]
    }
    for line in eig_lines:
        line = line.replace('=', ' ').split()
        data = list(map(float, line[1::2]))
        eig_data['data'].append(data)

    return eig_data


def f_scf_eigs(f_qm4d_out):
    """
    Get all the SCF eigenvalues from the opened qm4d output file.

    @return eig_data: dict. data for SCF eigenvalues.
            keys are:
            'data': 2d array, type=float. Each row includes eigenvalues for one
                    orbital.
            'columns': list. The column names for `eig_dic['data']`.

    @note
    1. Internally, use `f_scf_eig_raw_lines()` to extract the eigenvalues
       information. See `f_scf_eig_raw_lines()` for the file pointer
       position at exit.
    """
    eig_lines = f_scf_eig_raw_lines(f_qm4d_out)
    columns = 'is i eig_dfa occ'.split()
    eig_data = {
        'data': [],
        'columns': columns
    }

    spin = 0
    for eigs in eig_lines:
        for line in eigs:
            line = line.replace(':', ' ').split()
            idx = int(line[0]) - 1
            eig_val = float(line[2])
            occ = float(line[-1])
            data = [spin, idx, eig_val, occ]
            eig_data['data'].append(data)

        spin += 1
    return eig_data


def post_losc_EA_eigs(qm4d_out, based_on='eig_dfa'):
    """
    Get the all the orbital energies (eig_dfa, eig_direct, eig_proj, eig_diag)
    that are corresponding to EA.

    @param qm4d_out: string. path of qm4d output file
    @param based_on: string. eigenvalues' name that is used to determine
           all the corresponding orbital energies for EA. Default to 'eig_dfa'.
           Supported choices are specified in `_post_losc_eig_names`.
    @return dict. All the eigenvalues selected based on `based_on`.
            Keys: `['is' 'i'] + _post_losc_eig_names`.
    """
    if based_on not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'based_on' are: {_post_losc_eig_names}'.")

    with open(qm4d_out) as f:
        # step1: get electron numbers
        aelec, belec = f_electron_numbers(f)
        if not aelec.is_integer() or not belec.is_integer():
            raise Exception(
                f'Detect fractional electrons for qm4d output: {qm4d_out}')

        # step2: get electron numbers
        eigs_data = f_post_losc_eigs(f)
        return _EA(eigs_data, aelec, belec, based_on=based_on)


def post_losc_IP_eigs(qm4d_out, based_on='eig_dfa'):
    """
    Get the all the orbital energies (eig_dfa, eig_direct, eig_proj, eig_diag)
    that are corresponding to IP.

    @param qm4d_out: string. path of qm4d output file
    @param based_on: string. name of the eigenvalue that is used to determine
           all the corresponding orbital energies for IP. Default to 'eig_dfa'.
           Supported choices are specified in `_post_losc_eig_names`.
    @return dict. All the eigenvalues selected based on `based_on`.
            Keys: `['is' 'i'] + _post_losc_eig_names`.
    """
    if based_on not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'based_on' are: {_post_losc_eig_names}'.")

    with open(qm4d_out) as f:
        # step1: get electron numbers
        aelec, belec = f_electron_numbers(f)
        if not aelec.is_integer() or not belec.is_integer():
            raise Exception(
                f'Detect fractional electrons for qm4d output: {qm4d_out}')

        # step2: get electron numbers
        eigs_data = f_post_losc_eigs(f)
        return _IP(eigs_data, aelec, belec, based_on=based_on)


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
    @return float. The corresponding eigenvalue for EA.
    """
    if selection not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'selection' are: {_post_losc_eig_names}'.")

    return float(post_losc_EA_eigs(qm4d_out, based_on=based_on)[selection])


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
    @return float. The corresponding eigenvalue for IP.
    """
    if selection not in _post_losc_eig_names:
        raise ValueError(
            f"Valid values for 'selection' are: {_post_losc_eig_names}'.")

    return float(post_losc_IP_eigs(qm4d_out, based_on=based_on)[selection])


def scf_IP(qm4d_out):
    """
    Get the SCF orbital energy that is corresponding to IP.

    @param qm4d_out: string. path of qm4d output file
    @return float. The corresponding eigenvalue for IP. If no result is found,
            return 'float('nan')`
    """
    with open(qm4d_out) as f:
        aelec, belec = f_electron_numbers(f)
        if not aelec.is_integer() or not belec.is_integer():
            raise Exception('Detect fractional electron.')

        eigs_data = f_scf_eigs(f)
        return _IP(eigs_data, aelec, belec, based_on='eig_dfa')['eig_dfa']


def scf_EA(qm4d_out):
    """
    Get the SCF orbital energy that is corresponding to EA.

    @param qm4d_out: string. path of qm4d output file
    @return float. The corresponding eigenvalue for EA.

    @note
    1. If alpha and beta orbital energy are degenerated, return the results
    from alpha.
    """
    with open(qm4d_out) as f:
        aelec, belec = f_electron_numbers(f)
        if not aelec.is_integer() or not belec.is_integer():
            raise Exception('Detect fractional electron.')

        eigs_data = f_scf_eigs(f)
        return _EA(eigs_data, aelec, belec, based_on='eig_dfa')['eig_dfa']
