# preparation
install py5gphy toolbox on macbook pro with Apple M1 chipset
* install python3.11
    * download python3.11.9 image from https://www.python.org/downloads/macos/ and then install it
    * restart terminal or start a new terminal
    * check python3 version
    ```shell
        % python3 --version
        > Python 3.11.9
        %  pip3 install --upgrade pip
    ```
* install poetry
```shell
    % python3 -m pip install poetry
```
* clone py5gphy project from github   
    Personal access tokens (classic) may need be generated to access git clone
```shell
    $git clone https://github.com/hahaliu2001/python_5gtoolbox.git 
```
# run the project
* create venv and then run the test
```shell
    $cd python_5gtoolbox
    $make install  //it will install packages into venv
    $make test  //run all the testcases 
```
* clean the environment
```shell
    $make clean
```

* gitpush the code
```shell
    $make gitpush
```