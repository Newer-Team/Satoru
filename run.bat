@ECHO OFF

echo(
echo Requirements:
echo - Python 3.5, with its directory in the system PATH
echo - Pillow and PyQt5 for Python 3
echo - AMD Compress v2.2
echo(
echo Enjoy!

goto :srslygoaway

:choice
set /P c=Do you want to download the latest spritedata.xml [Y/N]?
if /I "%c%" EQU "Y" goto :downloadthatstuff
if /I "%c%" EQU "N" goto :nogoaway
goto :choice


:downloadthatstuff

@echo OFF
echo Downloading latest spritedata...
powershell -Command "Invoke-WebRequest http://rhcafe.us.to/spritexml.php -OutFile satorudata/spritedata.xml"
echo Done!

:nogoaway
set /P c=Do you want to download the latest category.xml [Y/N]?
if /I "%c%" EQU "Y" goto :downloadthatxml
if /I "%c%" EQU "N" goto :srslygoaway
goto :nogoaway

:downloadthatxml

@echo OFF
echo Downloading latest spritecategories...
powershell -Command "Invoke-WebRequest http://rhcafe.us.to/categoryxml.php -OutFile satorudata/spritecategories.xml"
echo Done!
echo Starting Satoru!
cmd /k python satoru.py

:srslygoaway
@echo OFF
echo Starting Satoru!
cmd /k python satoru.py