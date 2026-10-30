package com.sahibex.companion;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.json.JSONArray;
import org.json.JSONObject;

final class BridgeServer {
    private static final int MAX_BODY_BYTES = 512000;
    private static final int MAX_HEADER_BYTES = 16384;
    private static final int MAX_NONCES = 4096;
    private static final long NONCE_TTL_MS = 10 * 60 * 1000L;
    private final SahibexAccessibilityService service;
    private final int port;
    private volatile boolean running;
    private ServerSocket server;
    private ExecutorService clients;
    private final LinkedHashMap<String, Long> nonces = new LinkedHashMap<>();

    BridgeServer(SahibexAccessibilityService service, int port) {
        this.service = service;
        this.port = port;
    }

    synchronized void start() {
        if (running) return;
        running = true;
        clients = new ThreadPoolExecutor(4, 4, 0L, TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(32), runnable -> {
                Thread thread = new Thread(runnable, "sahibex-accessibility-client");
                thread.setDaemon(true);
                return thread;
            }, new ThreadPoolExecutor.AbortPolicy());
        Thread acceptor = new Thread(() -> {
            try (ServerSocket listener = new ServerSocket(port, 8, InetAddress.getByName("127.0.0.1"))) {
                server = listener;
                while (running) {
                    Socket socket = listener.accept();
                    try {
                        clients.execute(() -> handle(socket));
                    } catch (RejectedExecutionException rejected) {
                        try { reply(socket, 503, error("busy")); } catch (Exception ignored) { }
                        try { socket.close(); } catch (IOException ignored) { }
                    }
                }
            } catch (IOException ignored) {
                // Closing the listener is the normal stop path. Do not log tokens or request bodies.
            } finally {
                running = false;
            }
        }, "sahibex-accessibility-bridge");
        acceptor.setDaemon(true);
        acceptor.start();
    }

    synchronized void stop() {
        running = false;
        try { if (server != null) server.close(); } catch (IOException ignored) { }
        if (clients != null) clients.shutdownNow();
    }

    private void handle(Socket socket) {
        Socket s = socket;
        try {
            s.setSoTimeout(5000);
            InputStream in = s.getInputStream();
            ByteArrayOutputStream headerBytes = new ByteArrayOutputStream();
            int matched = 0;
            while (headerBytes.size() < MAX_HEADER_BYTES) {
                int b = in.read();
                if (b < 0) throw new IOException("incomplete headers");
                headerBytes.write(b);
                if ((matched == 0 && b == '\r') || (matched == 1 && b == '\n')
                    || (matched == 2 && b == '\r') || (matched == 3 && b == '\n')) {
                    matched++;
                    if (matched == 4) break;
                } else {
                    matched = b == '\r' ? 1 : 0;
                }
            }
            if (matched != 4) { reply(s, 431, error("headers too large")); return; }
            String headers = new String(headerBytes.toByteArray(), StandardCharsets.ISO_8859_1);
            String[] lines = headers.split("\r\n");
            if (lines.length == 0 || !"POST /v1/action HTTP/1.1".equals(lines[0])) {
                reply(s, 404, error("unsupported endpoint")); return;
            }
            int contentLength = -1;
            String authorization = "";
            boolean transferEncoding = false;
            for (int i = 1; i < lines.length; i++) {
                int colon = lines[i].indexOf(':');
                if (colon <= 0) continue;
                String name = lines[i].substring(0, colon).trim().toLowerCase();
                String value = lines[i].substring(colon + 1).trim();
                if ("content-length".equals(name)) contentLength = Integer.parseInt(value);
                if ("authorization".equals(name)) authorization = value;
                if ("transfer-encoding".equals(name)) transferEncoding = true;
            }
            if (transferEncoding || contentLength <= 0 || contentLength > MAX_BODY_BYTES) {
                reply(s, 400, error("invalid body length")); return;
            }
            byte[] bodyBytes = readExactly(in, contentLength);
            JSONObject body = new JSONObject(new String(bodyBytes, StandardCharsets.UTF_8));
            if (body.optInt("protocol_version", -1) != 1) {
                reply(s, 400, error("unsupported protocol")); return;
            }
            String token = service.getSharedToken();
            if (token == null || !constantTimeEquals("Bearer " + token, authorization)
                || !validSignature(token, body)) {
                reply(s, 401, error("authentication failed")); return;
            }
            String nonce = body.optString("nonce", "");
            if (!acceptNonce(nonce)) {
                reply(s, 409, error("replayed, missing, or excessive nonce")); return;
            }
            String action = body.optString("action", "");
            if (action.isEmpty()) { reply(s, 400, error("missing action")); return; }
            if (!service.recordAudit(action, "attempt", nonce)) {
                reply(s, 503, error("audit unavailable; action was not executed"));
                return;
            }
            JSONObject result = service.handle(action, body.optJSONObject("payload"));
            if (!service.recordAudit(action, "completed", nonce)) {
                reply(s, 500, error("action may have completed but audit finalization failed"));
                return;
            }
            reply(s, 200, new JSONObject().put("success", true).put("result", result));
        } catch (SecurityException denied) {
            try { reply(socket, 423, error("emergency stop engaged or action denied")); }
            catch (Exception ignored) { }
        } catch (IllegalArgumentException badRequest) {
            try { reply(socket, 400, error("invalid request")); } catch (Exception ignored) { }
        } catch (Exception failure) {
            try { reply(s, 500, error("request failed")); } catch (Exception ignored) { }
        } finally {
            try { s.close(); } catch (IOException ignored) { }
        }
    }

