"""
Related to the orbitals from calculation with using gaussian package.
"""

import numpy as np
import pandas as pd


def _is_degenerate(orb1, orb2):
    """
    The accuracy is 1e-4. This should be small enough.
    """
    return abs(orb1 - orb2) <= 1e-4


def _index_symmetry(syms_eigs):
    """
    Index the symmetry based on its occurrence according to the corresponding
    orbital energies (in an increasing order). The index starts from 1, NOT
    from 0. This way of indexing is a notation for chemists.

    @param syms_eigs: [(symmetry, eig), ...]
    """
    syms, eigs = zip(*syms_eigs)
    syms_dict = dict([(i, 0) for i in set(syms)])
    i = 0
    while i < len(syms):
        sym = syms[i]
        eig = eigs[i]
        idx = syms_dict[sym] + 1
        syms_dict[sym] = idx
        n = 1
        if (i != len(syms) - 1 and sym == syms[i+1] and
                _is_degenerate(eig, eigs[i+1])):

            new_sym = '{:d}{:s}'.format(idx, sym)
            syms_eigs[i+1] = (new_sym, eigs[i+1])
            n = 2
        new_sym = '{:d}{:s}'.format(idx, sym)
        syms_eigs[i] = (new_sym, eig)
        i += n
    return syms_eigs


def _get_sym(f):
    """
    Extract the orbital symmetries from a gaussian log file.

    @param f: file. It points to the FIRST LINE of orbital symmetries.
              The first line of orbital symmetries should always start with
              'Occupied xxx xxx'.
    @return syms: [symmetry, ...]. list of string that represents the orbital
            symmetries for occupied and virtual orbitals.

    @note
    The spin of the orbital symmetries is not handled here.
    """
    syms = []
    line = f.readline()
    # check prerequisite.
    if not line.strip().startswith('Occupied'):
        raise Exception(
            """Implementation Error: Wrong position of file pointer to extract
            the orbital symmetries.""")

    while line:
        pst = f.tell() - len(line)
        line = line.strip()
        if line.startswith('Occupied'):
            line = line.replace('(', '').replace(')', '')
            line = line.split()
            line.pop(0)
        elif line.startswith('Virtual'):
            line = line.replace('(', '').replace(')', '')
            line = line.split()
            line.pop(0)
        elif not line.startswith('('):
            # rewind to the begining of the current line
            f.seek(pst)
            break
        if type(line) == str:
            line = line.replace('(', '').replace(')', '').split()
        syms += line
        line = f.readline()
    return syms


def _get_orb_sym(f):
    """
    Extract the orbital symmetries from a gaussian log file.

    @param f: file. It points to the indicating line of orbital symmetries. The
           indicating line is 'Orbital symmetries:'.
    @return rst: [[symmetry, ...], ...]. list of string that represents the
            orbital symmetries for all orbitals. len(rst)=1 for restriced
            calculation and len(rst)=2 for unrestricted calculation.
    """
    line = f.readline()
    # check prerequisite.
    if not line.strip().startswith('Orbital symmetries:'):
        raise Exception(
            'Wrong position of file pointer to extract the orbital symmetries.')
    line = f.readline()
    if line.strip().startswith('Occupied'):
        f.seek(f.tell() - len(line))
        rst = [_get_sym(f)]
        return rst
    elif line.strip().startswith('Alpha Orbitals:'):
        rst = [_get_sym(f)]
        f.readline()
        rst.append(_get_sym(f))
        return rst


def _get_orb_ene(f):
    """
    Extract the orbital energies from a gaussian log file.

    @param f: file. It points to the FIRST LINE of orbital energies. The first
           line should always start with 'Alpha  occ. eigenvalues --'.
    @return rst: [[eig, ...], ...]. 2-dimension list. The length of `rst` is
            either 1 for spin=1 (alpha) or 2 for spin=2 (alpha, beta).
    """
    a_occ_pattern = 'Alpha  occ. eigenvalues --'
    a_vir_pattern = 'Alpha virt. eigenvalues --'
    b_occ_pattern = 'Beta  occ. eigenvalues --'
    b_vir_pattern = 'Beta virt. eigenvalues --'

    line = f.readline()
    # check prerequisite.
    if not (line.strip().startswith(a_occ_pattern)):
        raise Exception(
            """Implementation error: wrong position of file pointer to extract
            the orbital energies.""")

    a_eig = []
    b_eig = []
    while line:
        pst = f.tell() - len(line)
        line = line.strip()
        if line.startswith(a_occ_pattern):
            eigs = np.array(line.replace(
                a_occ_pattern, '').split(), dtype=float)
            a_eig += list(eigs)
        elif line.startswith(a_vir_pattern):
            eigs = np.array(line.replace(
                a_vir_pattern, '').split(), dtype=float)
            a_eig += list(eigs)
        elif line.startswith(b_occ_pattern):
            eigs = np.array(line.replace(
                b_occ_pattern, '').split(), dtype=float)
            b_eig += list(eigs)
        elif line.startswith(b_vir_pattern):
            eigs = np.array(line.replace(
                b_vir_pattern, '').split(), dtype=float)
            b_eig += list(eigs)
        else:
            # rewind to the begining of the current line
            f.seek(pst)
            break
        line = f.readline()
    rst = [a_eig]
    if b_eig:
        rst.append(b_eig)
    return rst


