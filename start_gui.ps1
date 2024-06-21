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
                   |___/                        version $version                         
"@
Write-Host "--------------------------------------------------------------------"

# check if virtual environment folder is not present
if (-not (Test-Path $venv)) {
    # print nice message

    Write-Host "Welcome to the Tagiatello installation script!"
    Write-Host "----------------------------------------------------------------------"

    # ask if should install gpu version
    $gpu = Read-Host "Please, specify which version you want to install (cpu/gpu) or press enter to choose default (gpu)"

    if ($gpu -eq "cpu") {
        $mode = "cpu"
    } else {
        $mode = "gpu"
    }
    Write-Host "Selected mode: $mode"
    Write-Host "--------------------------------------------------------------------"
    Write-Host "Creating virtual environment..."
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host "--------------------------------------------------------------------"
    Write-Host "Installing torch and torchvision..."
    if ($mode -eq "gpu") {
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    } else {
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    }
    Write-Host "--------------------------------------------------------------------"
    Write-Host "Installing other dependencies..."
    pip install -r requirements.txt
    Write-Host "--------------------------------------------------------------------"
    Write-Host "Installation completed! Starting the application..."
    python main.py
} else {


    Write-Host "Virtual environment already exists. Starting the application..."
    .\venv\Scripts\Activate.ps1
    python main.py
}



