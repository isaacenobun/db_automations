Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\Scripts\cpu_monitor.bat" & chr(34), 0
Set WshShell = Nothing