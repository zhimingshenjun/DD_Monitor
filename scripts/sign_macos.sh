#!/bin/zsh
AC_OTP_PASS="@keychain:AC_PASSWORD"
PRODUCT_NAME="DDMonitor"
APP_PATH="$PRODUCT_NAME.app"
ZIP_PATH="$PRODUCT_NAME.zip"
codesign --deep --force --verbose \
    --sign $CERT_ID --entitlements ../utils/entitlements.plist \
    -o runtime $APP_PATH
/usr/bin/ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"
xcrun altool --notarize-app \
    --primary-bundle-id "com.github.zhimingshenjun.ddmonitor" \
     --username $AC_USERNAME --password $AC_OTP_PASS \
     --file $ZIP_PATH