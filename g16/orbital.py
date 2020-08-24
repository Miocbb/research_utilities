"""
Related to the orbitals from calculation with using gaussian package.
"""

from research_utilities.exception.exception import *


def _f_orbital_symmetries(f):
    """
    Extract the FIRST set of orbital symmetries from a gaussian log file.
    The spin of the orbital symmetries is not handled here.

    @param f: file. It points to the FIRST LINE of orbital symmetries.
              The first line of orbital symmetries should always start with
              'Occupied xxx xxx'.
    @return syms: [symmetry, ...]. list of string that represents the orbital
            symmetries for occupied and virtual orbitals.
    """
    start = f.tell()
    syms = []
    line = f.readline()
    while line:
        if line.strip().startswith('Occupied'):
            line = line.replace('(', '').replace(')', '')
            line = line.split()
            line.pop(0)
        elif line.strip().startswith('Virtual'):
            line = line.replace('(', '').replace(')', '')
            line = line.split()
            line.pop(0)
        elif not line.strip().startswith('('):
            # rewind to the begining of the current line
            f.seek(f.tell() - len(line))
            break
        if type(line) == str:
            line = line.replace('(', '').replace(')', '').split()
        syms += line
        line = f.readline()
    if line:
        return syms
    else:
        raise NoResultsFoundFromOutput(
            f.name, start, 'No orbital symmetries found.')

def f_electron_numbers(f_g16_log):
    """
    Extract the electron numbers for alpha and beta from an g16 log file stream.

    @param f_g16_log: file object of a gaussian log file.
    @return (aelec, belec): (float, float). The alpha and beta electron numbers.
    """

    start = f_g16_log.tell()
    line = f_g16_log.readline()
    while line:
        if 'alpha electrons' in line:
            t = line.strip().split()
            return float(t[0]), float(t[3])
        line = f_g16_log.readline()
    raise NoResultsFoundFromOutput(f_g16_log.name, start, 'No electron number found.')


def f_orbital_symmetries(f_g16_log):
    """
    Extract the FIRST set of orbital symmetries from an opened gaussian log file
    from the CURRENT file pointer position.

    @param f_g16_log: file object of a gaussian log file.
    @return rst: [[symmetry, ...], ...]. list of string that represents the orbital
            symmetries for all orbitals. `len(rst)=1` for restriced calculation
            and `len(rst)=2` for unrestricted calculation.
    @note
    1. At exit, the file pointer locates at the end of the last line for orbital
       symmetries.
    """
    g16_log = f_g16_log.name
    g16_log_start = f_g16_log.tell()
    line = f_g16_log.readline()
    # navigate to the starting line that orbital symmetires information follows.
    while line:
        if line.strip().startswith('Orbital symmetries:'):
            break
        line = f_g16_log.readline()
    line = f_g16_log.readline()
    if line.strip().startswith('Occupied'):
        f_g16_log.seek(f_g16_log.tell() - len(line))
        rst = [_f_orbital_symmetries(f_g16_log)]
        return rst
    elif line.strip().startswith('Alpha Orbitals:'):
        rst = [_f_orbital_symmetries(f_g16_log)]
        f_g16_log.readline()
        rst.append(_f_orbital_symmetries(f_g16_log))
        return rst
    else:
        raise UnexpectedOutputFormat(
            g16_log, 'Search orbital symmetries fails')
    raise NoResultsFoundFromOutput(
        g16_log, g16_log_start, 'No orbital symmetries found.')


