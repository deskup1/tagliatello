# check if virtual environment folder exists, if not ask if should install gpu version or cpu version

$venv = "venv"
$mode = "cpu"

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

# check if virtual environment folder is not present
if (-not (Test-Path $venv)) {
    Write-Host "Welcome to the Tagiatello installation script!"
    Write-Host "----------------------------------------------------------------------"
    Write-Host "Creating virtual environment..."
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host "--------------------------------------------------------------------"
    Write-Host "Installing other dependencies..."
    pip install -r requirements.txt
    Write-Host "--------------------------------------------------------------------"
    Write-Host "Installation completed! Starting the application..."
    python main.py
} else {

    Write-Host "Virtual environment already exists."
    .\venv\Scripts\Activate.ps1

    # load text file app-data.yaml
    $appData = Get-Content -Path "app-data.yaml"

    $lastVersion = $appData | Select-String -Pattern "version:" | ForEach-Object { $_ -replace "version: ", "" }
    
    # if version is different than last version, run pip install -r requirements.txt
    if ($version -ne $lastVersion) {
        Write-Host "New version detected. Updating the application..."
        pip install -r requirements.txt
        Write-Host "Application updated. Starting the application..."
        python main.py
    } else {
        Write-Host "Application is up to date. Starting the application..."
        python main.py
    }

}