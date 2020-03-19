import os
import sys
import fileinput
import subprocess

file_name = sys.argv[1]

for line in fileinput.FileInput(file_name, inplace=1):
    if '.. auto-generated code for' in line:
        line = line.replace('.. auto-generated code for ', '')

        command, argument, *_ = line.split()

        command_result = subprocess.check_output([command, argument])
        command_result = command_result.decode("utf-8")
        command_result = command_result.replace('\\n', '\n')

        line = command_result
        line = '.. code-block:: bash\n\n' + line
        line = '\t'.join(line.splitlines(True))
    print(line, end='')
