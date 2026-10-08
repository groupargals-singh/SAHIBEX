# SAHIBEX Android Companion Bridge

Additive source/protocol stage for #15 Real Computer/UI Control.

Security boundary: loopback-only transport, per-session random token, HMAC request signing on the Python side, and human-granted Android Accessibility permission. SAHIBEX remains the authority; the companion never grants permission itself.

Build status: Android SDK 35, javac, aapt2, d8, apksigner, and Gradle are available on this device. Android Gradle Plugin 8.13.0 is not compatible with the installed Gradle 9.8, so the companion can be built on-device through the SDK toolchain directly. The manual debug APK is compiled, signed, and signature-verified successfully.

Device activation boundary: installing/replacing the companion APK and enabling the Accessibility service are Android user/system actions that this Termux UID is not authorized to perform programmatically. After installation, enable the SAHIBEX Accessibility service manually, open the companion, then run the secure screenshot test. Real screenshot/UI-tree/tap/type/key and emergency-stop/audit E2E must be marked PASS only after that device-side verification.
