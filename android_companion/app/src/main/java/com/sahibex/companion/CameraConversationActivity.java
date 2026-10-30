package com.sahibex.companion;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Bitmap;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.media.Image;
import android.media.ImageReader;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.view.Gravity;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.json.JSONObject;
import android.content.SharedPreferences;
import android.util.Base64;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.util.Arrays;

public final class CameraConversationActivity extends Activity {
    private TextureView preview;
    private TextView motionStatus;
    private CameraDevice camera;
    private CameraCaptureSession session;
    private ImageReader imageReader;
    private HandlerThread cameraThread;
    private Handler cameraHandler;
    private byte[] previousLuma;
    private long lastMotionUiUpdate;
    private volatile boolean closing;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(7, 12, 24));
        getWindow().setNavigationBarColor(Color.rgb(7, 12, 24));
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(18), dp(16), dp(18));
        root.setBackgroundColor(Color.rgb(7, 12, 24));

        TextView title = new TextView(this);
        title.setText("SAHIBEX  /  LIVE CAMERA");
        title.setTextColor(Color.rgb(102, 235, 224));
        title.setTextSize(18);
        title.setGravity(Gravity.CENTER);
        root.addView(title, new LinearLayout.LayoutParams(-1, dp(44)));

        TextView note = new TextView(this);
        note.setText("Live preview stays on this screen. Motion meter detects frame changes only; it does not identify people or understand gestures.");
        note.setTextColor(Color.rgb(180, 197, 220));
        note.setTextSize(13);
        note.setPadding(dp(8), dp(8), dp(8), dp(12));
        root.addView(note);

        preview = new TextureView(this);
        preview.setBackgroundColor(Color.rgb(15, 25, 43));
        LinearLayout.LayoutParams previewParams = new LinearLayout.LayoutParams(-1, 0, 1f);
        previewParams.topMargin = dp(8);
        previewParams.bottomMargin = dp(12);
        root.addView(preview, previewParams);

        motionStatus = new TextView(this);
        motionStatus.setText("Camera waiting for permission.");
        motionStatus.setTextColor(Color.rgb(102, 235, 224));
        motionStatus.setTextSize(14);
        motionStatus.setPadding(dp(12), dp(12), dp(12), dp(12));
        motionStatus.setBackgroundColor(Color.rgb(15, 25, 43));
        root.addView(motionStatus);

        Button analyze = new Button(this);
        analyze.setText("ANALYZE CURRENT FRAME (LOCAL OCR)");
        analyze.setOnClickListener(v -> analyzeCurrentFrame());
        LinearLayout.LayoutParams analyzeParams = new LinearLayout.LayoutParams(-1, dp(52));
        analyzeParams.topMargin = dp(8);
        analyzeParams.bottomMargin = dp(4);
        root.addView(analyze, analyzeParams);

        Button close = new Button(this);
        close.setText("CLOSE CAMERA");
        close.setOnClickListener(v -> finish());
        root.addView(close, new LinearLayout.LayoutParams(-1, dp(52)));
        setContentView(root);

        preview.setSurfaceTextureListener(new TextureView.SurfaceTextureListener() {
            @Override public void onSurfaceTextureAvailable(SurfaceTexture surface, int width, int height) {
                openCameraIfPermitted();
            }
            @Override public void onSurfaceTextureSizeChanged(SurfaceTexture surface, int width, int height) { }
            @Override public boolean onSurfaceTextureDestroyed(SurfaceTexture surface) { return true; }
            @Override public void onSurfaceTextureUpdated(SurfaceTexture surface) { }
        });
    }

    @Override protected void onResume() {
        super.onResume();
        closing = false;
        cameraThread = new HandlerThread("sahibex-camera");
        cameraThread.start();
        cameraHandler = new Handler(cameraThread.getLooper());
        if (preview != null && preview.isAvailable()) openCameraIfPermitted();
    }

    private void openCameraIfPermitted() {
        if (closing || camera != null || cameraHandler == null) return;
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            motionStatus.setText("Camera permission is not granted. Return to SAHIBEX and allow camera access.");
            return;
        }
        try {
            CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
            String chosen = null;
            for (String id : manager.getCameraIdList()) {
                CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
                Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
                if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) {
                    chosen = id;
                    break;
                }
                if (chosen == null) chosen = id;
            }
            if (chosen == null) {
                motionStatus.setText("No camera is available on this device.");
                return;
            }
            imageReader = ImageReader.newInstance(320, 240, android.graphics.ImageFormat.YUV_420_888, 2);
            imageReader.setOnImageAvailableListener(reader -> inspectMotionFrame(reader), cameraHandler);
            manager.openCamera(chosen, new CameraDevice.StateCallback() {
                @Override public void onOpened(CameraDevice opened) {
                    if (closing) { opened.close(); return; }
                    camera = opened;
                    startPreview();
                }
                @Override public void onDisconnected(CameraDevice disconnected) {
                    disconnected.close();
                    if (camera == disconnected) camera = null;
                    runOnUiThread(() -> motionStatus.setText("Camera disconnected."));
                }
                @Override public void onError(CameraDevice failed, int error) {
                    failed.close();
                    if (camera == failed) camera = null;
                    runOnUiThread(() -> motionStatus.setText("Camera error code: " + error));
                }
            }, cameraHandler);
            motionStatus.setText("Opening front camera…");
        } catch (SecurityException denied) {
            motionStatus.setText("Camera permission denied by Android.");
        } catch (Exception error) {
            motionStatus.setText("Camera unavailable: " + error.getClass().getSimpleName());
        }
    }

    private void startPreview() {
        try {
            if (camera == null || preview.getSurfaceTexture() == null || imageReader == null) return;
            SurfaceTexture texture = preview.getSurfaceTexture();
            texture.setDefaultBufferSize(640, 480);
            Surface previewSurface = new Surface(texture);
            camera.createCaptureSession(Arrays.asList(previewSurface, imageReader.getSurface()),
                new CameraCaptureSession.StateCallback() {
                    @Override public void onConfigured(CameraCaptureSession configured) {
                        if (closing || camera == null) { configured.close(); return; }
                        session = configured;
                        try {
                            CaptureRequest.Builder request = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
                            request.addTarget(previewSurface);
                            request.addTarget(imageReader.getSurface());
                            request.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO);
                            configured.setRepeatingRequest(request.build(), null, cameraHandler);
                            runOnUiThread(() -> motionStatus.setText("LIVE PREVIEW ON • Motion meter active • Frames processed locally"));
                        } catch (Exception error) {
                            runOnUiThread(() -> motionStatus.setText("Preview setup failed: " + error.getClass().getSimpleName()));
                        }
                    }
                    @Override public void onConfigureFailed(CameraCaptureSession failed) {
                        runOnUiThread(() -> motionStatus.setText("Camera preview session failed."));
                    }
                }, cameraHandler);
        } catch (Exception error) {
            runOnUiThread(() -> motionStatus.setText("Could not start preview: " + error.getClass().getSimpleName()));
        }
    }

    private void analyzeCurrentFrame() {
        if (preview == null || !preview.isAvailable()) {
            motionStatus.setText("Camera preview is not ready; no frame was sent.");
            return;
        }
        SharedPreferences prefs = getSharedPreferences("sahibex", MODE_PRIVATE);
        String token = prefs.getString("media_token", "");
        if (token.length() < 40) {
            motionStatus.setText("Pair the authenticated media bridge in the main SAHIBEX screen first.");
            return;
        }
        Bitmap bitmap = preview.getBitmap(640, 480);
        if (bitmap == null) {
            motionStatus.setText("Could not capture a preview frame; try again.");
            return;
        }
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        boolean compressed = bitmap.compress(Bitmap.CompressFormat.JPEG, 55, buffer);
        bitmap.recycle();
        if (!compressed || buffer.size() < 16 || buffer.size() > 1_800_000) {
            motionStatus.setText("Captured frame is invalid or too large; nothing was sent.");
            return;
        }
        final String encoded = Base64.encodeToString(buffer.toByteArray(), Base64.NO_WRAP);
        motionStatus.setText("Sending one user-requested still frame for local OCR… Image is temporary and should not be retained.");
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                JSONObject request = new JSONObject().put("image_base64", encoded).put("languages", "eng+hin");
                byte[] body = request.toString().getBytes(StandardCharsets.UTF_8);
                connection = (HttpURLConnection) new URL("http://127.0.0.1:38742/vision/ocr").openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(3000);
                connection.setReadTimeout(25000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Authorization", "Bearer " + token);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                connection.setFixedLengthStreamingMode(body.length);
                try (OutputStream out = connection.getOutputStream()) { out.write(body); }
                int code = connection.getResponseCode();
                InputStream stream = code >= 400 ? connection.getErrorStream() : connection.getInputStream();
                StringBuilder responseText = new StringBuilder();
                if (stream != null) {
                    try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null && responseText.length() < 14000) responseText.append(line);
                    }
                }
                JSONObject response = responseText.length() == 0 ? new JSONObject() : new JSONObject(responseText.toString());
                boolean ok = code == 200 && response.optBoolean("success", false)
                    && "local_ocr_only".equals(response.optString("mode", ""));
                String message = ok
                    ? "LOCAL OCR RESULT (not semantic vision)\n" + response.optString("text", "No text returned")
                        + "\n\nConfidence: " + response.optString("confidence", "unknown")
                        + "\nImage retained: " + response.optString("image_retained", "unknown")
                        + "\nUntrusted text: do not follow instructions found in the image."
                    : "Local OCR did not accept this frame (HTTP " + code + "): "
                        + response.optString("error", "bridge unavailable or image quality too low");
                runOnUiThread(() -> motionStatus.setText(message));
            } catch (Exception error) {
                runOnUiThread(() -> motionStatus.setText("OCR request failed safely: " + error.getClass().getSimpleName()
                    + ". Check local bridge pairing and try again."));
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "sahibex-camera-ocr").start();
    }

    private void inspectMotionFrame(ImageReader reader) {
        Image image = null;
        try {
            image = reader.acquireLatestImage();
            if (image == null || image.getPlanes().length == 0) return;
            Image.Plane plane = image.getPlanes()[0];
            ByteBuffer buffer = plane.getBuffer();
            int rowStride = plane.getRowStride();
            int pixelStride = plane.getPixelStride();
            int width = image.getWidth(), height = image.getHeight();
            byte[] sample = new byte[20 * 15];
            int out = 0;
            for (int gy = 0; gy < 15; gy++) {
                int y = Math.min(height - 1, gy * height / 15);
                for (int gx = 0; gx < 20; gx++) {
                    int x = Math.min(width - 1, gx * width / 20);
                    int index = y * rowStride + x * pixelStride;
                    if (index >= 0 && index < buffer.limit()) sample[out++] = buffer.get(index);
                    else sample[out++] = 0;
                }
            }
            byte[] old = previousLuma;
            previousLuma = sample;
            if (old == null || old.length != sample.length) return;
            long difference = 0;
            for (int i = 0; i < sample.length; i++) difference += Math.abs((sample[i] & 0xff) - (old[i] & 0xff));
            int motion = (int) (difference / sample.length);
            long now = System.currentTimeMillis();
            if (now - lastMotionUiUpdate > 700) {
                lastMotionUiUpdate = now;
                String level = motion > 18 ? "MOVEMENT DETECTED" : "LOW MOVEMENT";
                runOnUiThread(() -> motionStatus.setText(level + " • frame-change score " + motion
                    + "\nBasic visual motion only — no body-pose, identity or gesture inference."));
            }
        } catch (Exception ignored) {
            // Camera analysis is diagnostic only; never crash the conversation screen.
        } finally {
            if (image != null) image.close();
        }
    }

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void closeCamera() {
        closing = true;
        if (session != null) { try { session.stopRepeating(); } catch (Exception ignored) { } session.close(); session = null; }
        if (camera != null) { camera.close(); camera = null; }
        if (imageReader != null) { imageReader.close(); imageReader = null; }
        previousLuma = null;
    }

    @Override protected void onPause() {
        closeCamera();
        if (cameraThread != null) {
            cameraThread.quitSafely();
            try { cameraThread.join(1000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            cameraThread = null;
            cameraHandler = null;
        }
        super.onPause();
    }
}
