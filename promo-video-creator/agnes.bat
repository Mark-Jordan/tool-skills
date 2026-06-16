@echo off
REM Agnes API wrapper for Windows — ensures Chinese/CJK characters are handled correctly.
REM Usage: agnes.bat image --prompt "中文提示词" --size 1920x1080 --out output.png
REM
REM Without PYTHONUTF8=1, Chinese prompts passed via CLI will be garbled (mojibake)
REM and the generated images will be unrelated to the intended prompt.

set PYTHONUTF8=1
python "%~dp0scripts\agnes_api.py" %*
