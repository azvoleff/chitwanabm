@ECHO OFF
FOR /L %%n IN (1,1,5) DO (
    ECHO ------------------
    ECHO   Run number: %%n
    ECHO ------------------
    C:\Python27\python.exe runmodel.py
)
