# preparation
* install ubuntu22.04.02 VM
* install python3.11 on ubuntu
``` shell
    $sudo apt update -y && sudo apt upgrade -y
    $sudo add-apt-repository ppa:deadsnakes/ppa -y
    $sudo apt update -y
    $sudo apt install python3.11 -y
    
```
* change default python3 version to python3.11
``` shell
    $cd /usr/bin
    $sudo unlink python3
    $sudo ln -s /usr/bin/python3.11 python3
    $ls -la python3*  //check python3 link
        lrwxrwxrwx 1 root root      19 Oct 10 18:50 python3 -> /usr/bin/python3.11
        -rwxr-xr-x 1 root root 5909000 Sep 11 15:47 python3.10
        -rwxr-xr-x 1 root root 6724632 Sep  7 18:35 python3.11
    $sudo apt install python3-pip -y
```
* install poetry
```shell
    $python3 -m pip install poetry 
```
* close the terminal window and then start a new terminal window
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
