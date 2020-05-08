import os
import sys

def get_abs_dir():
  return os.path.abspath(os.path.dirname(sys.argv[0]))

def main():
  return 0

if __name__ == "__main__":
  main()