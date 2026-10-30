package com.sahibex.companion;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Bitmap;
import android.graphics.Path;
import android.graphics.Rect;
import android.hardware.HardwareBuffer;
import android.os.Build;
import android.os.Bundle;
import android.view.Display;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.ByteArrayOutputStream;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.json.JSONArray;
import org.json.JSONObject;

public final class SahibexAccessibilityService extends AccessibilityService {
    private static final String PREFS = "sahibex";
    private static final String STOP_KEY = "accessibility_stopped";
    private static final int MAX_TEXT_CHARS = 16000;
    private static final int MAX_TREE_NODES = 500;
    private static volatile boolean runtimeStopped;
    private BridgeServer server;

    @Override protected void onServiceConnected() {
        super.onServiceConnected();
        runtimeStopped = runtimeStopped || getSharedPreferences(PREFS, MODE_PRIVATE)
            .getBoolean(STOP_KEY, false);
        if (server != null) server.stop();
        server = new BridgeServer(this, 38741);
        server.start();
    }

    @Override public void onInterrupt() { }

    @Override public void onAccessibilityEvent(AccessibilityEvent event) { }

    @Override public void onDestroy() {
        if (server != null) server.stop();
        super.onDestroy();
    }

    String getSharedToken() {
        return getSharedPreferences(PREFS, MODE_PRIVATE).getString("token", null);
    }

    static void engageEmergencyStopLocally() {
        runtimeStopped = true;
    }

    static synchronized boolean resumeEmergencyStopLocally(android.content.SharedPreferences prefs) {
        boolean saved = prefs.edit().putBoolean(STOP_KEY, false).commit();
        if (saved) runtimeStopped = false;
        else runtimeStopped = true;
        return saved;
    }

    synchronized boolean recordAudit(String action, String outcome, String nonce) {
        try {
            android.content.SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
            JSONArray events = new JSONArray(prefs.getString("accessibility_audit_events", "[]"));
            JSONObject event = new JSONObject()
                .put("time_ms", System.currentTimeMillis())
                .put("action", action)
                .put("outcome", outcome)
                .put("nonce_fingerprint", sha256((nonce == null ? "" : nonce)
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0, 16));
            while (events.length() >= 100) events.remove(0);
            events.put(event);
            return prefs.edit().putString("accessibility_audit_events", events.toString()).commit();
        } catch (Exception failure) {
            return false;
        }
    }

    JSONObject handle(String action, JSONObject payload) throws Exception {
        JSONObject p = payload == null ? new JSONObject() : payload;
        if ("emergency_stop".equals(action)) {
            runtimeStopped = true;
            boolean saved = getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                .putBoolean(STOP_KEY, true).commit();
            if (!saved) throw new IllegalStateException("emergency stop persistence failed; runtime latch remains active");
            return new JSONObject().put("stopped", true).put("reason", "authenticated emergency stop");
        }
        if ("emergency_stop_status".equals(action)) {
            return new JSONObject().put("stopped", runtimeStopped ||
                getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(STOP_KEY, false));
        }
        if (runtimeStopped || getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(STOP_KEY, false)) {
            throw new SecurityException("emergency stop engaged; resume locally in companion app");
        }
        switch (action) {
            case "tap":
                return gesture(p.getInt("x"), p.getInt("y"), p.getInt("x"), p.getInt("y"), 80);
            case "swipe":
                return gesture(p.getInt("x"), p.getInt("y"), p.getInt("end_x"),
                    p.getInt("end_y"), p.optLong("duration_ms", 250));
            case "type_text":
                return typeText(p.getString("text"));
            case "keyevent":
                return globalKey(p.getInt("keycode"));
            case "ui_tree":
                return new JSONObject().put("tree", tree(getRootInActiveWindow(), 0, new int[]{0}));
            case "screenshot":
                return screenshot(p.optBoolean("include_base64", false));
            default:
                throw new IllegalArgumentException("unsupported action: " + action);
        }
    }

    private JSONObject gesture(int x, int y, int endX, int endY, long durationMs) throws Exception {
        int width = getResources().getDisplayMetrics().widthPixels;
        int height = getResources().getDisplayMetrics().heightPixels;
        if (x < 0 || y < 0 || endX < 0 || endY < 0
            || x >= width || endX >= width || y >= height || endY >= height) {
            throw new IllegalArgumentException("gesture coordinates outside current display");
        }
        if (durationMs < 1 || durationMs > 5000) {
            throw new IllegalArgumentException("gesture duration must be 1..5000 ms");
        }
        Path path = new Path();
        path.moveTo(x, y);
        if (x != endX || y != endY) path.lineTo(endX, endY);
        CountDownLatch latch = new CountDownLatch(1);
        AtomicReference<Boolean> completed = new AtomicReference<>(false);
        AtomicReference<Boolean> cancelled = new AtomicReference<>(false);
        GestureDescription gesture = new GestureDescription.Builder()
            .addStroke(new GestureDescription.StrokeDescription(path, 0, durationMs)).build();
        boolean dispatched = dispatchGesture(gesture, new GestureResultCallback() {
            @Override public void onCompleted(GestureDescription g) {
                completed.set(true);
                latch.countDown();
            }
            @Override public void onCancelled(GestureDescription g) {
                cancelled.set(true);
                latch.countDown();
            }
        }, null);
        if (!dispatched) throw new IllegalStateException("gesture dispatch rejected");
        if (!latch.await(6, TimeUnit.SECONDS)) throw new IllegalStateException("gesture completion timeout");
        if (!completed.get() || cancelled.get()) throw new IllegalStateException("gesture cancelled");
        return new JSONObject().put("accepted", true).put("completed", true);
    }

