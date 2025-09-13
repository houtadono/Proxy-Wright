[Setup]
AppId={{B8F3B8A4-8B5B-4B26-9E0D-4E7F2E9C6A31}}     ; giữ cố định!
SetupIconFile=assets\app.ico
AppName=ProxyWright
AppVersion={#AppVersion}
AppVerName=ProxyWright
DefaultDirName={pf}\ProxyWright
DefaultGroupName=ProxyWright
OutputDir=output
OutputBaseFilename=ProxyWright-Setup-{#Tag}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=yes
AppMutex=ProxyWrightMutex

[Files]
Source: "dist\ProxyWright\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "assets\installed.marker"; DestDir: "{app}"; DestName: ".installed"; Flags: ignoreversion

[Icons]
Name: "{group}\ProxyWright"; Filename: "{app}\ProxyWright.exe"
Name: "{userdesktop}\ProxyWright"; Filename: "{app}\ProxyWright.exe"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\ProxyWright.exe"; Description: "Khởi động Proxy Profile Manager"; Flags: nowait postinstall skipifsilent