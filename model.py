#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Contains main model loop: Contains the main loop for the model. Takes input 
parameters read from runModel.py, and passes results of model run back.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

def main(modelRun):
    for person in modelRun.persons():
        person.Survive()