def get_orb_sym(g16_log):
    """
    Extrat the orbital symmetries from gaussian log file.

    @param g16_log: string. file path for gaussian log file.
    @return rst: [[symmetry, ...], ...]. Orbital symmetries are stored in string.
            The length of rst is either 1 for spin=1 (alpha) and 2 for spin=2
            (alpha, beta). If no results are found, return None.

    @note
    The order of symmetries are the same as the orbital energies
    (increasing order) for each spin.
    """
    rst = []
    with open(g16_log) as f:
        line = f.readline()
        while line:
            line = f.readline()
            if line.strip().startswith('Orbital symmetries:'):
                # get orbital symmetries.
                f.seek(f.tell() - len(line))
                syms = _get_orb_sym(f)
                rst.append(syms)
    return rst[-1] if rst else None


def get_orb_ene_log(g16_log):
    """
    Extrat the orbital_energies from gaussian log file.

    @param g16_log: string. file path for gaussian log file.
    @return rst: [[energy, ...], ...]. Orbital energies are stored in float.
            The length of rst is either 1 for spin=1 (alpha) and 2 for spin=2
            (alpha, beta). If no results are found, return None.
    """
    rst = []
    with open(g16_log) as f:
        line = f.readline()
        while line:
            line = f.readline()
            if line.strip().startswith('Alpha  occ. eigenvalues --'):
                # get orbital symmetries.
                f.seek(f.tell() - len(line))
                eigs = _get_orb_ene(f)
                if eigs:
                    rst.append(eigs)
    return rst[-1] if rst else None


def get_orb_sym_ene(g16_log, index_sym=True):
    """
    Extrat the orbital_symmetries and orbital energies from gaussian log file.

    @param g16_log: string. file path for gaussian log file.
    @param index_sym: bool. Index the orbital symmetry with the number of
           occurrence. Default to True.
    @return df_rst: [pd.DataFrame, ...]. The length of rst is either 1 for spin=1
            (alpha) and 2 for spin=2 (alpha, beta).

    @note
    1. According to the searching pattern, if multiple symmetries/energies are
       found, this function always processes the last one to return.
    """
    syms = []
    eigs = []

    # extract symmetries and energies.
    with open(g16_log) as f:
        line = f.readline()
        while line:
            # The flag 'Orbital symmetries' indicates the orbital symmetries
            # and energies are in the following lines.
            if line.strip().startswith('Orbital symmetries:'):
                # get orbital symmetries.
                f.seek(f.tell() - len(line))
                syms_t = _get_orb_sym(f)
                if not syms_t:
                    raise Exception(
                        'Cannot find orbital symmetries due to format issue of log file.')

                # Stats to extract orbital energies.
                # The orbital energies follow the orbital symmetries in one line.
                f.readline()
                eigs_t = _get_orb_ene(f)
                if not eigs_t:
                    raise Exception(
                        'Cannot find orbital energies due to format issue of log file.')

                syms.append(syms_t)
                eigs.append(eigs_t)
            line = f.readline()

    used_syms = syms[-1] if syms else None
    if used_syms is None:
        raise Exception('Cannot find orbital symmetries.')
    used_eigs = eigs[-1] if eigs else None
    if used_eigs is None:
        raise Exception('Cannot find orbital energies.')
    if len(used_eigs) != len(used_syms):
        raise Exception(
            'Error: number of spin for orbital symmetries and energies does not match.')
    rst = []
    for i in range(len(used_eigs)):
        if len(used_eigs[i]) != len(used_syms[i]):
            raise Exception(
                'Number of orbital symmetries and energies does not match for eigs{:d}.'.format(i))
        else:
            rst.append(list(zip(used_syms[i], used_eigs[i])))
    # index the symmetry
    if index_sym:
        for i in rst:
            _index_symmetry(i)
    df_rst = []
    for i in rst:
        df_t = pd.DataFrame(i, columns='symmetry energy'.split()).reset_index()
        df_t['symmetry'] = df_t['symmetry'].astype(str)
        df_rst.append(df_t)
    return df_rst
