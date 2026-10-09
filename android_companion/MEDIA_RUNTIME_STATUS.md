# SAHIBEX Android media runtime

`core/brain/android_media_runtime.py` is the opt-in runtime adapter for Termux:API speech recognition, text-to-speech, and camera capture.

## Safety and activation

- No microphone or camera is opened unless the caller passes `consent=True` for that individual operation.
- The adapter never invokes a shell; commands are passed as argument lists and have a timeout.
- Photos are written only to the configured SAHIBEX capture directory.
- The Termux `termux-api` CLI package is installed on this device.
- A working Android **Termux:API companion app**, Android microphone/camera permissions, and a successful real hardware test are still required. CLI presence alone is not proof that audio or camera works.
- Vision reasoning is not yet a live image-understanding model. Camera capture is only the acquisition step; an image model/OCR stage and end-to-end verification are still required.
- Android Accessibility control is separate and must be verified through the companion app's device-side test.

## Test

Run:

`PYTHONPATH=. pytest -q tests/unit/test_android_media_runtime.py`

Do not mark voice/camera/vision fully live until a real user-approved microphone, speaker, camera, and image-understanding test passes.
