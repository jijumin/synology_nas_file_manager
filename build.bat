@echo off
chcp 65001 >nul
echo ================================================
echo 群晖NAS文件管理器 EXE打包工具
echo ================================================
echo.

echo 正在启动打包程序...
python build_exe.py

echo.
echo 打包完成！按任意键退出...
pause >nul 