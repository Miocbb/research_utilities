#!/usr/bin/env python3

import shutil
import os
import sys
from subprocess import Popen, PIPE
import subprocess
from research_utilities.qm4d.input_file import Input


class QM4D_SCFError(Exception):
    def __init__(self, msg):
        self._msg = msg
        super().__init__(msg)

    #def __str__(self):
    #    return self._msg


class QM4D_RunTimeError(Exception):
    def __init__(self, msg):
        self._msg = msg
        super().__init__(msg)

    def __str__(self):
        return f'QM4D runtime error: {self._msg}'


def abspath(qm4d_exe) -> str:
    qm4d_exe_sh = shutil.which(qm4d_exe)
    if qm4d_exe_sh is None:
        raise Exception('qm4d is not a executable path: ', qm4d_exe)
    # get abspath for qm4d exe
    abs_qm4d_exe = None
    if os.path.islink(qm4d_exe_sh):
        abs_qm4d_exe = os.readlink(qm4d_exe_sh)
        if shutil.which(abs_qm4d_exe) is None:
            raise Exception('qm4d is not a executable path: ', abs_qm4d_exe)
    else:
        abs_qm4d_exe = qm4d_exe_sh
    return abs_qm4d_exe


def _check_scf(qm4d_out):
    with open(qm4d_out) as f:
        flag_enter_scf = False
        flag_scf_normal = False
        for line in f:
            if (flag_enter_scf == False and line.startswith('ITER=')
                    and 'DeltaE' in line):
                flag_enter_scf = True
            if (flag_scf_normal == False and
                    line.startswith('SCF converged successfully.')):
                flag_scf_normal = True
                break
        if not flag_enter_scf:
            raise QM4D_SCFError(f'QM4D does not even enter SCF procedure. '
                                + f'Check output file "{os.path.relpath(qm4d_out)}"')
        if not flag_scf_normal:
            raise QM4D_SCFError(
                f'QM4D SCF fails. Check Output file: "{os.path.relpath(qm4d_out)}"')


def run(qm4d_exe, qm4d_inp, qm4d_out, append_out=False):
    qm4d_exe = abspath(qm4d_exe)
    cmd = '{:s} {:s} > {:s}'.format(qm4d_exe, qm4d_inp, qm4d_out)
    if append_out:
        cmd = '{:s} {:s} >> {:s}'.format(qm4d_exe, qm4d_inp, qm4d_out)
    os.system(cmd)
    if '$doqm' in Input(qm4d_inp).key_cmd():
        _check_scf(qm4d_out)


def run2(qm4d_exe, qm4d_inp, qm4d_out, append_out=False, print_err=False):
    """
    Run qm4d. Raise SCF error if qm4d encounter SCF failuar.
    """
    open_way = 'w'
    if append_out:
        open_way = 'w+'
    with open(qm4d_out, open_way) as f:
        p = Popen([qm4d_exe, qm4d_inp], stdout=f, stderr=PIPE, text=True)
        rc, err = p.communicate()
        if rc and err.strip():
            raise QM4D_RunTimeError(f'QM4D exits abnormally. Error message:\n'
                                    + f'{err}')
    if '$doqm' in Input(qm4d_inp).key_cmd():
        _check_scf(qm4d_out)


def run3(qm4d_exe, qm4d_inp, qm4d_out, append_out=False, print_err=False):
    """
    Run qm4d. Return (return_code, errmsg).
    """
    open_way = 'w'
    if append_out:
        open_way = 'w+'
    with open(qm4d_out, open_way) as f:
        rt = subprocess.run([qm4d_exe, qm4d_inp], stdout=f,
                            stderr=PIPE, text=True)
        rc, err = rt.returncode, rt.stderr
        if err.strip():
            raise QM4D_RunTimeError(f'QM4D exits abnormally. Error message:\n'
                                    + f'{err}')
        if rc and err.strip():
            raise QM4D_RunTimeError(f'QM4D exits abnormally. Error message:\n'
                                    + f'{err}')
    if '$doqm' in Input(qm4d_inp).key_cmd():
        _check_scf(qm4d_out)


if __name__ == '__main__':
    run3('qm4d_numerical_curvature', 'test.inp', 'test.out')
