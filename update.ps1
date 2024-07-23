# load application version from version.txt
$version = Get-Content -Path "version.txt"

Write-Host @"
  _______                  _   _           _            _   _         
 |__   __|                | | (_)         | |          | | | |        
    | |     __ _    __ _  | |  _    __ _  | |_    ___  | | | |   ___  
    | |    / _' |  / _' | | | | |  / _' | | __|  / _ \ | | | |  / _ \ 
    | |   | (_| | | (_| | | | | | | (_| | | |_  |  __/ | | | | | (_) |
    |_|    \__,_|  \__, | |_| |_|  \__,_|  \__|  \___| |_| |_|  \___/ 
                    __/ |                                             
                   |___/                                $version                
"@
Write-Host "--------------------------------------------------------------------"

Write-Host "Updating the application..."


try {
    # check if virtual environment folder is not present
    $venv = "venv"
    if (-not (Test-Path $venv)) {
        Write-Host "Creating virtual environment..."
        python -m venv $venv
    }
} catch {
    Write-Host $_
    Read-Host -Prompt "Press Enter to exit"
}

try {
    Write-Host "Switching to main branch..."
    git checkout main

    Write-Host "Pulling the latest changes..."
    git pull
} catch {
    Write-Host "An error occurred while switching to main branch or pulling the latest changes."
    Write-Host $_
    Read-Host -Prompt "Press Enter to exit"
}

try {
    Write-Host "Updating the virtual environment..."
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
} catch {
    Write-Host "An error occurred while updating the virtual environment."
    Write-Host $_
    Read-Host -Prompt "Press Enter to exit"
}

Write-Host "Update completed!"
Read-Host -Prompt "Press Enter to exit"