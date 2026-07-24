; Instalador de BGC Software (Inno Setup).
;
; Se compila en el CI con:  ISCC.exe /DMyAppVersion=1.2.3 installer.iss
; Produce:  installer_output\BGC-software-Setup.exe
;
; Instalación POR USUARIO (sin admin): así las actualizaciones que dispara el
; abuelo desde la app no piden contraseña de administrador. CloseApplications +
; RestartApplications permiten reemplazar el .exe aunque esté abierto y volver
; a lanzarlo al terminar (esto es lo que hace fluido el "Actualizar ahora").

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppName "BGC Software"
#define MyAppExeName "BGC-software.exe"
#define MyAppPublisher "Cooperativa BGC"

[Setup]
; AppId identifica la app para futuras actualizaciones. NO cambiar entre versiones.
AppId={{6F3B2A1C-9D4E-4E7A-B1C2-BGC0SOFTWARE01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BGC Software
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=BGC-software-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=yes
SetupIconFile=app_icon2.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "dist\BGC-software.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\BGC Software"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\BGC Software"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir BGC Software"; Flags: nowait postinstall skipifsilent
