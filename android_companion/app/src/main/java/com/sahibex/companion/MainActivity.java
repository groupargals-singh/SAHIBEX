package com.sahibex.companion;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.view.View;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.UUID;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.json.JSONObject;
import android.content.SharedPreferences;

public final class MainActivity extends Activity {
    private TextView status;

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

        final String pairingToken = token;
        Button test = new Button(this);
        test.setText("Run Secure Screenshot Test");
        test.setOnClickListener(v -> runScreenshotTest(pairingToken));

        status = new TextView(this);
        status.setText("\nStatus: ready");
        status.setTextSize(16);

        root.addView(info);
        root.addView(settings);
        root.addView(test);
        root.addView(status);
        setContentView(root);
    }

    private void runScreenshotTest(String token) {
        status.setText("\nStatus: testing bridge + screenshot...");
        new Thread(() -> {
            try {
                String nonce = UUID.randomUUID().toString();
                String canonical = "{\"action\":\"screenshot\",\"nonce\":\""
                    + jsonQuote(nonce) + "\",\"payload\":{},\"protocol_version\":1}";
                String signature = hmacSha256(token, canonical);
                JSONObject body = new JSONObject();
                body.put("protocol_version", 1);
                body.put("action", "screenshot");
                body.put("nonce", nonce);
                body.put("payload", new JSONObject());
                body.put("signature", signature);

                URL url = new URL("http://127.0.0.1:38741/");
                HttpURLConnection c = (HttpURLConnection) url.openConnection();
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

                JSONObject parsed = new JSONObject(response);
                JSONObject result = parsed.optJSONObject("result");
                String msg;
                if (code == 200 && parsed.optBoolean("success", false) && result != null) {
                    msg = "PASS\nHTTP 200\nScreenshot bytes: "
                        + result.optLong("bytes", 0)
                        + "\nSHA-256: " + result.optString("sha256", "");
                } else {
                    msg = "FAIL\nHTTP " + code + "\n" + response;
                }
                final String finalMsg = msg;
                runOnUiThread(() -> status.setText("\nStatus: " + finalMsg));
            } catch (Throwable t) {
                runOnUiThread(() -> status.setText(
                    "\nStatus: FAIL\n" + t.getClass().getSimpleName() + ": " + t.getMessage()));
            }
        }).start();
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

    private static String jsonQuote(String value) {
        return JSONObject.quote(value).substring(1, JSONObject.quote(value).length() - 1);
    }
}
