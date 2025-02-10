# setup project environment at vscode on ubuntu VM

* remote explorer -> add new SSH
* vscode install Python and python Debugger extensions
* open terminal in vscode, run make install, it will install all python dependencies
* open VSCode, Command Palette-> Python: Create Environment -> choose Venv -> choose use existing venv

# setup project environment at vscode on Windows( it also work for linux and Macbook)
* remove ./.venv/ folder if exist
* vscode install Python and python Debugger extensions
* Command Palette-> Python: Create Environment -> VEnv -> choose Python version 3.11
* vscode choose new terminal -> choose Command Prompt, and it will start with (.venv) as below shows
    * ``` (.venv) C:\xxx\python_5gtoolbox  ```
    *  do not choose PowerShell which didn't work
    
* check python version to be selected python3 version 
    * ``` python --version ```
* install poetry
    * ```python -m pip install poetry```
* run below poetry cli 
    * ```poetry config virtualenvs.in-project true```
    * ```poetry install```

# how to debug files on Windows
* vscode click `Run and Debug`
* choose `Python: poetry run Current File under Windows` 

# how to debug files on linux and Macbook
* vscode click `Run and Debug`
* choose `Python: poetry run Current File under Linux` 

# how to solve VS Code Debugger not working for python issue
* the issue is:
    * Clicking on "Run Python File" works fine. Clicking on "Debug Python File" now does nothing. 
    Run->"start Debugging' no command comes to terminal

* the solution:
    * removing ./venv/ and ./.venv/ in my working directory
    * recreate the virtual environment
    * run my debug launch config specified in ./.vscode/launch.json (via F5)
    * redirect missing python interpreter path to the one specified in the venv