def f_orbital_energies(f_g16_log):
    """
    Extract the FIRST set of orbital energies from an opened gaussian log file.

    @param f_g16_log: file.
    @return rst: [[eig, ...], ...]. 2-dimension list. `len(rst)` is the spin of
            the calculation.
    """
    a_occ_pattern = 'Alpha  occ. eigenvalues --'
    a_vir_pattern = 'Alpha virt. eigenvalues --'
    b_occ_pattern = 'Beta  occ. eigenvalues --'
    b_vir_pattern = 'Beta virt. eigenvalues --'

    line = f_g16_log.readline()
    while line:
        if line.strip().startswith(a_occ_pattern):
            f_g16_log.seek(f_g16_log.tell() - len(line))
            break
        line = f_g16_log.readline()

    a_eig = []
    b_eig = []
    line = f_g16_log.readline()
    while line:
        if line.strip().startswith(a_occ_pattern):
            eigs = map(float, line.replace(a_occ_pattern, '').split())
            a_eig += list(eigs)
        elif line.strip().startswith(a_vir_pattern):
            eigs = map(float, line.replace(a_vir_pattern, '').split())
            a_eig += list(eigs)
        elif line.strip().startswith(b_occ_pattern):
            eigs = map(float, line.replace(b_occ_pattern, '').split())
            b_eig += list(eigs)
        elif line.strip().startswith(b_vir_pattern):
            eigs = map(float, line.replace(b_vir_pattern, '').split())
            b_eig += list(eigs)
        else:
            # rewind to the begining of the current line
            f_g16_log.seek(f_g16_log.tell() - len(line))
            break
        line = f_g16_log.readline()
    rst = [i for i in [a_eig, b_eig] if i]
    return rst


def _index_symmetry(d):
    """
    Index orbital symmetry labels with its number of occurrence.

    @param d[in, out]: dict.
           {('symmetry': list of symmetries),
            ('energy': list of orbital energies)}.
    @return Add ('indexed_symmetry': list of indexed symmetries) to `d`.
    """
    sym_set = set(d['symmetry'])
    sym_count = dict([(i, 0) for i in sym_set])
    d['indexed_symmetry'] = [None] * len(d['symmetry'])

    for i, sym in enumerate(d['symmetry']):
        if i == 0:
            sym_count[sym] += 1
            n = sym_count[sym]
            d['indexed_symmetry'][i] = f'{n}{sym}'
        else:
            if (d['symmetry'][i] == d['symmetry'][i-1] and
                        abs(d['energy'][i] - d['energy'][i - 1]) < 1e-4
                    ):
                d['indexed_symmetry'][i] = d['indexed_symmetry'][i-1]
            else:
                sym_count[sym] += 1
                n = sym_count[sym]
                d['indexed_symmetry'][i] = f'{n}{sym}'
    return d


def f_orbital_symmetries_energies(f_g16_log, index_sym=True):
    """
    Extrat the FIRST set of orbital_symmetries and orbital energies from
    an open gaussian log file.

    @param f_g16_log: file.
    @param index_sym: bool. Index the orbital symmetry with the number of
           occurrence. Default to True.
    @return rst: [dict, ...]. `len(rst)` is the spin of the calculation.
    """
    # extract symmetries
    start_pst = f_g16_log.tell()
    syms = f_orbital_symmetries(f_g16_log)
    if not syms:
        raise NoResultsFoundFromOutput(f_g16_log.name, start_pst,
                                       'No orbital symmetries from g16 output.')
    # extract symmetries
    line = f_g16_log.readline()
    line = f_g16_log.readline()
    if not line.strip().startswith('Alpha  occ. eigenvalues --'):
        raise UnexpectedOutputFormat(f_g16_log.name,
                                     'No orbital energies follow orbital symmetries.')
    else:
        f_g16_log.seek(f_g16_log.tell() - len(line))
    start_pst = f_g16_log.tell()
    eigs = f_orbital_energies(f_g16_log)
    if not eigs:
        raise NoResultsFoundFromOutput(f_g16_log.name, start_pst,
                                       'No orbital energies from g16 output.')

    if len(eigs) != len(syms):
        raise Exception(
            'Spin for orbital symmetries and energies does not match.')
    for i in range(len(eigs)):
        if len(eigs[i]) != len(syms[i]):
            raise Exception(
                'Dimension of orbital symmetires and energies does not match.')

    rst = [{'symmetry': syms[i], 'energy': eigs[i]} for i in range(len(syms))]

    # index the symmetry
    if index_sym:
        for i in rst:
            _index_symmetry(i)
    return rst
