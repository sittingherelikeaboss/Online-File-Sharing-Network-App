import os

print(os.getcwd())
os.chdir("serverdir")
list = os.listdir(os.getcwd())
