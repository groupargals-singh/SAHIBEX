# SAHIBEX Android Companion Bridge

Additive source/protocol stage for #15 Real Computer/UI Control.

Security boundary: loopback-only transport, per-session random token, HMAC request signing on the Python side, and human-granted Android Accessibility permission. SAHIBEX remains the authority; the companion never grants permission itself.

Build status: this device has no Android SDK, Gradle, aapt2, d8, javac, or apksigner, so an APK cannot be built or installed here yet.

Remaining device stage: build/install companion, enable Accessibility service manually, pair the session token, then run real screenshot/UI-tree/tap/type/key verification and emergency-stop/audit E2E.
