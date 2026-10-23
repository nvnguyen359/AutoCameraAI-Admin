[Setup]
AppName=AutoCameraAI-Admin
AppVersion=1.0.0
AppPublisher=AutoCameraAI
DefaultDirName={autopf}\AutoCameraAI-Admin
DefaultGroupName=AutoCameraAI-Admin
OutputDir=.\Output
OutputBaseFilename=AutoCameraAI_Admin_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình (Desktop)"; GroupDescription: "Additional icons:"
Name: "startupicon"; Description: "Khởi động cùng Windows"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\AutoCameraAI-Admin\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AutoCameraAI-Admin"; Filename: "{app}\AutoCameraAI-Admin.exe"
Name: "{autodesktop}\AutoCameraAI-Admin"; Filename: "{app}\AutoCameraAI-Admin.exe"; Tasks: desktopicon
Name: "{userstartup}\AutoCameraAI-Admin"; Filename: "{app}\AutoCameraAI-Admin.exe"; Parameters: "--minimized"; Tasks: startupicon

[Run]
Filename: "{app}\AutoCameraAI-Admin.exe"; Description: "Khởi chạy AutoCameraAI-Admin ngay"; Flags: nowait postinstall skipifsilent
Filename: "{app}\AutoCameraAI-Admin.exe"; Flags: nowait skipifnotsilent
