
import os
import sys
import copy


class CommandLine:
    """
    QM4D style command line. It is always separated by whitespace.

    -----------
    Examples
    'xyz mol.xyz': 'xyz' is the cmd key, and 'mol.xyz' is the cmd value.
    """

    def __init__(self, cmd_str):
        self._cmd = cmd_str.strip().split()

    def __str__(self):
        return ' '.join(self._cmd)

    def __repr__(self):
        return self.__str__()

    def _index(self, key, step=1) -> int:
        """
        Return the index of command value based on command key and step.
        """
        try:
            key = key.strip()
            idx = self._cmd.index(key) + step
            self._cmd[idx]
            return idx
        except ValueError:
            raise ValueError(f'{key} is not in command line.')
        except IndexError:
            raise IndexError(
                f'Index is out of command line\'s range: {idx} vs {len(self._cmd)}')

    def copy(self) -> 'CommandLine':
        return CommandLine(self.to_str())

    def get(self, key, step=1) -> str:
        """
        Get value from the cmd.

        -----------
        Parameters
        key: str
            the comand key.
        step: int, default 1.
            Get the command value from the index of command key with number of
            steps `step`.

        -----------
        Return str
            The raw and striped string for the command value.
        """
        idx = self._index(key, step=step)
        return self._cmd[idx]

    def to_str(self) -> str:
        return ' '.join(self._cmd)

    def update(self, key, value, step=1) -> 'self':
        """
        Update the value from the cmd based on command key and step.

        -----------
        Parameters
        key: str
            the comand key.
        value: str
            the new comand value.
        step: int, default 1.
            Get the command value from the index of command key with number of
            steps `step`.

        -----------
        Return self
        """
        idx = self._index(key, step=step)
        self._cmd[idx] = value.strip()
        return self


