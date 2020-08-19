
import os
import sys
import copy


class Input:
    """
    QM4D style input

    A block of command starts with "$cmd_block_name", where "cmd_block_name"
    is the command block name, such as '$qm', '$doqm' and so on. Usually the
    block of command will end with keyword "end".
    """

    def __init__(self, inp=''):
        self._path = inp
        self._key_cmd_name = []
        self._key_cmd_block = {}
        if self._path:
            if not os.path.isfile(self._path):
                raise Exception(f'Input "{inp}"is not a file.')
            with open(self._path) as f:
                raw_cmd = [line.strip() for line in f.readlines()]
                key_cmd_idx = [i for i, cmd in enumerate(raw_cmd)
                               if cmd.startswith(r'$')]
                self._key_cmd_name, self._key_cmd_block = self._split(raw_cmd,
                                                                      key_cmd_idx)

    def __str__(self):
        inp = ''
        for name in self._key_cmd_name:
            block = self._key_cmd_block[name]
            new_block = [i + '\n' for i in block]
            inp += ''.join(new_block)
        return inp

    def __repr__(self):
        return self.__str__()

    def _split(self, array, index):
        new_idx = index + [len(array)]
        names = []
        blocks = {}
        for i in range(len(index)):
            block = array[new_idx[i]: new_idx[i+1]]
            name = array[new_idx[i]]
            names.append(name)
            blocks[name] = block
        return names, blocks

    def copy(self):
        other = Input()
        other._path = self._path
        other._key_cmd_name = copy.deepcopy(self._key_cmd_name)
        other._key_cmd_block = copy.deepcopy(self._key_cmd_block)
        return other

    def _array_startswith(self, array, sub_array):
        l1 = len(array)
        l2 = len(sub_array)
        if l1 < l2:
            return False
        else:
            flag = True
            for i in range(l2):
                flag = (flag and (array[i] == sub_array[i]))
            return flag

    def replace_line(self, line, new_line, key_cmd='') -> int:
        """
        Replace matched line in the input file in place.

        -----------
        Parameters
        key_cmd: str, default ''.
            QM4D key command name, such as '$qm', '$doqm'.
            This makes the replacement for the specified key command blocks.
            If `key_cmd == ''`, the replacement will be applied to the whole
            input.
        line: str
            original input line starts with `line.split()`.
        new_line: str
            The line used for replacement.

        -----------
        Note
        The `line.split()` is used as the pattern to find all lines in the
        searching block. See also `self._array_startswith()`.

        -----------
        Return int
            The number of replacement.
        """
        key_cmd = key_cmd.split()
        if not key_cmd:
            key_cmd = self._key_cmd_name
        n = 0
        for key in key_cmd:
            block_cmd = self._key_cmd_block[key]
            line_s = line.split()
            for i, cmd_line in enumerate(block_cmd):
                cmd_line_s = cmd_line.split()
                if self._array_startswith(cmd_line_s, line_s):
                    block_cmd[i] = new_line
                    n += 1
        return n

    def find(self, parttern, key_cmd='') -> list:
        """
        Find the matched input line based on parttern.

        The `parttern.split()` is used for searching.
        See `self._array_startswith()`.

        -----------
        Parameter
        key_cmd: str
            QM4D key command, such as '$qm'.
        parttern: str
            The search parttern.

        -----------
        Return list
            The list of matched input line.
        """
        rst = []
        key_cmd = key_cmd.split()
        if not key_cmd:
            key_cmd = self._key_cmd_name
        for key in key_cmd:
            block_cmd = self._key_cmd_block[key]
            parrtern_s = parttern.split()
            for i, cmd_line in enumerate(block_cmd):
                cmd_line_s = cmd_line.split()
                if self._array_startswith(cmd_line_s, parrtern_s):
                    rst.append(cmd_line)
        return rst

    def insert(self, key_cmd, cmd, position='end'):
        """
        -----------
        Parameter
        key_cmd: str
            QM4D key command, such as '$qm'.
        cmd: str
            The new command to be inserted.
        position: str, ['head', 'end', other_string]. Default is 'end'.
            'head': insert after the `key_cmd`.
            'end': insert before the end of the key command block.
            other_string: use other_string to find the matched line. Then
                insert the new command after the matched line.
        """
        block_cmd = self._key_cmd_block[key_cmd]
        idx = -1
        if position == 'head':
            idx = 1
        elif position == 'end':
            try:
                idx = block_cmd.index('end')
            except ValueError:
                idx = len(block_cmd)
        else:
            flag = False
            for i, line in enumerate(block_cmd):
                if self._array_startswith(line.split(), position.split()):
                    idx = i + 1
                    flag = True
                    break
            if not flag:
                raise ValueError(
                    f'No matching position found based on {position}')
        block_cmd.insert(idx, cmd)

    def to_inp(self, file_name):
        """
        Write input content into a file.
        """
        with open(file_name, 'w') as f:
            f.write(self.__str__())

    def print(self):
        print(self.__str__())

    def path(self):
        return self._path

    def abspath(self):
        return os.path.abspath(self._path)
