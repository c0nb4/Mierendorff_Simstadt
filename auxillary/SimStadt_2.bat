@ECHO OFF
REM --- UTF-8 Ausgabe aktivieren ---
chcp 65001 >nul

REM --- Zum Ordner des Skripts wechseln ---
cd /D "%~dp0"

REM --- Arbeitsspeicherbegrenzung setzen ---
set "maxRAM=2g"
set "startRAM=512m"

REM --- Pfad zur Java-Installation explizit setzen ---
set "JAVA_EXE=C:\Program Files\BellSoft\LibericaJDK-8-Full\bin\java.exe"

REM --- Classpath mit SimStadt-Bibliotheken ---
set "CLASSPATH=lib/*;workflows/*"

REM --- Java-Optionen vorbereiten ---
set "JAVA_OPTS=-Xms%startRAM% -Xmx%maxRAM% -Djava.util.logging.config.file=logging.properties -Dfile.encoding=UTF-8"

REM --- Optional: ControlsFX JavaFX-Module exportieren (nur falls nötig) ---
REM set "JAVA_OPTS=%JAVA_OPTS% --add-exports=javafx.base/com.sun.javafx.runtime=ALL-UNNAMED"

REM --- Optional: Sprach- und Ländereinstellungen für CSV-Ausgabe ---
REM set "JAVA_OPTS=%JAVA_OPTS% -Duser.language=en -Duser.country=US"

REM --- Anwendung starten ---
if "%~1"=="" (
    ECHO Launching: "%JAVA_EXE%" %JAVA_OPTS% -classpath "%CLASSPATH%" eu.simstadt.desktop.SimStadtApp
    "%JAVA_EXE%" %JAVA_OPTS% -classpath "%CLASSPATH%" eu.simstadt.desktop.SimStadtApp
) ELSE (
    ECHO Launching: "%JAVA_EXE%" %JAVA_OPTS% -classpath "%CLASSPATH%" eu.simstadt.desktop.SimStadtCommandLineInterface "%~1"
    "%JAVA_EXE%" %JAVA_OPTS% -classpath "%CLASSPATH%" eu.simstadt.desktop.SimStadtCommandLineInterface "%~1"
)

pause
