# Copyright 2011 Alex Zvoleff
#
# This file is part of the ChitwanABM agent-based model.
# 
# ChitwanABM is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# ChitwanABM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# ChitwanABM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

###############################################################################
# Loads the CVFS data and prints summary info about several people, households, 
# and neighborhoods that is used by the test.py script to verify the operation 
# of the ChitwanABM model.
###############################################################################

library("foreign")
census <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0004_REST.xpt")
hhrel <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0016_REST.xpt")
hhag <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0002_REST.xpt")
neigh <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0014_REST.xpt")

# Pull out an entire household to test how the agents are read in to the model
# Use HHID=905 (a random household)
census$CENGENDR[census$CENGENDR==1] <- "male"
census$CENGENDR[census$CENGENDR==2] <- "female"
census.hh <- census[which(census$HHID=="905"),]
# Convert ages expressed in years to ages in months, as used in the model
AGEMNTHS <- census.hh$CENAGE*12
census.hh <- with(census.hh, data.frame(RESPID, CENAGE, AGEMNTHS, CENGENDR))

hhrel.hh <- hhrel[which(hhrel$HHID=="905"),]
hhrel.hh <- with(hhrel.hh, data.frame(RESPID, SUBJECT, PARENT1, PARENT2, SPOUSE1, SPOUSE2, SPOUSE3))

hh <- merge(hhrel.hh, census.hh, by="RESPID")
