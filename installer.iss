#define VN_ISL_LOCAL "assets\innosetup\Vietnamese.isl"
#define VN_ISL_COMPILER AddBackslash(CompilerPath) + "Languages\Unofficial\Vietnamese.isl"
#if FileExists(VN_ISL_COMPILER)
  #define VN_ISL "compiler:Languages\Unofficial\Vietnamese.isl"
#else
  #define VN_ISL VN_ISL_LOCAL
#endif


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


ShowLanguageDialog=yes
UsePreviousLanguage=yes
LanguageDetectionMethod=uilanguage

[Languages]
Name: "english";    MessagesFile: "compiler:Default.isl"
#if FileExists("assets\innosetup\Vietnamese.isl")
  Name: "vietnamese"; MessagesFile: "assets\innosetup\Vietnamese.isl"
#else
  #pragma message "Vietnamese.isl not found – building EN-only installer"
#endif

[CustomMessages]
english.Options=Options:
vietnamese.Options=Tuỳ chọn:

english.DesktopShortcut=Create Desktop shortcut
vietnamese.DesktopShortcut=Tạo lối tắt trên Desktop

english.LaunchApp=Launch ProxyWright
vietnamese.LaunchApp=Khởi động ProxyWright

english.LangCode=en
vietnamese.LangCode=vi

[Files]
Source: "dist\ProxyWright\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "dist\Updater.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\installed.marker"; DestDir: "{app}"; DestName: ".installed"; Flags: ignoreversion

[Dirs]
Name: "{localappdata}\ProxyWright"; Flags: uninsneveruninstall

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"; GroupDescription: "{cm:Options}"; Flags: unchecked

[Icons]
Name: "{group}\ProxyWright";       Filename: "{app}\ProxyWright.exe"
Name: "{userdesktop}\ProxyWright"; Filename: "{app}\ProxyWright.exe"; Tasks: desktopicon

; [UninstallDelete]
; Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\ProxyWright.exe"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent

[Code]
function GetSelectedLangCode(): string;
begin
  Result := ExpandConstant('{cm:LangCode}');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  IniFile, Existing, LangCode, SettingsDir: string;
begin
  if CurStep = ssPostInstall then
  begin
    SettingsDir := ExpandConstant('{localappdata}\ProxyWright');
    if not DirExists(SettingsDir) then
      ForceDirectories(SettingsDir);

    IniFile := SettingsDir + '\settings.ini';
    LangCode := GetSelectedLangCode();
    Existing := GetIniString('general', 'language', '', IniFile);
    if Existing = '' then
      SetIniString('general', 'language', LangCode, IniFile);
  end;
end;
