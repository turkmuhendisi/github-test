@echo off
title GlobalMain Command Center
cd /d "%~dp0..\.."
powershell -ExecutionPolicy Bypass -File "%~dp0codelist.ps1"

