# Creates a self-signed cert for Entra app-only auth (homelab). Outputs PFX + CER under ./certs/
# Upload graph-app.cer to App registration > Certificates. Use graph-app.pfx locally as GRAPH_CERT_PATH.

$ErrorActionPreference = "Stop"
# Repo root = parent of /scripts
$repoRoot = Split-Path -Parent $PSScriptRoot

$base = Join-Path $repoRoot "certs"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$cert = New-SelfSignedCertificate `
    -Subject "CN=m365-posture-homelab" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable `
    -KeySpec KeyExchange `
    -KeyLength 2048 `
    -HashAlgorithm SHA256 `
    -NotAfter (Get-Date).AddYears(2)

$thumb = $cert.Thumbprint
$pfxPath = Join-Path $base "graph-app.pfx"
$cerPath = Join-Path $base "graph-app.cer"

# Passwordless PFX (homelab). For a password-protected PFX, set $pwd instead.
$pwd = New-Object System.Security.SecureString
Export-PfxCertificate `
    -Cert "Cert:\CurrentUser\My\$thumb" `
    -FilePath $pfxPath `
    -Password $pwd | Out-Null

Export-Certificate `
    -Cert "Cert:\CurrentUser\My\$thumb" `
    -FilePath $cerPath | Out-Null

Write-Host "Created:"
Write-Host "  PFX (private): $pfxPath"
Write-Host "  CER (public):  $cerPath"
Write-Host "  Thumbprint:    $thumb"
Write-Host ""
Write-Host "Next: Upload graph-app.cer to Entra app registration > Certificates."
Write-Host "Then set GRAPH_CERT_PATH to the PFX path (after you move it, update the path)."
