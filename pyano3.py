#!/usr/bin/python

# this is the __main__ python code.  run "python pyano3.py" to get game a-going.
from game import *

# define a main function
def main():
    game = GameClass()
    game.mainloop()

# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__=="__main__":
    # call the main function
    main()

