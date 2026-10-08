package com.sahibex.companion;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.json.JSONArray;
import org.json.JSONObject;
import android.content.SharedPreferences;

public final class MainActivity extends Activity {
    private TextView status;
    private Button tapTarget;
    private EditText typeTarget;
    private final AtomicBoolean tapTriggered = new AtomicBoolean(false);

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        SharedPreferences p = getSharedPreferences("sahibex", MODE_PRIVATE);
        String token = p.getString("token", null);
        if (token == null) {
            byte[] b = new byte[32];
            new java.security.SecureRandom().nextBytes(b);
            token = android.util.Base64.encodeToString(
                b, android.util.Base64.NO_WRAP | android.util.Base64.URL_SAFE);
            p.edit().putString("token", token).apply();
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(40, 80, 40, 40);

        TextView info = new TextView(this);
        info.setText("SAHIBEX Android Companion\n\n"
            + "Accessibility Service must be ON.\n\n"
            + "Pairing token (keep private):\n" + token);
        info.setTextSize(16);

        Button settings = new Button(this);
        settings.setText("Open Accessibility Settings");
        settings.setOnClickListener(v ->
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));

        Button screenshot = new Button(this);
        screenshot.setText("Run Secure Screenshot Test");
        final String pairingToken = token;
        screenshot.setOnClickListener(v -> runScreenshotTest(pairingToken));

        Button fullTest = new Button(this);
        fullTest.setText("Run Phase 6B Full Device Test");
        fullTest.setOnClickListener(v -> runFullDeviceTest(pairingToken));

        tapTarget = new Button(this);
        tapTarget.setText("6B Tap Target");
        tapTarget.setOnClickListener(v -> {
            tapTriggered.set(true);
            status.setText("\nStatus: tap target received");
        });

        typeTarget = new EditText(this);
        typeTarget.setHint("6B Type Target");
        typeTarget.setSingleLine(true);

        status = new TextView(this);
        status.setText("\nStatus: ready");
        status.setTextSize(16);