class Input:
    """
    QM4D style input

    A block of command starts with "$cmd_block_name", where "cmd_block_name"
    is the command block name, such as '$qm', '$doqm' and so on. Usually the
    block of command will end with keyword "end".
    """

    def __init__(self, inp=''):
        self._path = inp
        # record key commands' order
        self._key_cmd_name = []
        # dict: (str, list of str) = (key_cmd, command block)
        self._key_cmd_block = {}
        if self._path:
            if not os.path.isfile(self._path):
                raise Exception(f'Input "{inp}"is not a file.')
            with open(self._path) as f:
                raw_cmd = [line.strip() for line in f.readlines()]
                key_cmd_idx = [i for i, cmd in enumerate(raw_cmd)
                               if cmd.startswith(r'$')]
                self._key_cmd_name, self._key_cmd_block = self._split(
                    raw_cmd, key_cmd_idx)
            for key, _ in self._key_cmd_block.items():
                self._key_cmd_block[key].pop(0)

    def __str__(self):
        inp = ''
        for name in self._key_cmd_name:
            block = self._key_cmd_block[name]
            new_block = [i + '\n' for i in block]
            inp += f'{name}\n' + ''.join(new_block)
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

    def copy(self):
        other = Input()
        other._path = self._path
        other._key_cmd_name = copy.deepcopy(self._key_cmd_name)
        other._key_cmd_block = copy.deepcopy(self._key_cmd_block)
        return other

    def replace_line(self, key_cmd, line, new_line) -> int:
        """
        Replace matched line in the input file in place.

        -----------
        Parameters
        key_cmd: str
            QM4D key command name, such as '$qm', '$doqm'.
            This makes the replacement for the specified key command blocks.
            If `key_cmd == 'all'`, the replacement will be applied to the whole
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
        key_cmd = self._key_cmd_name if key_cmd == 'all' else [key_cmd.strip()]
        line_s = line.strip().split()
        new_line = new_line.strip()
        n = 0
        for key in key_cmd:
            block_cmd = self._key_cmd_block[key]
            for i, cmd_line in enumerate(block_cmd):
                if self._array_startswith(cmd_line.split(), line_s):
                    block_cmd[i] = new_line
                    n += 1
        return n

    def find(self, key_cmd, pattern) -> list:
        """
        Find the matched input line based on pattern.

        The `pattern.split()` is used for searching.
        See `self._array_startswith()`.

        -----------
        Parameter
        key_cmd: str
            QM4D key command, such as '$qm'. If `key_cmd == 'all'`, the search
            will be applied to the whole input.
        pattern: str
            The search pattern.

        -----------
        Return list
            The list of matched input line.
        """
        rst = []
        key_cmd = self._key_cmd_name if key_cmd == 'all' else [key_cmd.strip()]
        parrtern_s = pattern.strip().split()
        for key in key_cmd:
            block_cmd = self._key_cmd_block[key]
            for _, cmd_line in enumerate(block_cmd):
                if self._array_startswith(cmd_line.split(), parrtern_s):
                    rst.append(cmd_line)
        return rst

    def find_first(self, key_cmd, pattern) -> str:
        """
        Find the first matched input line based on pattern.

        The `pattern.split()` is used for searching.
        See `self._array_startswith()`.

        -----------
        Parameter
        key_cmd: str
            QM4D key command, such as '$qm'. If `key_cmd == 'all'`, the search
            will be applied to the whole input.
        pattern: str
            The search pattern.

        -----------
        Return str
            The matched input line.
        """
        find = self.find(key_cmd, pattern)
        if not find:
            raise ValueError(
                f'No matched line found from input. Pattern: {pattern}')
        else:
            return find[0]

    def find_last(self, key_cmd, pattern) -> str:
        """
        Find the last matched input line based on pattern.

        The `pattern.split()` is used for searching.
        See `self._array_startswith()`.

        -----------
        Parameter
        key_cmd: str
            QM4D key command, such as '$qm'. If `key_cmd == 'all'`, the search
            will be applied to the whole input.
        pattern: str
            The search pattern.

        -----------
        Return str
            The matched input line.
        """
        find = self.find(key_cmd, pattern)
        if not find:
            raise ValueError(
                f'No matched line found from input. Pattern: {pattern}')
        else:
            return find[-1]

    def insert(self, key_cmd, cmd, position='end') -> 'self':
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
        key_cmd = key_cmd.strip()
        cmd = cmd.strip()
        if key_cmd not in self._key_cmd_block.keys():
            self._key_cmd_block[key_cmd] = [cmd]
            self._key_cmd_name.append(key_cmd)
            return self

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

        return self

    def delete_line(self, key_cmd, cmd) -> int:
        """
        Delete a line of command in a key command block.

        -----------
        Parameter
        key_cmd: str
            QM4D key command, such as '$qm'. If `key_cmd == 'all'`, the deletion
            will be applied to the whole input.
        cmd: str
            The command to be deleted.

        -----------
        Retrun int
            The number of deletion.
        """
        key_cmd = self._key_cmd_name if key_cmd == 'all' else [key_cmd.strip()]
        cmd_s = cmd.strip().split()
        n = 0
        for key in key_cmd:
            cmd_block = self._key_cmd_block[key]
            new_cmd_block = []
            for _, cmd_line in enumerate(cmd_block):
                if not self._array_startswith(cmd_line.split(), cmd_s):
                    new_cmd_block.append(cmd_line)
                else:
                    n += 1
            self._key_cmd_block[key] = new_cmd_block
        return n

    def delete_block(self, key_cmd) -> 'self':
        """
        Delete the whole key command block.

        -----------
        Parameter
        key_cmd: str
            QM4D key command, such as '$qm'.
        """
        del self._key_cmd_block[key_cmd.strip()]
        self._key_cmd_name.remove(key_cmd.strip())
        return self

    def to_inp(self, file_name):
        """
        Write input content into a file.
        """
        with open(file_name, 'w') as f:
            f.write(self.__str__())

    def print(self):
        print(self.__str__())

    def path(self) -> str:
        return self._path

    def abspath(self) -> str:
        return os.path.abspath(self._path)
