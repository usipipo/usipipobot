[app]

# (str) Title of your application
title = uSipipo VPN

# (str) Package name
package.name = usipipo

# (str) Package domain (needed for android/ios packaging)
package.domain = org.usipipo

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,kivymd==2.0.1.dev0,httpx==0.27.0,cryptography==42.0.0,pydantic==2.5.0,keyring==24.3.0,certifi==2024.2.2,qrcode==7.4.2,Pillow==10.2.0

# (str) Supported orientation (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible
android.targetapi = 34

# (int) Minimum API your APK will support
android.minapi = 26

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (bool) If True, then automatically accept SDK license agreements
android.accept_sdk_license = True

# (str) Android entry point (default is ok for Kivy-based app)
android.entrypoint = org.kivy.android.PythonActivity

# (str) The Android app theme (default is ok for Kivy-based app)
android.apptheme = "@android:style/Theme.NoTitleBar"

# (str) Presplash background color
android.presplash_color = #0a0a0f

# (str) Icon filename
android.icon = assets/images/icon_512.png

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk)
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk)
android.debug_artifact = apk

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .ipa) storage
bin_dir = ./bin
