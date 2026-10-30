package com.sahibex.companion;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.provider.Settings;
import android.media.AudioFormat;
import android.media.MediaPlayer;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import android.view.View;
import android.view.Gravity;
import android.graphics.Color;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Shader;
import android.graphics.RadialGradient;
import android.graphics.drawable.GradientDrawable;
import android.widget.ScrollView;
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
    private static final int AUDIO_PERMISSION_REQUEST = 5108;
    private static final int CAMERA_PERMISSION_REQUEST = 5109;
    private static final int AUDIO_SAMPLE_RATE = 16000;
    private static final int MAX_RECORDING_SECONDS = 20;
    private volatile AudioRecord activeAudioRecord;
    private volatile boolean recordingActive = false;
    private volatile String asrLanguageHint = "auto";
    private volatile Thread audioCaptureThread;
    private Button voiceInputButton;
    private EditText mediaTokenInput;
    private TextView mediaStatus;
    private EditText chatInput;
    private TextView chatLog;
    private Button sendChatButton;
    private Button cameraButton;
    private volatile MediaPlayer activeNeuralPlayer;

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
        root.setPadding(dp(20), dp(24), dp(20), dp(28));
        root.setBackgroundColor(Color.rgb(7, 12, 24));

        TextView brand = new TextView(this);
        brand.setText("S A H I B E X  /  MASTER BRAIN");
        brand.setTextColor(Color.rgb(102, 235, 224));
        brand.setTextSize(13);
        brand.setGravity(Gravity.CENTER);
        root.addView(brand, new LinearLayout.LayoutParams(-1, dp(32)));
        BrainCoreView brainCore = new BrainCoreView(this);
        root.addView(brainCore, new LinearLayout.LayoutParams(-1, dp(156)));
        TextView tagline = new TextView(this);
        tagline.setText("SEE  •  THINK  •  LEARN  •  EXECUTE");
        tagline.setTextColor(Color.rgb(157, 177, 211));
        tagline.setTextSize(11);
        tagline.setGravity(Gravity.CENTER);
        root.addView(tagline, new LinearLayout.LayoutParams(-1, dp(26)));

        Button diagnosticsButton = new Button(this);
        diagnosticsButton.setText("LIVE 3D BRAIN HEALTH & ERROR DIAGNOSTICS");
        diagnosticsButton.setTextColor(Color.rgb(4, 18, 30));
        diagnosticsButton.setBackground(accentBackground());
        diagnosticsButton.setOnClickListener(v -> loadDiagnostics());
        LinearLayout.LayoutParams diagnosticsParams = new LinearLayout.LayoutParams(-1, dp(52));
        diagnosticsParams.topMargin = dp(10);
        diagnosticsParams.bottomMargin = dp(12);
        root.addView(diagnosticsButton, diagnosticsParams);

        TextView info = new TextView(this);
        info.setText("SECURE COMPANION PAIRING\nPairing token (keep private):\n" + token);
        info.setTextColor(Color.rgb(180, 197, 220));
        info.setTextSize(12);
        info.setPadding(dp(14), dp(12), dp(14), dp(12));
        info.setBackground(panelBackground());
        root.addView(info);

        Button rotatePairingToken = new Button(this);
        rotatePairingToken.setText("Rotate Companion Pairing Token");
        rotatePairingToken.setOnClickListener(v -> new AlertDialog.Builder(this)
            .setTitle("Rotate pairing token?")
            .setMessage("The old token will stop working. You must save the newly shown token securely in Termux before using Main Brain control.")
            .setNegativeButton("Cancel", (dialog, which) -> dialog.dismiss())
            .setPositiveButton("ROTATE TOKEN", (dialog, which) -> {
                byte[] fresh = new byte[32];
                new java.security.SecureRandom().nextBytes(fresh);
                String freshToken = android.util.Base64.encodeToString(
                    fresh, android.util.Base64.NO_WRAP | android.util.Base64.URL_SAFE);
                boolean saved = p.edit().putString("token", freshToken).commit();
                if (saved) {
                    new AlertDialog.Builder(this)
                        .setTitle("Pairing token rotated")
                        .setMessage("A new token has been saved. Close this dialog, then the app will refresh to show it. The old token is invalid.")
                        .setPositiveButton("REFRESH", (d, w) -> recreate())
                        .setCancelable(false)
                        .show();
                } else {
                    status.setText("\nERROR: token rotation could not be saved; old token remains active.");
                }
            }).show());

        Button settings = new Button(this);
        settings.setText("Open Accessibility Settings");
        settings.setOnClickListener(v ->
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));

        Button emergencyStop = new Button(this);
        emergencyStop.setText("EMERGENCY STOP — Disable UI Control");
        emergencyStop.setOnClickListener(v -> new AlertDialog.Builder(this)
            .setTitle("Stop SAHIBEX UI control?")
            .setMessage("This immediately blocks remote tap, swipe, typing, key and screenshot actions. Resume requires a separate local confirmation.")
            .setNegativeButton("Cancel", (dialog, which) -> dialog.dismiss())
            .setPositiveButton("STOP NOW", (dialog, which) -> {
                SahibexAccessibilityService.engageEmergencyStopLocally();
                boolean saved = p.edit().putBoolean("accessibility_stopped", true).commit();
                status.setText(saved
                    ? "\nStatus: EMERGENCY STOP ENGAGED — UI control blocked."
                    : "\nEMERGENCY STOP ACTIVE IN MEMORY; persistence failed. Keep app open and retry.");
            }).show());

        Button resumeControl = new Button(this);
        resumeControl.setText("Resume UI Control (local confirmation)");
        resumeControl.setOnClickListener(v -> new AlertDialog.Builder(this)
            .setTitle("Resume SAHIBEX UI control?")
            .setMessage("Only resume if you are physically present and intend to re-enable remote accessibility actions.")
            .setNegativeButton("Keep Stopped", (dialog, which) -> dialog.dismiss())
            .setPositiveButton("RESUME", (dialog, which) -> {
                boolean resumed = SahibexAccessibilityService.resumeEmergencyStopLocally(p);
                status.setText(resumed
                    ? "\nStatus: UI control resumed by local confirmation."
                    : "\nResume failed to persist; UI control remains stopped.");
            }).show());

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
        mediaInfo.setText("\nVOICE BRIDGE\nPair with the local Termux media bridge to enable speech.");
        mediaInfo.setTextColor(Color.rgb(102, 235, 224));
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
        voiceInputButton = new Button(this);
        voiceInputButton.setText("VOICE");
        voiceInputButton.setTextColor(Color.rgb(102, 235, 224));
        voiceInputButton.setBackground(panelBackground());
        voiceInputButton.setOnClickListener(v -> startVoiceRequest());
        cameraButton = new Button(this);
        cameraButton.setText("CAM");
        cameraButton.setTextColor(Color.rgb(102, 235, 224));
        cameraButton.setBackground(panelBackground());
        cameraButton.setOnClickListener(v -> startCameraConversation());
        mediaStatus = new TextView(this);
        mediaStatus.setText("Voice bridge: waiting for pairing and microphone action.");
        mediaStatus.setTextColor(Color.rgb(180, 197, 220));
        mediaStatus.setTextSize(13);
        mediaStatus.setPadding(dp(12), dp(10), dp(12), dp(10));
        mediaStatus.setBackground(panelBackground());

        TextView chatHeading = new TextView(this);
        chatHeading.setText("TALK TO SAHIBEX");
        chatHeading.setTextColor(Color.rgb(102, 235, 224));
        chatHeading.setTextSize(14);
        chatHeading.setPadding(0, dp(18), 0, dp(8));
        chatLog = new TextView(this);
        chatLog.setText("SAHIBEX\nNamaste! Type a message below, or pair the voice bridge and speak.");
        chatLog.setTextColor(Color.rgb(230, 239, 255));
        chatLog.setTextSize(15);
        chatLog.setPadding(dp(14), dp(14), dp(14), dp(14));
        chatLog.setGravity(Gravity.TOP | Gravity.START);
        chatLog.setBackground(panelBackground());
        ScrollView chatScroll = new ScrollView(this);
        chatScroll.setFillViewport(true);
        chatScroll.addView(chatLog, new ScrollView.LayoutParams(-1, -2));
        root.addView(chatHeading);
        root.addView(chatScroll, new LinearLayout.LayoutParams(-1, dp(210)));
        LinearLayout composer = new LinearLayout(this);
        composer.setOrientation(LinearLayout.HORIZONTAL);
        composer.setGravity(Gravity.CENTER_VERTICAL);
        chatInput = new EditText(this);
        chatInput.setHint("Message SAHIBEX…");
        chatInput.setHintTextColor(Color.rgb(122, 143, 176));
        chatInput.setTextColor(Color.WHITE);
        chatInput.setTextSize(15);
        chatInput.setSingleLine(false);
        chatInput.setMinLines(1);
        chatInput.setMaxLines(4);
        chatInput.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEND);
        chatInput.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES | android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        chatInput.setPadding(dp(12), dp(10), dp(12), dp(10));
        chatInput.setBackground(panelBackground());
        composer.addView(chatInput, new LinearLayout.LayoutParams(0, -2, 1f));
        LinearLayout.LayoutParams voiceParams = new LinearLayout.LayoutParams(-2, dp(52));
        voiceParams.leftMargin = dp(6);
        composer.addView(voiceInputButton, voiceParams);
        LinearLayout.LayoutParams cameraParams = new LinearLayout.LayoutParams(-2, dp(52));
        cameraParams.leftMargin = dp(6);
        composer.addView(cameraButton, cameraParams);
        sendChatButton = new Button(this);
        sendChatButton.setText("SEND");
        sendChatButton.setTextColor(Color.rgb(4, 18, 30));
        sendChatButton.setBackground(accentBackground());
        LinearLayout.LayoutParams sendParams = new LinearLayout.LayoutParams(-2, dp(52));
        sendParams.leftMargin = dp(8);
        composer.addView(sendChatButton, sendParams);
        sendChatButton.setOnClickListener(v -> sendTypedMessage());
        chatInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == android.view.inputmethod.EditorInfo.IME_ACTION_SEND) { sendTypedMessage(); return true; }
            return false;
        });
        LinearLayout.LayoutParams composerParams = new LinearLayout.LayoutParams(-1, -2);
        composerParams.topMargin = dp(8);
        root.addView(composer, composerParams);

        root.addView(rotatePairingToken);
        root.addView(mediaInfo);
        root.addView(mediaTokenInput);
        root.addView(saveMediaToken);
        root.addView(mediaStatus);
        root.addView(settings);
        root.addView(emergencyStop);
        root.addView(resumeControl);
        root.addView(screenshot);
        root.addView(fullTest);
        root.addView(tapTarget);
        root.addView(typeTarget);
        root.addView(status);
        ScrollView page = new ScrollView(this);
        page.setFillViewport(true);
        page.setBackgroundColor(Color.rgb(7, 12, 24));
        page.addView(root);
        setContentView(page);
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
        if (recordingActive) {
            stopVoiceRecording();
            return;
        }
        String token = getSharedPreferences("sahibex", MODE_PRIVATE)
            .getString("media_token", "");
        if (token.length() < 40) {
            mediaStatus.setText("Save the SAHIBEX media pairing token first.");
            return;
        }
        chooseVoiceLanguage();
    }

    private void chooseVoiceLanguage() {
        final String[] labels = {"Hindi / Hinglish", "English", "Auto detect"};
        new AlertDialog.Builder(this)
            .setTitle("Choose speaking language")
            .setItems(labels, (dialog, which) -> {
                asrLanguageHint = which == 0 ? "hi" : which == 1 ? "en" : "auto";
                if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                        != PackageManager.PERMISSION_GRANTED) {
                    requestPermissions(new String[] { Manifest.permission.RECORD_AUDIO },
                        AUDIO_PERMISSION_REQUEST);
                    mediaStatus.setText("Microphone permission is required for local speech recognition.");
                } else {
                    beginVoiceRecording();
                }
            })
            .setOnCancelListener(dialog -> mediaStatus.setText("Voice request cancelled; microphone was not started."))
            .show();
    }

    @Override public void onRequestPermissionsResult(int requestCode,
            String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == CAMERA_PERMISSION_REQUEST) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                openCameraConversation();
            } else {
                mediaStatus.setText("Camera permission denied. Camera was not opened.");
            }
            return;
        }
        if (requestCode != AUDIO_PERMISSION_REQUEST) return;
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            beginVoiceRecording();
        } else {
            mediaStatus.setText("Microphone permission denied. Nothing was recorded or sent.");
        }
    }

    private void startCameraConversation() {
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] { Manifest.permission.CAMERA }, CAMERA_PERMISSION_REQUEST);
            mediaStatus.setText("Camera permission is required for live preview and basic motion detection.");
            return;
        }
        openCameraConversation();
    }

    private void openCameraConversation() {
        startActivity(new Intent(this, CameraConversationActivity.class));
    }

    private void beginVoiceRecording() {
        if (recordingActive) return;
        int minBuffer = AudioRecord.getMinBufferSize(AUDIO_SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        if (minBuffer <= 0) {
            mediaStatus.setText("This device cannot initialize 16 kHz microphone capture.");
            return;
        }
        AudioRecord recorder = null;
        try {
            recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION,
                AUDIO_SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT, Math.max(minBuffer, 8192));
            if (recorder.getState() != AudioRecord.STATE_INITIALIZED) {
                recorder.release();
                mediaStatus.setText("SAHIBEX microphone capture could not initialize.");
                return;
            }
            recorder.startRecording();
        } catch (Throwable error) {
            if (recorder != null) {
                try { recorder.release(); } catch (Throwable ignored) { }
            }
            mediaStatus.setText("Microphone start failed: " + error.getClass().getSimpleName());
            return;
        }
        activeAudioRecord = recorder;
        recordingActive = true;
        voiceInputButton.setText("Stop recording and transcribe");
        mediaStatus.setText("SAHIBEX local listening ON — speak now. Tap again to stop (max 20 seconds).\n"
            + "Audio remains on this phone; no Android speech-recognition service is called.");
        final AudioRecord capture = recorder;
        audioCaptureThread = new Thread(() -> {
            ByteArrayOutputStream pcm = new ByteArrayOutputStream();
            byte[] chunk = new byte[4096];
            long deadline = System.currentTimeMillis() + MAX_RECORDING_SECONDS * 1000L;
            try {
                while (recordingActive && System.currentTimeMillis() < deadline) {
                    int count = capture.read(chunk, 0, chunk.length);
                    if (count > 0) {
                        if (pcm.size() + count > AUDIO_SAMPLE_RATE * 2 * MAX_RECORDING_SECONDS) break;
                        pcm.write(chunk, 0, count);
                    } else if (count < 0) {
                        break;
                    }
                }
            } catch (Throwable ignored) {
                // The UI reports an empty/invalid capture without exposing audio or stack traces.
            } finally {
                recordingActive = false;
                try { capture.stop(); } catch (Throwable ignored) { }
                try { capture.release(); } catch (Throwable ignored) { }
                activeAudioRecord = null;
                byte[] rawPcm = pcm.toByteArray();
                runOnUiThread(() -> {
                    voiceInputButton.setText("Speak to SAHIBEX (local AI)");
                    if (rawPcm.length < AUDIO_SAMPLE_RATE / 2) {
                        mediaStatus.setText("No usable audio captured. Check microphone access and try again.");
                        return;
                    }
                    mediaStatus.setText("Audio captured. Running SAHIBEX's local offline speech model...");
                    transcribeCapturedAudio(toPcmWav(rawPcm));
                });
            }
        }, "sahibex-local-microphone");
        audioCaptureThread.start();
    }

    private void stopVoiceRecording() {
        recordingActive = false;
        mediaStatus.setText("Stopping microphone and finalizing local audio...");
    }

    private byte[] toPcmWav(byte[] pcm) {
        ByteBuffer header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN);
        header.put(new byte[] {'R','I','F','F'});
        header.putInt(36 + pcm.length);
        header.put(new byte[] {'W','A','V','E','f','m','t',' '});
        header.putInt(16);
        header.putShort((short) 1); // PCM
        header.putShort((short) 1); // mono
        header.putInt(AUDIO_SAMPLE_RATE);
        header.putInt(AUDIO_SAMPLE_RATE * 2);
        header.putShort((short) 2);
        header.putShort((short) 16);
        header.put(new byte[] {'d','a','t','a'});
        header.putInt(pcm.length);
        ByteArrayOutputStream wav = new ByteArrayOutputStream(44 + pcm.length);
        try {
            wav.write(header.array());
            wav.write(pcm);
        } catch (java.io.IOException impossible) {
            throw new IllegalStateException("In-memory WAV preparation failed", impossible);
        }
        return wav.toByteArray();
    }

    private void transcribeCapturedAudio(final byte[] wavBytes) {
        final String token = getSharedPreferences("sahibex", MODE_PRIVATE)
            .getString("media_token", "");
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(
                    "http://127.0.0.1:38742/transcribe").openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(120000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Authorization", "Bearer " + token);
                connection.setRequestProperty("Content-Type", "audio/wav");
                connection.setRequestProperty("X-SAHIBEX-Language", asrLanguageHint);
                connection.setFixedLengthStreamingMode(wavBytes.length);
                try (OutputStream out = connection.getOutputStream()) { out.write(wavBytes); }
                int code = connection.getResponseCode();
                InputStream stream = code >= 400 ? connection.getErrorStream() : connection.getInputStream();
                String body = readAll(stream);
                JSONObject response = body.isEmpty() ? new JSONObject() : new JSONObject(body);
                if (code != 200 || !response.optBoolean("success", false)) {
                    String detail = response.optString("message", response.optString("error", "local_asr_failed"));
                    runOnUiThread(() -> mediaStatus.setText("SAHIBEX local recognition unavailable: "
                        + detail + "\nNo Android/cloud recognizer fallback was used."));
                    return;
                }
                String transcript = response.optString("transcript", "").trim();
                String engine = response.optString("engine", "local engine");
                String language = response.optString("language", "auto");
                if (transcript.isEmpty()) {
                    runOnUiThread(() -> mediaStatus.setText("SAHIBEX did not detect clear speech. Please try again."));
                    return;
                }
                runOnUiThread(() -> reviewLocalTranscript(transcript, engine, language));
            } catch (Throwable error) {
                runOnUiThread(() -> mediaStatus.setText("SAHIBEX local speech bridge failed: "
                    + error.getClass().getSimpleName()
                    + "\nCheck that the local offline ASR runtime and media bridge are installed and running."));
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "sahibex-local-transcription").start();
    }

    private void reviewLocalTranscript(String transcript, String engine, String language) {
        EditText edit = new EditText(this);
        edit.setText(transcript);
        edit.setSingleLine(false);
        edit.setMinLines(2);
        edit.setMaxLines(6);
        edit.setInputType(android.text.InputType.TYPE_CLASS_TEXT
            | android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE
            | android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        new AlertDialog.Builder(this)
            .setTitle("SAHIBEX local AI heard")
            .setMessage("Engine: " + engine + " | Language: " + language
                + "\nCheck spelling before sending; uncertain words can be edited.")
            .setView(edit)
            .setPositiveButton("Confirm and send", (dialog, which) -> {
                String confirmed = edit.getText().toString().trim();
                if (confirmed.isEmpty()) {
                    mediaStatus.setText("Empty transcript cancelled; nothing was sent.");
                } else {
                    sendVoiceTranscript(confirmed);
                }
            })
            .setNegativeButton("Cancel", (dialog, which) ->
                mediaStatus.setText("Voice request cancelled. Transcript was not sent to Main Brain."))
            .show();
    }

    private void sendTypedMessage() {
        if (chatInput == null || sendChatButton == null) return;
        final String message = chatInput.getText().toString().trim();
        if (message.isEmpty()) return;
        final String token = getSharedPreferences("sahibex", MODE_PRIVATE).getString("media_token", "");
        if (token.length() < 40) {
            appendChat("SYSTEM", "Pair the local media bridge first using the token from Termux.");
            mediaStatus.setText("Typing is ready, but the local SAHIBEX bridge is not paired.");
            return;
        }
        chatInput.setText("");
        appendChat("YOU", message);
        appendChat("SAHIBEX", "Thinking…");
        sendChatButton.setEnabled(false);
        mediaStatus.setText("Sending your message to the local SAHIBEX Master Brain…");
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                JSONObject request = new JSONObject().put("text", message);
                byte[] body = request.toString().getBytes(StandardCharsets.UTF_8);
                connection = (HttpURLConnection) new URL("http://127.0.0.1:38742/voice").openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(3000);
                connection.setReadTimeout(180000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Authorization", "Bearer " + token);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                connection.setFixedLengthStreamingMode(body.length);
                try (OutputStream out = connection.getOutputStream()) { out.write(body); }
                int code = connection.getResponseCode();
                InputStream responseStream = code >= 400 ? connection.getErrorStream() : connection.getInputStream();
                String responseText = readAll(responseStream);
                JSONObject response = responseText.isEmpty() ? new JSONObject() : new JSONObject(responseText);
                String answer = response.optString("message", response.optString("error", "SAHIBEX returned no response."));
                boolean ok = code == 200 && response.optBoolean("success", false) && !answer.trim().isEmpty();
                String finalAnswer = ok ? answer : "Request failed safely (HTTP " + code + "): " + answer;
                runOnUiThread(() -> {
                    replaceThinkingWith(finalAnswer);
                    mediaStatus.setText("Chat status: " + (ok ? "response received" : "request failed") + " | Verification: " + response.optString("verification_status", "unknown"));
                    sendChatButton.setEnabled(true);
                    if (ok) {
                        String lang = response.optString("answer_language", "und");
                        boolean hindi = answer.codePoints().anyMatch(cp -> cp >= 0x0900 && cp <= 0x097F) || lang.equals("hi") || lang.equals("hi-Latn");
                        requestNeuralSpeech(answer, hindi ? "hi" : "en", "SAHIBEX chat reply");
                    }
                });
            } catch (Throwable error) {
                runOnUiThread(() -> {
                    replaceThinkingWith("Local SAHIBEX bridge unavailable. Check bridge status in Termux and try again.");
                    mediaStatus.setText("Chat connection failed: " + error.getClass().getSimpleName());
                    sendChatButton.setEnabled(true);
                });
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "sahibex-typed-chat").start();
    }

    private void loadDiagnostics() {
        final String token = getSharedPreferences("sahibex", MODE_PRIVATE)
            .getString("media_token", "");
        if (token.length() < 40) {
            new AlertDialog.Builder(this).setTitle("SAHIBEX Diagnostics")
                .setMessage("Media bridge pairing is required. Save the private media pairing token in the app first.")
                .setPositiveButton("OK", null).show();
            return;
        }
        final AlertDialog loading = new AlertDialog.Builder(this)
            .setTitle("SAHIBEX Live Diagnostics")
            .setMessage("Collecting read-only health and error evidence…")
            .setNegativeButton("Close", null).create();
        loading.show();
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL("http://127.0.0.1:38742/diagnostics").openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(3000);
                connection.setReadTimeout(15000);
                connection.setRequestProperty("Authorization", "Bearer " + token);
                int code = connection.getResponseCode();
                InputStream stream = code >= 400 ? connection.getErrorStream() : connection.getInputStream();
                String raw = readAll(stream);
                JSONObject data = raw.isEmpty() ? new JSONObject() : new JSONObject(raw);
                runOnUiThread(() -> {
                    if (!isFinishing()) {
                        loading.dismiss();
                        showDiagnosticDashboard(data, code);
                    }
                });
            } catch (Throwable error) {
                runOnUiThread(() -> {
                    loading.dismiss();
                    new AlertDialog.Builder(this).setTitle("Diagnostics unavailable")
                        .setMessage("Could not retrieve the local report: " + error.getClass().getSimpleName()
                            + "\nCheck that the Termux media bridge is running and paired.")
                        .setPositiveButton("OK", null).show();
                });
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "sahibex-diagnostics").start();
    }

    private void showDiagnosticDashboard(JSONObject data, int httpCode) {
        int pad = dp(14);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(pad, pad, pad, pad);
        content.setBackgroundColor(Color.rgb(7, 12, 24));

        TextView heading = diagnosticText("SAHIBEX  /  LIVE SYSTEM DIGITAL TWIN", 13,
            Color.rgb(102, 235, 224), true);
        content.addView(heading);
        BrainCoreView hologram = new BrainCoreView(this);
        content.addView(hologram, new LinearLayout.LayoutParams(-1, dp(170)));

        String overall = data.optString("overall_status", "UNKNOWN");
        int overallColor = overall.equals("LIMITED_CHECKS_PASS") ? Color.rgb(70, 225, 155)
            : Color.rgb(255, 190, 90);
        content.addView(diagnosticText("HTTP " + httpCode + "   •   " + overall, 15, overallColor, true));
        content.addView(diagnosticText("READ-ONLY INSPECTION  •  No automatic repairs or protected changes", 11,
            Color.rgb(158, 178, 207), false));

        JSONObject summary = data.optJSONObject("summary");
        if (summary != null) {
            LinearLayout metrics = new LinearLayout(this);
            metrics.setOrientation(LinearLayout.HORIZONTAL);
            metrics.setPadding(0, dp(12), 0, dp(12));
            addMetric(metrics, summary.optInt("internal_handlers_registered") + "/" + summary.optInt("internal_roles_defined"), "HANDLERS", Color.rgb(72, 225, 180));
            addMetric(metrics, summary.optInt("live_services_online") + "/" + summary.optInt("live_services_checked"), "SERVICES", Color.rgb(110, 190, 255));
            addMetric(metrics, String.valueOf(summary.optInt("recent_error_records")), "LOG EVENTS", Color.rgb(255, 184, 90));
            content.addView(metrics);
        }

        addDiagnosticSection(content, "01  CORE BRAIN COMPONENTS", "Source discovery is not a runtime function test.");
        JSONArray brains = data.optJSONArray("brains");
        if (brains != null) for (int i = 0; i < brains.length(); i++) {
            JSONObject item = brains.optJSONObject(i);
            if (item == null) continue;
            boolean present = item.optBoolean("file_present", false);
            addDiagnosticRow(content, item.optString("name"), item.optString("status"),
                item.optString("file"), present ? Color.rgb(73, 220, 155) : Color.rgb(255, 105, 105));
        }

        addDiagnosticSection(content, "02  INTERNAL BRAIN ARMY  /  61 ROLES", "Registered = MasterBrain contains an explicit handler registration. It does not mean the handler passed a function test.");
        JSONObject roleSummary = data.optJSONObject("role_summary");
        if (roleSummary != null) {
            content.addView(diagnosticText("Defined: " + roleSummary.optInt("defined_roles")
                + "   Registered: " + roleSummary.optInt("registered_handlers")
                + "   Unregistered: " + roleSummary.optInt("unregistered_handlers"), 12,
                Color.rgb(105, 220, 190), true));
        }
        JSONArray roles = data.optJSONArray("internal_roles");
        if (roles != null) for (int i = 0; i < roles.length(); i++) {
            JSONObject item = roles.optJSONObject(i);
            if (item == null) continue;
            boolean registered = item.optBoolean("handler_registered_in_master_brain", false);
            addDiagnosticRow(content, item.optString("role_id"),
                registered ? "HANDLER REGISTERED • NOT FUNCTION TESTED" : "DEFINED • NO HANDLER",
                item.optString("purpose"), registered ? Color.rgb(90, 195, 255) : Color.rgb(255, 105, 105));
        }

        addDiagnosticSection(content, "03  LIVE LOCAL SERVICES", "TCP reachability checks only.");
        JSONArray services = data.optJSONArray("services");
        if (services != null) for (int i = 0; i < services.length(); i++) {
            JSONObject item = services.optJSONObject(i);
            if (item == null) continue;
            boolean online = item.optBoolean("online", false);
            addDiagnosticRow(content, item.optString("name"), online ? "ONLINE" : "OFFLINE",
                "127.0.0.1:" + item.optInt("port"), online ? Color.rgb(73, 220, 155) : Color.rgb(255, 105, 105));
        }

        addDiagnosticSection(content, "04  DATA-FLOW ARCHITECTURE", "Dashed concept path only; request-level tracing is not yet implemented.");
        JSONArray edges = data.optJSONArray("data_flow_edges");
        if (edges != null) for (int i = 0; i < edges.length(); i++) {
            JSONObject edge = edges.optJSONObject(i);
            if (edge != null) content.addView(diagnosticText(
                "◉  " + edge.optString("from") + "   →   " + edge.optString("to") + "   [NOT LIVE-TRACED]",
                12, Color.rgb(112, 197, 235), false));
        }

        addDiagnosticSection(content, "05  RECENT REAL DISPATCH FLOW", "These are actual internal-role handler calls recorded in this process. Request text and payloads are never stored.");
        JSONArray dispatches = data.optJSONArray("recent_dispatch_events");
        if (dispatches == null || dispatches.length() == 0) {
            content.addView(diagnosticText("No internal-role dispatch events recorded in this process yet.",
                11, Color.rgb(164, 182, 208), false));
        } else for (int i = dispatches.length() - 1; i >= 0; i--) {
            JSONObject event = dispatches.optJSONObject(i);
            if (event == null) continue;
            String duration = event.has("duration_ms") ? " • " + event.optDouble("duration_ms") + " ms" : "";
            addDiagnosticRow(content, event.optString("role_id"), event.optString("status") + duration,
                "Unix time: " + event.optDouble("timestamp_unix"), event.optString("status").startsWith("HANDLER_ERROR")
                    ? Color.rgb(255, 105, 105) : Color.rgb(90, 195, 255));
        }

        addDiagnosticSection(content, "06  ERRORS  /  TRACEBACK LOCATOR", "Historical log records; inspect timestamps and reproduce before calling a fault current.");
        JSONArray errors = data.optJSONArray("errors");
        if (errors == null || errors.length() == 0) {
            content.addView(diagnosticText("No matching recent log records. This does not prove there are no errors.",
                12, Color.rgb(175, 190, 215), false));
        } else for (int i = 0; i < errors.length(); i++) {
            JSONObject item = errors.optJSONObject(i);
            if (item == null) continue;
            String location = item.optString("source_file", "source frame unavailable");
            if (!item.isNull("source_line")) location += ":" + item.optInt("source_line") + " in " + item.optString("function");
            String age = item.optLong("log_modified_at_unix", 0) > 0
                ? "Log file modified: " + new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.getDefault())
                    .format(new java.util.Date(item.optLong("log_modified_at_unix") * 1000L)) : "Log timestamp unavailable";
            addDiagnosticRow(content, item.optString("severity") + "  •  " + item.optString("log") + ":" + item.optInt("line"),
                location + "\n" + age, item.optString("message"), item.optString("severity").equals("WARNING")
                    ? Color.rgb(255, 190, 90) : Color.rgb(255, 105, 105));
        }

        addDiagnosticSection(content, "06  KNOWN LIMITATIONS", "No green status is inferred from a file name or registration alone.");
        JSONArray limitations = data.optJSONArray("limitations");
        if (limitations != null) for (int i = 0; i < limitations.length(); i++)
            content.addView(diagnosticText("•  " + limitations.optString(i), 11, Color.rgb(164, 182, 208), false));

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        scroll.addView(content);
        new AlertDialog.Builder(this).setTitle("SAHIBEX 3D Diagnostic Command Center")
            .setView(scroll)
            .setPositiveButton("CLOSE", null)
            .setNeutralButton("REFRESH", (dialog, which) -> loadDiagnostics())
            .show();
    }

    private TextView diagnosticText(String value, float size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setPadding(0, dp(5), 0, dp(5));
        if (bold) view.setTypeface(null, android.graphics.Typeface.BOLD);
        return view;
    }

    private void addDiagnosticSection(LinearLayout parent, String title, String subtitle) {
        TextView heading = diagnosticText(title, 13, Color.rgb(102, 235, 224), true);
        heading.setPadding(0, dp(15), 0, dp(2));
        parent.addView(heading);
        parent.addView(diagnosticText(subtitle, 10, Color.rgb(137, 158, 190), false));
    }

    private void addDiagnosticRow(LinearLayout parent, String title, String statusText,
            String detail, int statusColor) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.VERTICAL);
        row.setPadding(dp(10), dp(7), dp(10), dp(7));
        row.setBackground(panelBackground());
        TextView name = diagnosticText(title, 12, Color.WHITE, true);
        TextView state = diagnosticText(statusText, 10, statusColor, true);
        TextView info = diagnosticText(detail, 10, Color.rgb(153, 174, 205), false);
        row.addView(name);
        row.addView(state);
        row.addView(info);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = dp(4);
        parent.addView(row, params);
    }

    private void addMetric(LinearLayout parent, String value, String label, int color) {
        LinearLayout metric = new LinearLayout(this);
        metric.setOrientation(LinearLayout.VERTICAL);
        metric.setGravity(Gravity.CENTER);
        metric.setPadding(dp(5), dp(8), dp(5), dp(8));
        metric.setBackground(panelBackground());
        TextView number = diagnosticText(value, 18, color, true);
        number.setGravity(Gravity.CENTER);
        TextView caption = diagnosticText(label, 9, Color.rgb(155, 175, 204), true);
        caption.setGravity(Gravity.CENTER);
        metric.addView(number);
        metric.addView(caption);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, -2, 1f);
        params.setMargins(dp(3), 0, dp(3), 0);
        parent.addView(metric, params);
    }

    private void appendChat(String speaker, String message) {
        if (chatLog == null) return;
        String current = chatLog.getText().toString();
        if (current.startsWith("SAHIBEX\nNamaste!")) current = "";
        chatLog.setText(current + (current.isEmpty() ? "" : "\n\n") + speaker + "\n" + message);
    }

    private void replaceThinkingWith(String answer) {
        if (chatLog == null) return;
        String current = chatLog.getText().toString();
        int index = current.lastIndexOf("SAHIBEX\nThinking…");
        if (index >= 0) current = current.substring(0, index) + "SAHIBEX\n" + answer;
        else current += "\n\nSAHIBEX\n" + answer;
        chatLog.setText(current);
    }

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private GradientDrawable panelBackground() {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(Color.rgb(15, 25, 43));
        shape.setCornerRadius(dp(16));
        shape.setStroke(dp(1), Color.rgb(36, 64, 88));
        return shape;
    }

    private GradientDrawable accentBackground() {
        GradientDrawable shape = new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,
            new int[] { Color.rgb(72, 231, 211), Color.rgb(87, 177, 255) });
        shape.setCornerRadius(dp(14));
        return shape;
    }

    private static final class BrainCoreView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private long frame = 0;
        BrainCoreView(Activity activity) { super(activity); setLayerType(View.LAYER_TYPE_SOFTWARE, null); }
        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float cx = getWidth() / 2f, cy = getHeight() / 2f;
            float pulse = (float) (Math.sin(frame * 0.10) * 2.5);
            float radius = 43 + pulse;

            // Deep holographic halo.
            paint.setStyle(Paint.Style.FILL);
            paint.setShader(new RadialGradient(cx, cy, 88 + pulse,
                new int[] { Color.argb(95, 36, 235, 220), Color.argb(38, 44, 120, 255), Color.TRANSPARENT },
                null, Shader.TileMode.CLAMP));
            canvas.drawCircle(cx, cy, 88 + pulse, paint);
            paint.setShader(null);

            // Perspective orbit rings create a layered 3D hologram effect.
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(1.5f);
            paint.setColor(Color.argb(175, 66, 220, 230));
            canvas.save();
            canvas.rotate(-18 + (float)Math.sin(frame * 0.012) * 3, cx, cy);
            canvas.drawOval(cx - 76, cy - 24, cx + 76, cy + 24, paint);
            canvas.restore();
            paint.setColor(Color.argb(130, 92, 154, 255));
            canvas.save();
            canvas.rotate(28 - (float)Math.sin(frame * 0.009) * 3, cx, cy);
            canvas.drawOval(cx - 66, cy - 19, cx + 66, cy + 19, paint);
            canvas.restore();

            // Spherical core with off-centre highlight and shaded depth.
            paint.setStyle(Paint.Style.FILL);
            paint.setShader(new RadialGradient(cx - 15, cy - 17, 76,
                new int[] { Color.rgb(156, 255, 247), Color.rgb(28, 133, 177), Color.rgb(13, 31, 78) },
                new float[] { 0f, 0.48f, 1f }, Shader.TileMode.CLAMP));
            canvas.drawCircle(cx, cy, radius, paint);
            paint.setShader(null);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(1.2f);
            paint.setColor(Color.argb(210, 135, 250, 246));
            canvas.drawOval(cx - radius * 0.92f, cy - radius * 0.32f,
                cx + radius * 0.92f, cy + radius * 0.32f, paint);
            canvas.save();
            canvas.rotate(54, cx, cy);
            canvas.drawOval(cx - radius * 0.42f, cy - radius,
                cx + radius * 0.42f, cy + radius, paint);
            canvas.restore();

            // Neural points orbit the core; links remain visual, not claimed runtime edges.
            for (int i = 0; i < 14; i++) {
                double angle = (Math.PI * 2 * i / 14.0) + frame * 0.012;
                float orbit = 61 + (i % 3) * 7;
                float x = cx + (float)Math.cos(angle) * orbit;
                float y = cy + (float)Math.sin(angle) * orbit * 0.42f;
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(0.8f);
                paint.setColor(Color.argb(70, 104, 231, 244));
                canvas.drawLine(cx, cy, x, y, paint);
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(i % 3 == 0 ? Color.rgb(255, 205, 105)
                    : (i % 2 == 0 ? Color.rgb(100, 255, 225) : Color.rgb(128, 177, 255)));
                canvas.drawCircle(x, y, i % 3 == 0 ? 3.3f : 2.2f, paint);
            }
            paint.setStyle(Paint.Style.FILL);
            paint.setColor(Color.WHITE);
            paint.setTextAlign(Paint.Align.CENTER);
            paint.setTextSize(23);
            canvas.drawText("S", cx, cy + 8, paint);
            frame++;
            if (isAttachedToWindow()) postInvalidateDelayed(70);
        }
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
                String processedTranscript = response.optString("processed_text", transcript);
                String correctionNotice = processedTranscript.equals(transcript)
                    ? "" : "\nSAHIBEX heard/corrected: " + processedTranscript;
                String suggestionNotice = "";
                org.json.JSONArray inputSuggestions = response.optJSONArray("input_suggestions");
                if (inputSuggestions != null && inputSuggestions.length() > 0) {
                    org.json.JSONObject suggestion = inputSuggestions.optJSONObject(0);
                    if (suggestion != null) {
                        suggestionNotice = "\nPossible spelling (not applied): "
                            + suggestion.optString("original", "") + " → "
                            + suggestion.optString("suggested", "");
                    }
                }
                String display = "You said: " + transcript + correctionNotice + suggestionNotice
                    + "\n\nSAHIBEX: " + answer
                    + "\n\nHTTP: " + code + " | Verification: "
                    + response.optString("verification_status", "unknown");
                runOnUiThread(() -> {
                    mediaStatus.setText(display);
                    if (code == 200 && response.optBoolean("success", false)
                            && !answer.trim().isEmpty()) {
                        String answerLanguage = response.optString("answer_language", "und");
                        boolean hindiAnswer = answer.codePoints().anyMatch(cp ->
                            cp >= 0x0900 && cp <= 0x097F)
                            || answerLanguage.equals("hi")
                            || answerLanguage.equals("hi-Latn");
                        String ttsLanguage = hindiAnswer ? "hi" : "en";
                        // Always prefer the same local neural voice. Do not silently
                        // switch to Android's unrelated compatibility voice.
                        requestNeuralSpeech(answer, ttsLanguage, display);
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

    private void requestNeuralSpeech(final String answer, final String language, final String display) {
        final String token = getSharedPreferences("sahibex", MODE_PRIVATE)
            .getString("media_token", "");
        new Thread(() -> {
            HttpURLConnection connection = null;
            File audioFile = null;
            try {
                JSONObject request = new JSONObject().put("text", answer).put("language", language);
                byte[] body = request.toString().getBytes(StandardCharsets.UTF_8);
                connection = (HttpURLConnection) new URL(
                    "http://127.0.0.1:38742/synthesize").openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(3000);
                connection.setReadTimeout(60000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Authorization", "Bearer " + token);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                connection.setFixedLengthStreamingMode(body.length);
                try (OutputStream out = connection.getOutputStream()) { out.write(body); }
                int code = connection.getResponseCode();
                if (code == 200 && "audio/wav".equalsIgnoreCase(connection.getContentType())) {
                    byte[] audio;
                    try (InputStream in = connection.getInputStream();
                         ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
                        byte[] chunk = new byte[8192];
                        int count;
                        while ((count = in.read(chunk)) != -1) {
                            if (bytes.size() + count > 12 * 1024 * 1024) {
                                throw new IllegalStateException("Neural audio exceeded safe size limit");
                            }
                            bytes.write(chunk, 0, count);
                        }
                        audio = bytes.toByteArray();
                    }
                    if (audio.length < 44 || audio.length > 12 * 1024 * 1024) {
                        throw new IllegalStateException("Invalid neural audio size");
                    }
                    audioFile = File.createTempFile("sahibex-tts-", ".wav", getCacheDir());
                    try (FileOutputStream out = new FileOutputStream(audioFile)) { out.write(audio); }
                    final File readyFile = audioFile;
                    final String neuralEngine = connection.getHeaderField("X-SAHIBEX-TTS-Engine");
                    audioFile = null; // UI playback owns this temporary file until completion.
                    runOnUiThread(() -> {
                        try {
                            MediaPlayer old = activeNeuralPlayer;
                            if (old != null) { old.stop(); old.release(); }
                            MediaPlayer player = new MediaPlayer();
                            activeNeuralPlayer = player;
                            player.setDataSource(readyFile.getAbsolutePath());
                            player.setOnCompletionListener(done -> {
                                done.release();
                                if (activeNeuralPlayer == done) activeNeuralPlayer = null;
                                readyFile.delete();
                            });
                            player.setOnErrorListener((failed, what, extra) -> {
                                failed.release();
                                if (activeNeuralPlayer == failed) activeNeuralPlayer = null;
                                readyFile.delete();
                                showNeuralVoiceFailure(display, "Neural audio playback failed; Android fallback was not played.");
                                return true;
                            });
                            player.setOnPreparedListener(MediaPlayer::start);
                            player.prepareAsync();
                            mediaStatus.setText(display + "\nVoice engine: local neural " +
                                ((neuralEngine == null || neuralEngine.trim().isEmpty()) ? "TTS" : neuralEngine));
                        } catch (Exception playbackError) {
                            readyFile.delete();
                            showNeuralVoiceFailure(display, "Neural audio playback failed; Android fallback was not played.");
                        }
                    });
                    return;
                }
                String error = "neural_tts_unavailable";
                try (InputStream err = connection.getErrorStream()) {
                    if (err != null) {
                        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                        byte[] chunk = new byte[1024]; int count;
                        while ((count = err.read(chunk)) != -1 && bytes.size() < 8192) bytes.write(chunk, 0, count);
                        JSONObject errorJson = new JSONObject(bytes.toString(StandardCharsets.UTF_8.name()));
                        error = errorJson.optString("error", error);
                    }
                } catch (Exception ignored) { }
                final String reason = error;
                runOnUiThread(() -> showNeuralVoiceFailure(display,
                    "Local neural voice unavailable (" + reason + "). Android fallback was not played."));
            } catch (Exception error) {
                runOnUiThread(() -> showNeuralVoiceFailure(display,
                    "Local neural voice connection failed. Android fallback was not played."));
            } finally {
                if (audioFile != null && audioFile.exists()) audioFile.delete();
                if (connection != null) connection.disconnect();
            }
        }, "sahibex-neural-tts").start();
    }

    private void showNeuralVoiceFailure(String display, String notice) {
        // The user asked for one consistent SAHIBEX voice. Automatically speaking
        // Android TTS here changed voice identity/accent and sounded like a translator.
        // Fail visibly instead of playing a different voice without consent.
        mediaStatus.setText(display + "\n" + notice + " Retry after checking the local voice bridge.");
    }

    @Override protected void onDestroy() {
        recordingActive = false;
        MediaPlayer player = activeNeuralPlayer;
        if (player != null) {
            try { player.stop(); } catch (IllegalStateException ignored) { }
            player.release();
            activeNeuralPlayer = null;
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
