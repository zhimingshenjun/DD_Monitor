#!/bin/sh
pyinstaller DD监控室.spec
cp -r utils/ dist/DD监控室/utils/
cp scripts/run.sh dist/DD监控室/