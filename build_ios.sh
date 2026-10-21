#!/usr/bin/env bash
set -euo pipefail

SDK=$(xcrun --sdk iphoneos --show-sdk-path)
CC=$(xcrun --sdk iphoneos --find clang)

mkdir -p ios/Runner/libs

cd native_lib
python3 grabTitles.py

GOOS=ios \
GOARCH=arm64 \
CGO_ENABLED=1 \
CC="$CC" \
CGO_CFLAGS="-isysroot $SDK -arch arm64 -miphoneos-version-min=14.0" \
CGO_LDFLAGS="-isysroot $SDK -arch arm64 -miphoneos-version-min=14.0" \
go build -buildmode=c-archive -o ../ios/Runner/libs/libwiiudownloader.a

cd ..
flutter build ios --no-codesign --release
mkdir -p Payload
mv build/ios/iphoneos/Runner.app Payload
zip -r wiiudownloader.ipa Payload
rm -rf Payload