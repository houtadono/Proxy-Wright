[Setup]
AppId={{B8F3B8A4-8B5B-4B26-9E0D-4E7F2E9C6A31}}
AppName=ProxyWright
AppVersion={#AppVersion}
AppVerName=ProxyWright {#AppVersion}
SetupIconFile=assets\app.ico
DefaultDirName={autopf}\ProxyWright
DefaultGroupName=ProxyWright
OutputDir=output
OutputBaseFilename=ProxyWright-Setup-{#Tag}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=yes
AppMutex=ProxyWrightMutex
DisableDirPage=no
UsePreviousAppDir=no
UninstallDisplayIcon={app}\ProxyWright.exe
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Files]
Source: "dist\ProxyWright\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "dist\Updater.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\installed.marker"; DestDir: "{app}"; DestName: ".installed"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Tạo shortcut trên Desktop"; GroupDescription: "Tuỳ chọn:"; Flags: unchecked

[Icons]
Name: "{group}\ProxyWright"; Filename: "{app}\ProxyWright.exe"
Name: "{userdesktop}\ProxyWright"; Filename: "{app}\ProxyWright.exe"; Tasks: desktopicon

; [UninstallDelete]
; Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\ProxyWright.exe"; Description: "Khởi động ProxyWright"; Flags: nowait postinstall skipifsilent