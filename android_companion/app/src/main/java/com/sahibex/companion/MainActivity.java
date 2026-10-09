package com.sahibex.companion;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import java.util.Locale;
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
    private static final int VOICE_REQUEST_CODE = 5107;
    private EditText mediaTokenInput;
    private TextView mediaStatus;
    private TextToSpeech textToSpeech;
    private volatile boolean ttsReady = false;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        SharedPreferences p = getSharedPreferences("sahibex", MODE_PRIVATE);
        textToSpeech = new TextToSpeech(this, result -> {
            if (result == TextToSpeech.SUCCESS && textToSpeech != null) {
                int languageResult = textToSpeech.setLanguage(Locale.getDefault());
                ttsReady = languageResult != TextToSpeech.LANG_MISSING_DATA
                    && languageResult != TextToSpeech.LANG_NOT_SUPPORTED;
            }
        });
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

        TextView mediaInfo = new TextView(this);
        mediaInfo.setText("\nSAHIBEX LIVE VOICE BRIDGE\nPaste the pairing token from Termux file: data/android_companion_media_token");
        mediaInfo.setTextSize(14);
        mediaTokenInput = new EditText(this);
        mediaTokenInput.setSingleLine(true);
        mediaTokenInput.setHint("SAHIBEX media pairing token");
        mediaTokenInput.setInputType(android.text.InputType.TYPE_CLASS_TEXT
            | android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);
        mediaTokenInput.setText(p.getString("media_token", ""));
        Button saveMediaToken = new Button(this);
        saveMediaToken.setText("Save Voice Pairing Token");
        saveMediaToken.setOnClickListener(v -> {
            String mediaToken = mediaTokenInput.getText().toString().trim();
            if (mediaToken.length() < 40) {
                mediaStatus.setText("Pairing token invalid; paste the full token from Termux.");
                return;
            }
            getSharedPreferences("sahibex", MODE_PRIVATE).edit()
                .putString("media_token", mediaToken).apply();
            mediaStatus.setText("Pairing token saved locally. Voice requests remain permission-gated.");
        });
        Button voiceInput = new Button(this);
        voiceInput.setText("Speak to SAHIBEX");
        voiceInput.setOnClickListener(v -> startVoiceRequest());
        mediaStatus = new TextView(this);
        mediaStatus.setText("Voice bridge: waiting for pairing and microphone action.");
        mediaStatus.setTextSize(14);

        root.addView(info);
        root.addView(mediaInfo);
        root.addView(mediaTokenInput);
        root.addView(saveMediaToken);
        root.addView(voiceInput);
        root.addView(mediaStatus);
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

    private void startVoiceRequest() {
        String token = getSharedPreferences("sahibex", MODE_PRIVATE)
            .getString("media_token", "");
        if (token.length() < 40) {
            mediaStatus.setText("Save the Termux pairing token first.");
            return;
        }
        try {
            Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            // Prefer Hindi (India) so Hindi/Hinglish speech is not misread as English.
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN");
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "hi-IN");
            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT,
                "Hindi/Hinglish mein dheere aur saaf boliye: Speak slowly and clearly");
            startActivityForResult(intent, VOICE_REQUEST_CODE);
            mediaStatus.setText("Listening through Android speech recognition...");
        } catch (Exception e) {
            mediaStatus.setText("Speech recognition unavailable: " + e.getClass().getSimpleName());
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != VOICE_REQUEST_CODE) return;
        if (resultCode != RESULT_OK || data == null) {
            mediaStatus.setText("Voice input cancelled or no speech recognized.");
            return;
        }
        java.util.ArrayList<String> matches = data.getStringArrayListExtra(
            RecognizerIntent.EXTRA_RESULTS);
        if (matches == null || matches.isEmpty()) {
            mediaStatus.setText("No usable speech transcript was returned.");
            return;
        }
        // Speech recognizers often return several alternatives. Let the user correct
        // recognition before any command reaches SAHIBEX.
        java.util.ArrayList<String> clean = new java.util.ArrayList<>();
        for (String item : matches) {
            if (item != null && !item.trim().isEmpty() && !clean.contains(item.trim())) {
                clean.add(item.trim());
            }
        }
        if (clean.isEmpty()) {
            mediaStatus.setText("No usable speech transcript was returned.");
            return;
        }
        String[] choices = clean.toArray(new String[0]);
        new AlertDialog.Builder(this)
            .setTitle("SAHIBEX heard — choose the correct words")
            .setItems(choices, (dialog, which) -> sendVoiceTranscript(choices[which]))
            .setNegativeButton("Cancel", (dialog, which) ->
                mediaStatus.setText("Voice request cancelled. Nothing was sent."))
            .show();
    }

    private void sendVoiceTranscript(final String transcript) {
        final String token = getSharedPreferences("sahibex", MODE_PRIVATE)
            .getString("media_token", "");
        mediaStatus.setText("Sending selected words to the local SAHIBEX brain...");
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                JSONObject request = new JSONObject().put("text", transcript);
                byte[] body = request.toString().getBytes(StandardCharsets.UTF_8);
                connection = (HttpURLConnection) new URL(
                    "http://127.0.0.1:38742/voice").openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(3000);
                connection.setReadTimeout(180000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Authorization", "Bearer " + token);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                connection.setFixedLengthStreamingMode(body.length);
                try (OutputStream out = connection.getOutputStream()) { out.write(body); }
                int code = connection.getResponseCode();
                InputStream responseStream = code >= 400
                    ? connection.getErrorStream() : connection.getInputStream();
                String responseText = readAll(responseStream);
                JSONObject response = responseText.isEmpty()
                    ? new JSONObject() : new JSONObject(responseText);
                String answer = response.optString("message",
                    response.optString("error", "SAHIBEX returned no response."));
                String display = "You said: " + transcript + "\n\nSAHIBEX: " + answer
                    + "\n\nHTTP: " + code + " | Verification: "
                    + response.optString("verification_status", "unknown");
                runOnUiThread(() -> {
                    mediaStatus.setText(display);
                    if (code == 200 && ttsReady && textToSpeech != null && !answer.trim().isEmpty()) {
                        textToSpeech.speak(answer, TextToSpeech.QUEUE_FLUSH, null, "sahibex-voice-response");
                    }
                });
            } catch (Throwable e) {
                String error = "Voice bridge failed: " + e.getClass().getSimpleName()
                    + ". Ensure the SAHIBEX media bridge is running in Termux.";
                runOnUiThread(() -> mediaStatus.setText(error));
            } finally {
                if (connection != null) connection.disconnect();
            }
        }).start();
    }

    @Override protected void onDestroy() {
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
        }
        super.onDestroy();
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