    private JSONObject typeText(String text) throws Exception {
        if (text == null || text.length() > MAX_TEXT_CHARS) {
            throw new IllegalArgumentException("text must be at most " + MAX_TEXT_CHARS + " characters");
        }
        AccessibilityNodeInfo root = getRootInActiveWindow();
        AccessibilityNodeInfo node = findFocusedEditable(root, 0);
        if (node == null) throw new IllegalStateException("no focused editable node");
        if (node.isPassword()) throw new SecurityException("typing into password fields is blocked");
        Bundle args = new Bundle();
        args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
        boolean accepted = node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
        if (!accepted) {
            throw new IllegalStateException("focused editable field rejected text action");
        }
        return new JSONObject().put("accepted", true).put("completed", true);
    }

    private AccessibilityNodeInfo findFocusedEditable(AccessibilityNodeInfo node, int depth) {
        if (node == null || depth > 12) return null;
        if (node.isEditable() && node.isFocused() && node.isEnabled() && !node.isPassword()) return node;
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo found = findFocusedEditable(node.getChild(i), depth + 1);
            if (found != null) return found;
        }
        return null;
    }

    private JSONObject globalKey(int keyCode) throws Exception {
        boolean ok;
        if (keyCode == KeyEvent.KEYCODE_BACK) ok = performGlobalAction(GLOBAL_ACTION_BACK);
        else if (keyCode == KeyEvent.KEYCODE_HOME) ok = performGlobalAction(GLOBAL_ACTION_HOME);
        else if (keyCode == KeyEvent.KEYCODE_APP_SWITCH) ok = performGlobalAction(GLOBAL_ACTION_RECENTS);
        else throw new IllegalArgumentException("unsupported global key");
        if (!ok) throw new IllegalStateException("global key action rejected");
        return new JSONObject().put("accepted", true).put("completed", true);
    }

    private JSONArray tree(AccessibilityNodeInfo node, int depth, int[] count) throws Exception {
        JSONArray empty = new JSONArray();
        if (node == null || depth > 12 || count[0] >= MAX_TREE_NODES) return empty;
        count[0]++;
        JSONObject out = new JSONObject();
        Rect bounds = new Rect();
        node.getBoundsInScreen(bounds);
        out.put("class", String.valueOf(node.getClassName()));
        out.put("text", node.isPassword() ? "[REDACTED]" : node.getText());
        out.put("contentDescription", node.isPassword() ? "[REDACTED]" : node.getContentDescription());
        out.put("password", node.isPassword());
        out.put("clickable", node.isClickable());
        out.put("editable", node.isEditable());
        out.put("enabled", node.isEnabled());
        out.put("bounds", new JSONArray().put(bounds.left).put(bounds.top)
            .put(bounds.right).put(bounds.bottom));
        JSONArray children = new JSONArray();
        for (int i = 0; i < node.getChildCount() && count[0] < MAX_TREE_NODES; i++) {
            JSONArray child = tree(node.getChild(i), depth + 1, count);
            for (int j = 0; j < child.length(); j++) children.put(child.get(j));
        }
        out.put("children", children);
        return new JSONArray().put(out);
    }

    private JSONObject screenshot(boolean includeBase64) throws Exception {
        if (Build.VERSION.SDK_INT < 30) throw new IllegalStateException("screenshot requires Android 11+");
        CountDownLatch latch = new CountDownLatch(1);
        AtomicReference<Bitmap> bitmapRef = new AtomicReference<>();
        AtomicReference<HardwareBuffer> bufferRef = new AtomicReference<>();
        AtomicReference<Throwable> errorRef = new AtomicReference<>();
        AtomicBoolean abandoned = new AtomicBoolean(false);
        Object captureLock = new Object();
        takeScreenshot(Display.DEFAULT_DISPLAY, getMainExecutor(), new TakeScreenshotCallback() {
            @Override public void onSuccess(ScreenshotResult result) {
                HardwareBuffer buffer = result.getHardwareBuffer();
                synchronized (captureLock) {
                    if (abandoned.get()) {
                        buffer.close();
                        latch.countDown();
                        return;
                    }
                    bufferRef.set(buffer);
                    try {
                        Bitmap bitmap = Bitmap.wrapHardwareBuffer(buffer, result.getColorSpace());
                        if (bitmap == null) throw new IllegalStateException("bitmap conversion failed");
                        bitmapRef.set(bitmap);
                    } catch (Throwable error) {
                        errorRef.set(error);
                    } finally {
                        latch.countDown();
                    }
                }
            }
            @Override public void onFailure(int errorCode) {
                errorRef.set(new IllegalStateException("screenshot failed: " + errorCode));
                latch.countDown();
            }
        });
        try {
            if (!latch.await(6, TimeUnit.SECONDS)) throw new IllegalStateException("screenshot timeout");
            if (errorRef.get() != null) throw new IllegalStateException(errorRef.get().toString());
            Bitmap bitmap = bitmapRef.get();
            if (bitmap == null) throw new IllegalStateException("screenshot returned no bitmap");
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            if (!bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) {
                throw new IllegalStateException("PNG encoding failed");
            }
            byte[] data = out.toByteArray();
            JSONObject result = new JSONObject().put("bytes", data.length).put("sha256", sha256(data));
            if (includeBase64) result.put("base64", Base64.getEncoder().encodeToString(data));
            return result;
        } finally {
            synchronized (captureLock) {
                abandoned.set(true);
                Bitmap bitmap = bitmapRef.getAndSet(null);
                if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
                HardwareBuffer buffer = bufferRef.getAndSet(null);
                if (buffer != null) buffer.close();
            }
        }
    }

    private String sha256(byte[] data) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(data);
        StringBuilder out = new StringBuilder();
        for (byte value : digest) out.append(String.format("%02x", value));
        return out.toString();
    }
}
