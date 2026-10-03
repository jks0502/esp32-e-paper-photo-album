@echo off
setlocal
cd /d "%~dp0.."
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "FRAME_VS=%%i"
if not defined FRAME_VS (
  echo Microsoft C++ Build Tools not found.
  exit /b 1
)
call "%FRAME_VS%\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
if not exist build\host mkdir build\host
for %%v in (1 2) do (
  cl /nologo /std:c++17 /EHsc /W3 /utf-8 /DFRAME_PANEL_VERSION=%%v /Itests\mocks /Ifirmware\CoupleFrame\src\waveshare /TP firmware\CoupleFrame\CoupleFrame.ino firmware\CoupleFrame\Photos.cpp firmware\CoupleFrame\src\waveshare\DEV_Config.cpp firmware\CoupleFrame\src\waveshare\EPD_4in2.cpp firmware\CoupleFrame\src\waveshare\EPD_4in2_V2.cpp tests\test_firmware.cpp /Febuild\host\panel%%v.exe /Fobuild\host\ > build\host\compile-panel%%v.log 2>&1
  if errorlevel 1 (
    type build\host\compile-panel%%v.log
    exit /b 1
  )
  build\host\panel%%v.exe
  if errorlevel 1 exit /b 1
)

