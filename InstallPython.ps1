# Attribute to https://stackoverflow.com/a/45827384/10568801

$pythonVersion = "3.8.1"
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion.exe"
$pythonDownloadPath = "python-$pythonVersion.exe"
$pythonInstallDir = "Python$pythonVersion"


(New-Object Net.WebClient).DownloadFile($pythonUrl, $pythonDownloadPath)
& $pythonDownloadPath /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 TargetDir=$pythonInstallDir
if ($LASTEXITCODE -ne 0) {
    throw "The python installer at '$pythonDownloadPath' exited with error code '$LASTEXITCODE'"
}
