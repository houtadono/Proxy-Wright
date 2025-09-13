[Setup]
SetupIconFile=assets\app.ico
AppName=ProxyWright
AppVersion=1.0.0
AppVerName=ProxyWright
DefaultDirName={pf}\ProxyWright
DefaultGroupName=ProxyWright
OutputDir=output
OutputBaseFilename=ProxyWright-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\ProxyWright\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\ProxyWright"; Filename: "{app}\ProxyWright.exe"
Name: "{commondesktop}\ProxyWright"; Filename: "{app}\ProxyWright.exe"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\ProxyWright.exe"; Description: "Khởi động Proxy Profile Manager"; Flags: nowait postinstall skipifsilent