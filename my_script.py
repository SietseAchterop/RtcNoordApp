
import os, sys, time, shlex

def main():
    print("Main was here!")
    print(os.getcwd())
    print(os.getenv("PATH"))
    print(os.system('df'))
    print(os.system('ls -l /'))
    print(os.system('env'))
    print('=========')
    print(os.system('traceroute www.rug.nl'))
    print('=========')
    print(os.system('sleep(60)'))
          
main()

