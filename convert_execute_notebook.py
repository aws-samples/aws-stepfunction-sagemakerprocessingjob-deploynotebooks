# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Author - Govindhi Venkatachalapathy <govindhi@amazon.com>
import os
import nbformat
import sys
import argparse
from nbconvert import PythonExporter
from subprocess import run, PIPE
 
NOTEBOOK_SRC_DIR = './src/notebooks'
 
def convert_and_execute_notebook_to_python():
    nb = None
    output = ''
    rc = None
    with open(os.path.join(NOTEBOOK_SRC_DIR, args.notebookname)) as fh:
        nb = nbformat.reads(fh.read(), nbformat.NO_CONVERT)
    exporter = PythonExporter()
    source, meta = exporter.from_notebook_node(nb)
    source = source.replace("%config Completer.use_jedi = False", "# %config Completer.use_jedi = False")
    source = source.replace("get_ipython().", "# get_ipython().")
    # Get the converted python script name from notebook name
    python_script_path = os.path.join(NOTEBOOK_SRC_DIR, '%s.py' %os.path.splitext(args.notebookname)[0])
    with open(python_script_path, 'w+') as fh:
        fh.writelines(source)
    # Execute the converted python script
    result = run([sys.executable, python_script_path], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    output = result.stdout
    if result.returncode != 0:
        output += result.stderr
    return result.returncode, output
 
if __name__ == '__main__':
    parser = parser = argparse.ArgumentParser(description='Convert and Execute Jupyter notebook')
    parser.add_argument('-n', '--notebookname', required=True, help='Notebook name')
    args = parser.parse_args()
 
    rc, output = convert_and_execute_notebook_to_python()
    print("Return code:%s" %rc)
    print("Execution Output:%s" %output)
    if rc == 0:
        sys.exit(0)
    else:
        sys.exit(1)
