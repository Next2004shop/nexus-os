# Install PHP Portable - Verified
$ErrorActionPreference = "Stop"

$url = "https://windows.php.net/downloads/releases/php-8.3.28-Win32-vs16-x64.zip"
$dest = "php.zip"
$extract = "php"

Write-Host "Downloading Verified PHP 8.3.28..."
try {
    Invoke-WebRequest -Uri $url -OutFile $dest
} catch {
    Write-Host "Error downloading: $($_.Exception.Message)"
    exit 1
}

Write-Host "Extracting..."
if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
Expand-Archive -Path $dest -DestinationPath $extract -Force

# Setup php.ini
Copy-Item "$extract/php.ini-development" "$extract/php.ini"

# Verify
& "$extract/php.exe" -v

Write-Host "Success! PHP is in ./php"
