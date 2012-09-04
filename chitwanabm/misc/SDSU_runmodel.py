"""
Script used to simplify running the chitwanabm on SDSU lab computers. Sets up 
the python and system paths so the model can find all the required 
dependencies.
"""

import os
import sys

def main():
    # First setup system path
    os.environ['PATH'] = "Z:\\Programs\GDAL;Z:\\Python_Local_64bit\Scripts;" + os.environ['PATH']

    # Now setup python path
    oldpaths = sys.path
    sys.path = ["Z:\\Python_Local_64bit\site-packages", "Z:\\Code", 
                "Z:\\Python_Local_64bit\Scripts"]
    sys.path.extend(oldpaths)

    import chitwanabm.runmodel

    chitwanabm.runmodel.main()

if __name__ == "__main__":
    sys.exit(main())
