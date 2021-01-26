#!/bin/sh
pyinstaller --clean --noconfirm DDMonitor_unix.spec
cp scripts/run.sh dist/DDMonitor/