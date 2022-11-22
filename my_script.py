
import os, sys, time, shlex

def main():
    print("Main was here!")
    print(os.getcwd())
    print(os.getenv("PATH"))
    print(os.system('df'))
    print(os.system('ls -l /'))
    print(os.system('env'))
    print('=========')
    print(os.system('stress --cpu 2 --vm-bytes 128M --timeout 60s'))
    print('=========')
          
main()

