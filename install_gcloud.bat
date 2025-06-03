@echo off
REM Google Cloud CLI Kurulum Script'i - Windows
REM AI Overview Optimization Projesi

echo.
echo ================================================
echo   Google Cloud CLI Kurulum - Windows
echo ================================================
echo.

REM Yönetici hakları kontrolü
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Yönetici haklariyla çalışıyorsunuz.
) else (
    echo UYARI: Yönetici haklari önerilir. Kurulum sırasında sorun yaşayabilirsiniz.
    pause
)

echo.
echo 1. Google Cloud CLI indiriliyor...
echo.

REM Temp dizinine indir
set "TEMP_INSTALLER=%TEMP%\GoogleCloudSDKInstaller.exe"

REM PowerShell ile download
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe', '%TEMP_INSTALLER%')}"

if not exist "%TEMP_INSTALLER%" (
    echo HATA: Dosya indirilemedi!
    echo Manuel olarak şu linkten indirin:
    echo https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo.
echo 2. Kurulum başlatılıyor...
echo.

REM Installer'ı çalıştır
"%TEMP_INSTALLER%"

if %errorLevel% neq 0 (
    echo HATA: Kurulum başarısız!
    pause
    exit /b 1
)

echo.
echo 3. Kurulum tamamlandı. Terminal yeniden başlatılıyor...
echo.

REM Temp dosyasını temizle
if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"

echo.
echo ================================================
echo   KURULUM TAMAMLANDI!
echo ================================================
echo.
echo Sonraki adımlar:
echo 1. Bu terminal'i kapatın
echo 2. Yeni bir terminal açın
echo 3. Şu komutları çalıştırın:
echo.
echo    gcloud version
echo    gcloud auth login
echo    gcloud config set project YOUR_PROJECT_ID
echo.
echo 4. Proje kurulumuna devam edin:
echo    python setup.py
echo.

pause 