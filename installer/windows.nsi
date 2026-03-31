; PlotBook Windows Installer Script (NSIS)

!include "MUI2.nsh"

Name "PlotBook"
OutFile "PlotBook-Setup.exe"
InstallDir "$PROGRAMFILES\PlotBook"
InstallDirRegKey HKLM "Software\PlotBook" "InstallDir"
RequestExecutionLevel admin

; UI
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"

    ; Copy all files from the PyInstaller build
    File /r "*.*"

    ; Remove the installer script itself from the install dir
    Delete "$INSTDIR\installer.nsi"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\PlotBook"
    CreateShortCut "$SMPROGRAMS\PlotBook\PlotBook.lnk" "$INSTDIR\PlotBook.exe"
    CreateShortCut "$SMPROGRAMS\PlotBook\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

    ; Desktop shortcut
    CreateShortCut "$DESKTOP\PlotBook.lnk" "$INSTDIR\PlotBook.exe"

    ; Registry for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlotBook" \
        "DisplayName" "PlotBook"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlotBook" \
        "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlotBook" \
        "DisplayVersion" "0.1.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlotBook" \
        "Publisher" "PlotBook"
    WriteRegStr HKLM "Software\PlotBook" "InstallDir" "$INSTDIR"

    ; Register .plotbook file association
    WriteRegStr HKCR ".plotbook" "" "PlotBook.Project"
    WriteRegStr HKCR "PlotBook.Project" "" "PlotBook Project"
    WriteRegStr HKCR "PlotBook.Project\shell\open\command" "" "$\"$INSTDIR\PlotBook.exe$\" $\"%1$\""
SectionEnd

Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    RMDir /r "$SMPROGRAMS\PlotBook"
    Delete "$DESKTOP\PlotBook.lnk"

    ; Remove registry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlotBook"
    DeleteRegKey HKLM "Software\PlotBook"
    DeleteRegKey HKCR ".plotbook"
    DeleteRegKey HKCR "PlotBook.Project"
SectionEnd
