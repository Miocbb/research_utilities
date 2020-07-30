#!/usr/bin/env python3

import numpy as np
def Etot_fchk(g16_fchk):
    """
    @param g16_fchk: string. the path for g16 fchk file.
    @return float. the SCF total energy
    """
    if not g16_fchk.endswith('.fchk'):
        raise Exception('{:s} is not a g16 fchk file.'.format(g16_fchk))

    try:
        with open(g16_fchk) as f:
            for line in f:
                if 'Total Energy' in line:
                    Etot = line.split()[-1]
                    try:
                        return float(Etot)
                    except Exception:
                        return np.nan
    except Exception:
        pass
    return np.nan

def scf_Etot_log(g16_log):
    """
    @param g16_fchk: string. the path for g16 log file.
    @return float. the SCF total energy

    @note
    The search partern is "SCF Done:". If multiple SCF energies
    are found, return the last one.
    """
    if not g16_log.endswith('.log'):
        raise Exception('{:s} is not a g16 log file.'.format(g16_log))

    try:
        ene = []
        with open(g16_log) as f:
            for line in f:
                if line.strip().startswith('SCF Done:'):
                    ene.append(float(line.split()[4]))
        if ene:
            return ene[-1]
    except Exception:
        pass
    return np.nan
