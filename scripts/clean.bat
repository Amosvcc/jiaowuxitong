@echo off
cd /d %~dp0\..
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist DataAnalysisApp.spec del /q DataAnalysisApp.spec
