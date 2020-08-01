class NoResultsFoundFromOutput(Exception):
    def __init__(self, output, start, message):
        self.output = output
        self.start = start
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return (f'\nError type: {self.__class__.__name__}\n' +
                f'Output file: {self.output}\n'
                + f'File starting position of searching: {self.start}\n' +
                f'Error message: {self.message}')


class UnexpectedOutputFormat(Exception):
    def __init__(self, output, message):
        self.output = output
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return (f'\nError type: {self.__class__.__name__}\n' +
                f'Output file: {self.output}\n'
                + f'Unexpected output format to look up results.\n' +
                f'Error message: {self.message}')
