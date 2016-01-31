[Setup]
AppName=CBModel
AppVersion=1.02
DefaultDirName={pf}\CBModel
DefaultGroupName=CBModel
OutputBaseFilename=Install_CBModel
SetupIconFile=symbol.ico
WizardImageBackColor=clWhite
WizardImageFile=logo_install.bmp
UninstallDisplayIcon={app}\symbol.ico

[Files]
Source: "C:\Program Files\CBModel\dist\cbmodel\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{commonprograms}\CBModel"; Filename: "{app}\cbmodel.exe"; WorkingDir: "{app}"; IconFilename: "{app}\symbol.ico"; Comment: "Crossbeams Modeller"
