@echo off
echo ========================================================
echo   Сборка игры "Рыцарь против Зомби" (Knight vs Zombies)
echo ========================================================

echo Проверка зависимостей...
python -m pip install -q pyinstaller pygame-ce pydantic pydantic-settings

echo Запуск PyInstaller...
pyinstaller --noconfirm KnightVsZombies.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   Сборка успешно завершена!
    echo   Файл приложения: dist\KnightVsZombies.exe
    echo ========================================================
) else (
    echo.
    echo [ОШИБКА] Не удалось собрать приложение.
)
pause