    private byte[] readExactly(InputStream in, int length) throws IOException {
        byte[] data = new byte[length];
        int offset = 0;
        while (offset < length) {
            int count = in.read(data, offset, length - offset);
            if (count < 0) throw new IOException("incomplete body");
            if (count == 0) continue;
            offset += count;
        }
        return data;
    }

    private synchronized boolean acceptNonce(String nonce) {
        if (nonce == null || nonce.trim().isEmpty() || nonce.length() > 256) return false;
        long now = System.currentTimeMillis();
        Iterator<Map.Entry<String, Long>> it = nonces.entrySet().iterator();
        while (it.hasNext()) {
            if (now - it.next().getValue() > NONCE_TTL_MS) it.remove();
        }
        if (nonces.containsKey(nonce) || nonces.size() >= MAX_NONCES) return false;
        nonces.put(nonce, now);
        return true;
    }

    private boolean validSignature(String token, JSONObject body) throws Exception {
        String canonical = canonicalRequest(body);
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(token.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] digest = mac.doFinal(canonical.getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder();
        for (byte value : digest) hex.append(String.format("%02x", value));
        return constantTimeEquals(hex.toString(), body.optString("signature", ""));
    }

    // Rebuild from authenticated semantic fields; never trust caller-supplied _canonical.
    private String canonicalRequest(JSONObject body) throws Exception {
        String action = body.optString("action", "");
        String nonce = body.optString("nonce", "");
        JSONObject payload = body.optJSONObject("payload");
        if (payload == null) payload = new JSONObject();
        return "{\"action\":" + JSONObject.quote(action)
            + ",\"nonce\":" + JSONObject.quote(nonce)
            + ",\"payload\":" + canonicalValue(payload)
            + ",\"protocol_version\":1}";
    }

    private String canonicalValue(Object value) throws Exception {
        if (value == null || value == JSONObject.NULL) return "null";
        if (value instanceof JSONObject) {
            JSONObject object = (JSONObject) value;
            ArrayList<String> keys = new ArrayList<>();
            for (Iterator<String> it = object.keys(); it.hasNext();) keys.add(it.next());
            Collections.sort(keys);
            StringBuilder out = new StringBuilder("{");
            for (int i = 0; i < keys.size(); i++) {
                if (i > 0) out.append(",");
                String key = keys.get(i);
                out.append(JSONObject.quote(key)).append(":").append(canonicalValue(object.opt(key)));
            }
            return out.append("}").toString();
        }
        if (value instanceof JSONArray) {
            JSONArray array = (JSONArray) value;
            StringBuilder out = new StringBuilder("[");
            for (int i = 0; i < array.length(); i++) {
                if (i > 0) out.append(",");
                out.append(canonicalValue(array.opt(i)));
            }
            return out.append("]").toString();
        }
        if (value instanceof String) return JSONObject.quote((String) value);
        if (value instanceof Boolean) return value.toString();
        if (value instanceof Number) return value.toString();
        throw new IllegalArgumentException("unsupported JSON value");
    }

    private boolean constantTimeEquals(String expected, String actual) {
        return MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8),
            actual.getBytes(StandardCharsets.UTF_8));
    }

    private JSONObject error(String message) {
        try { return new JSONObject().put("success", false).put("error", message); }
        catch (Exception impossible) { return new JSONObject(); }
    }

    private void reply(Socket socket, int code, JSONObject body) throws IOException {
        byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
        String reason = code == 200 ? "OK" : code == 401 ? "Unauthorized"
            : code == 404 ? "Not Found" : code == 409 ? "Conflict"
            : code == 423 ? "Locked" : code == 431 ? "Request Header Fields Too Large"
            : code == 503 ? "Service Unavailable" : code == 500 ? "Internal Server Error" : "Bad Request";
        OutputStream out = socket.getOutputStream();
        out.write(("HTTP/1.1 " + code + " " + reason + "\r\n"
            + "Content-Type: application/json; charset=utf-8\r\n"
            + "Cache-Control: no-store\r\n"
            + "X-Content-Type-Options: nosniff\r\n"
            + "Content-Length: " + bytes.length + "\r\n"
            + "Connection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
        out.write(bytes);
        out.flush();
    }
}
