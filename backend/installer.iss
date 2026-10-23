#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{8E94A2F1-6C4D-4E3A-9B7D-2F1E5A8C3D90}
AppName=AutoCameraAI-Admin
AppVersion={#MyAppVersion}
AppPublisher=AutoCameraAI
DefaultDirName={autopf}\AutoCameraAI-Admin
DefaultGroupName=AutoCameraAI-Admin
OutputDir=..\Output
OutputBaseFilename=AutoCameraAI_Admin_Setup
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
CloseApplications=force
CloseApplicationsFilter=*.exe
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình (Desktop)"; GroupDescription: "Tùy chọn bổ sung:"
Name: "startupicon"; Description: "Khởi động cùng Windows"; GroupDescription: "Tùy chọn bổ sung:"

[Files]
Source: "dist\AutoCameraAI-Admin\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs restartreplace

[InstallDelete]
Type: files; Name: "{app}\client\browser\chunk-*.js"
Type: files; Name: "{app}\client\browser\main-*.js"
Type: files; Name: "{app}\client\browser\styles-*.css"
Type: files; Name: "{app}\client\chunk-*.js"
Type: files; Name: "{app}\client\main-*.js"
Type: files; Name: "{app}\client\styles-*.css"

[Icons]
Name: "{group}\AutoCameraAI-Admin"; Filename: "{app}\AutoCameraAI-Admin.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\AutoCameraAI-Admin"; Filename: "{app}\AutoCameraAI-Admin.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\AutoCameraAI-Admin"; Filename: "{app}\AutoCameraAI-Admin.exe"; Parameters: "--silent"; WorkingDir: "{app}"; Tasks: startupicon

[Run]
Filename: "{app}\AutoCameraAI-Admin.exe"; Description: "Khởi chạy AutoCameraAI-Admin ngay"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\AutoCameraAI-Admin.exe"; WorkingDir: "{app}"; Flags: nowait skipifnotsilent
