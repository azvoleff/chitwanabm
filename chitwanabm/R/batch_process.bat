echo off
REM Copyright 2008-2012 Alex Zvoleff
REM
REM This file is part of the chitwanabm agent-based model.
REM 
REM chitwanabm is free software: you can redistribute it and/or modify it under the
REM terms of the GNU General Public License as published by the Free Software
REM Foundation, either version 3 of the License, or (at your option) any later
REM version.
REM 
REM chitwanabm is distributed in the hope that it will be useful, but WITHOUT ANY
REM WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
REM PARTICULAR PURPOSE.  See the GNU General Public License for more details.
REM 
REM You should have received a copy of the GNU General Public License along with
REM chitwanabm.  If not, see <http://www.gnu.org/licenses/>.
REM
REM See the README.rst file for author contact information.

set R_BIN="C:\Program Files\R\R-2.15.2\bin\x64\Rscript.exe"
set SCRIPT_PATH=C:\Users\azvoleff\Code\Python\chitwanabm\chitwanabm\R

set DATA_PATH=%1

call %R_BIN% "%SCRIPT_PATH%\batch_calculations.R" %DATA_PATH%
call %R_BIN% "%SCRIPT_PATH%\batch_plots.R" %DATA_PATH%
