#!/usr/bin/env python3


def losc_Etot(qm4d_out):
    """
    Get total energy for post-SCF-LOSC-DFA from qm4d output.

    @param qm4d_out: string. the path for qm4d output file.
    @return float. the total energy for post-SCF-LOSC

    @note
    This function makes sure to exit with no error. It
    either returns a number or 'float('nan')'.
    """
    try:
        with open(qm4d_out) as f:
            for line in f:
                if 'E_tot_losc' in line:
                    line = line.replace('=', ' ')
                    Etot = line.split()[-1]
                    try:
                        return float(Etot)
                    except Exception:
                        return float('nan')
    except Exception:
        pass
    return float('nan')


def scf_Etot(qm4d_out):
    """
    Get SCF total energy from qm4d output.
    @param qm4d_out: string. the path for qm4d output file.
    @return float. the SCF total energy

    @note
    This function makes sure to exit with no error. It
    either returns a number or 'float('nan')'.
    """
    try:
        with open(qm4d_out) as f:
            for line in f:
                if 'SCF converged successfully. nIter' in line:
                    line = line.replace('=', ' ')
                    Etot = line.split()[-1]
                    try:
                        return float(Etot)
                    except Exception:
                        return float('nan')
    except Exception:
        pass
    return float('nan')
