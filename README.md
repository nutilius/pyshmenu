# pyshmenu
Sample menu for shell scripts in python

Examples:


Get all java processes and go to logs subdirectory in current working directory of the process

result=$(ps -ef | grep java | awk '{ print $1, $2, $NF }' | pyshmenu.py --type value ) && result=$(echo $result | awk '{ print $2 }') && cd /proc/$result/cwd/logs
