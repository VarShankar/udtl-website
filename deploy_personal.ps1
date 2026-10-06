# Windows (PowerShell) version. Requires GlobalProtect VPN + built-in OpenSSH (ssh/scp).
# Run from the project folder:  .\deploy_personal.ps1
$ErrorActionPreference = "Stop"
$HostName = "shankar@shell.cs.utah.edu"
Set-Location $PSScriptRoot
if (Get-Command python -ErrorAction SilentlyContinue) { python build.py personal }   # optional rebuild
$stamp = Get-Date -Format "yyyy-MM-dd-HHmm"
Write-Host "Backing up current public_html -> public_html_backup_$stamp"
ssh $HostName "cp -a public_html public_html_backup_$stamp 2>/dev/null; mkdir -p public_html"
scp -r dist/personal/* "${HostName}:public_html/"
ssh $HostName "chmod -R a+rX public_html"
Write-Host "Done: https://users.cs.utah.edu/~shankar/"
