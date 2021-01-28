#!/bin/zsh
CERT_ID=""
AC_USERNAME=""
AC_OTP_PASS=""
codesign --deep --force --verbose \
    --sign $CERT_ID --entitlements ../utils/entitlements.plist \
    -o runtime DDMonitor.app
xcrun altool --notarize-app 
    --primary-bundle-id "com.github.zhimingshenjun.ddmonitor" \
     --username $AC_USERNAME --password $AC_OTP_PASS \
     --file DDMonitor.zip