        root.addView(info);
        root.addView(settings);
        root.addView(screenshot);
        root.addView(fullTest);
        root.addView(tapTarget);
        root.addView(typeTarget);
        root.addView(status);
        setContentView(root);
    }

    private void runScreenshotTest(String token) {
        status.setText("\nStatus: testing bridge + screenshot...");
        new Thread(() -> {
            try {
                JSONObject parsed = bridgeCall(token, "screenshot",
                    new JSONObject().put("include_base64", false));
                JSONObject result = parsed.optJSONObject("result");
                int code = parsed.optInt("_http", 0);
                String msg;
                if (code == 200 && parsed.optBoolean("success", false) && result != null) {
                    msg = "PASS\nHTTP 200\nScreenshot bytes: "
                        + result.optLong("bytes", 0)
                        + "\nSHA-256: " + result.optString("sha256", "");
                } else {
                    msg = "FAIL\nHTTP " + code + "\n" + parsed.toString();
                }
                final String finalMsg = msg;
                runOnUiThread(() -> status.setText("\nStatus: " + finalMsg));
            } catch (Throwable t) {
                runOnUiThread(() -> status.setText(
                    "\nStatus: FAIL\n" + t.getClass().getSimpleName() + ": " + t.getMessage()));
            }
        }).start();
    }

    private void runFullDeviceTest(String token) {
        status.setText("\nStatus: Phase 6B test running...");
        tapTriggered.set(false);
        new Thread(() -> {
            StringBuilder report = new StringBuilder();
            try {
                JSONObject tree = bridgeCall(token, "ui_tree", new JSONObject());
                boolean treePass = tree.optBoolean("success", false)
                    && tree.optJSONObject("result") != null
                    && tree.optJSONObject("result").optJSONArray("tree") != null;
                report.append("UI-tree: ").append(treePass ? "PASS" : "FAIL").append("\n");
                if (!treePass) throw new IllegalStateException("UI-tree unavailable");

                int[] loc = new int[2];
                runOnUiThread(() -> tapTarget.getLocationOnScreen(loc));
                Thread.sleep(300);
                JSONObject tap = bridgeCall(token, "tap",
                    new JSONObject().put("x", loc[0] + tapTarget.getWidth() / 2)
                        .put("y", loc[1] + tapTarget.getHeight() / 2));
                Thread.sleep(600);
                boolean tapPass = tap.optBoolean("success", false)
                    && tap.optJSONObject("result") != null
                    && tap.optJSONObject("result").optBoolean("accepted", false)
                    && tapTriggered.get();
                report.append("Tap/click: ").append(tapPass ? "PASS" : "FAIL").append("\n");
                if (!tapPass) throw new IllegalStateException("tap target was not activated");

                runOnUiThread(() -> {
                    typeTarget.requestFocus();
                    typeTarget.setSelection(typeTarget.length());
                });
                Thread.sleep(300);
                final String text = "SAHIBEX-6B-TEST";
                JSONObject typed = bridgeCall(token, "type_text",
                    new JSONObject().put("text", text));
                Thread.sleep(300);
                boolean typePass = typed.optBoolean("success", false)
                    && typed.optJSONObject("result") != null
                    && typed.optJSONObject("result").optBoolean("accepted", false)
                    && text.equals(typeTarget.getText().toString());
                report.append("Text typing: ").append(typePass ? "PASS" : "FAIL").append("\n");
                if (!typePass) throw new IllegalStateException("typed text verification failed");

                AlertDialog[] dialogRef = new AlertDialog[1];
                runOnUiThread(() -> {
                    dialogRef[0] = new AlertDialog.Builder(this)
                        .setTitle("SAHIBEX 6B Key Test")
                        .setMessage("Back key should close this dialog.")
                        .create();
                    dialogRef[0].show();
                });
                Thread.sleep(500);
                JSONObject key = bridgeCall(token, "keyevent",
                    new JSONObject().put("keycode", 4));
                Thread.sleep(500);
                boolean keyPass = key.optBoolean("success", false)
                    && key.optJSONObject("result") != null
                    && key.optJSONObject("result").optBoolean("accepted", false)
                    && (dialogRef[0] == null || !dialogRef[0].isShowing());
                report.append("Key press: ").append(keyPass ? "PASS" : "FAIL").append("\n");
                if (!keyPass) throw new IllegalStateException("back key verification failed");

                JSONObject shot = bridgeCall(token, "screenshot",
                    new JSONObject().put("include_base64", false));
                JSONObject sr = shot.optJSONObject("result");
                boolean shotPass = shot.optBoolean("success", false)
                    && sr != null && sr.optLong("bytes", 0) > 0
                    && sr.optString("sha256", "").length() == 64;
                report.append("Screenshot: ").append(shotPass ? "PASS" : "FAIL").append("\n");
                if (!shotPass) throw new IllegalStateException("final screenshot verification failed");

                runOnUiThread(() -> status.setText("\nStatus: PASS\n" + report.toString()
                    + "REAL DEVICE E2E PASS"));
            } catch (Throwable t) {
                final String failure = report.toString() + "FAIL: " + t.getMessage();
                runOnUiThread(() -> status.setText("\nStatus: FAIL\n" + failure));
            }
        }).start();
    }

    private JSONObject bridgeCall(String token, String action, JSONObject payload) throws Exception {
        String nonce = UUID.randomUUID().toString();
        String canonical = "{\"action\":" + JSONObject.quote(action)
            + ",\"nonce\":" + JSONObject.quote(nonce)
            + ",\"payload\":" + canonicalValue(payload)
            + ",\"protocol_version\":1}";
        String signature = hmacSha256(token, canonical);

        JSONObject body = new JSONObject();
        body.put("protocol_version", 1);
        body.put("action", action);
        body.put("nonce", nonce);
        body.put("payload", payload);
        body.put("signature", signature);

        HttpURLConnection c = (HttpURLConnection)
            new URL("http://127.0.0.1:38741/v1/action").openConnection();
        c.setRequestMethod("POST");
        c.setConnectTimeout(2000);
        c.setReadTimeout(8000);
        c.setDoOutput(true);
        c.setRequestProperty("Authorization", "Bearer " + token);
        c.setRequestProperty("Content-Type", "application/json");
        byte[] data = body.toString().getBytes(StandardCharsets.UTF_8);
        c.setFixedLengthStreamingMode(data.length);
        try (OutputStream out = c.getOutputStream()) { out.write(data); }
        int code = c.getResponseCode();
        InputStream stream = code >= 400 ? c.getErrorStream() : c.getInputStream();
        String response = readAll(stream);
        c.disconnect();
        JSONObject parsed = response.isEmpty() ? new JSONObject() : new JSONObject(response);
        parsed.put("_http", code);
        return parsed;
    }

    private static String canonicalValue(Object v) throws Exception {
        if (v == null || v == JSONObject.NULL) return "null";
        if (v instanceof JSONObject) {
            JSONObject o = (JSONObject) v;
            java.util.ArrayList<String> keys = new java.util.ArrayList<>();
            java.util.Iterator<String> it = o.keys();
            while (it.hasNext()) keys.add(it.next());
            java.util.Collections.sort(keys);
            StringBuilder s = new StringBuilder("{");
            for (int i = 0; i < keys.size(); i++) {
                if (i > 0) s.append(",");
                String k = keys.get(i);
                s.append(JSONObject.quote(k)).append(":").append(canonicalValue(o.get(k)));
            }
            return s.append("}").toString();
        }
        if (v instanceof String) return JSONObject.quote((String) v);
        if (v instanceof Boolean || v instanceof Number) return v.toString();
        if (v instanceof JSONArray) return v.toString();
        throw new IllegalArgumentException("unsupported canonical JSON value");
    }

    private static String readAll(InputStream in) throws Exception {
        if (in == null) return "";
        StringBuilder s = new StringBuilder();
        try (BufferedReader r = new BufferedReader(
                new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) s.append(line);
        }
        return s.toString();
    }

    private static String hmacSha256(String key, String text) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(key.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] raw = mac.doFinal(text.getBytes(StandardCharsets.UTF_8));
        StringBuilder out = new StringBuilder();
        for (byte b : raw) out.append(String.format("%02x", b));
        return out.toString();
    }
}
