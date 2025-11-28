# Скрипт для безопасного запуска бота
Write-Host "Проверка запущенных экземпляров бота..." -ForegroundColor Yellow

# Останавливаем все процессы Python
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "Остановка предыдущих экземпляров..." -ForegroundColor Yellow
    foreach ($proc in $pythonProcesses) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

Write-Host "Запуск бота..." -ForegroundColor Green
python bot.py

