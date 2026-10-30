from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID = ROOT / "android_companion/app/src/main"
SERVICE = (ANDROID / "java/com/sahibex/companion/SahibexAccessibilityService.java").read_text()
BRIDGE = (ANDROID / "java/com/sahibex/companion/BridgeServer.java").read_text()
ACTIVITY = (ANDROID / "java/com/sahibex/companion/MainActivity.java").read_text()
MANIFEST = (ANDROID / "AndroidManifest.xml").read_text()


def test_accessibility_bridge_binds_only_loopback():
    assert 'InetAddress.getByName("127.0.0.1")' in BRIDGE
    assert 'POST /v1/action HTTP/1.1' in BRIDGE


def test_signature_is_rebuilt_from_action_nonce_payload_and_version():
    assert "canonicalRequest(body)" in BRIDGE
    assert "never trust caller-supplied _canonical" in BRIDGE
    assert 'body.optString("_canonical"' not in BRIDGE


def test_nonce_replay_cache_does_not_clear_on_capacity():
    assert "MAX_NONCES = 4096" in BRIDGE
    assert "NONCE_TTL_MS" in BRIDGE
    assert "nonces.containsKey(nonce)" in BRIDGE
    assert "nonces.clear()" not in BRIDGE


def test_request_parser_limits_headers_body_and_socket_wait():
    assert "MAX_BODY_BYTES = 512000" in BRIDGE
    assert "MAX_HEADER_BYTES = 16384" in BRIDGE
    assert "setSoTimeout(5000)" in BRIDGE
    assert "readExactly(in, contentLength)" in BRIDGE
    assert "transferEncoding" in BRIDGE


def test_bridge_has_bounded_worker_pool_and_loopback_only_server():
    assert "new ThreadPoolExecutor(4, 4" in BRIDGE
    assert "new ArrayBlockingQueue<>(32)" in BRIDGE
    assert "RejectedExecutionException" in BRIDGE
    assert 'new ServerSocket(port, 8, InetAddress.getByName("127.0.0.1"))' in BRIDGE


def test_gesture_reports_completion_not_only_dispatch_acceptance():
    assert "onCompleted(GestureDescription g)" in SERVICE
    assert "onCancelled(GestureDescription g)" in SERVICE
    assert "gesture completion timeout" in SERVICE
    assert 'put("completed", true)' in SERVICE


def test_gesture_coordinates_and_duration_are_validated():
    assert "gesture coordinates outside current display" in SERVICE
    assert "durationMs > 5000" in SERVICE


def test_text_action_rejection_fails_closed_instead_of_reporting_completion():
    assert 'if (!accepted)' in SERVICE
    assert 'focused editable field rejected text action' in SERVICE
    assert 'return new JSONObject().put("accepted", true).put("completed", true);' in SERVICE


def test_emergency_stop_blocks_remote_actions_and_is_persistent():
    assert '"emergency_stop"' in SERVICE
    assert '"emergency_stop_status"' in SERVICE
    assert 'getBoolean(STOP_KEY, false)' in SERVICE
    assert "emergency stop engaged; resume locally in companion app" in SERVICE
    assert "runtimeStopped = true" in SERVICE
    assert "emergency stop persistence failed; runtime latch remains active" in SERVICE


def test_app_exposes_confirmed_local_stop_and_resume_controls():
    assert "EMERGENCY STOP — Disable UI Control" in ACTIVITY
    assert "STOP NOW" in ACTIVITY
    assert "RESUME" in ACTIVITY
    assert 'putBoolean("accessibility_stopped", true)' in ACTIVITY
    assert 'putBoolean("accessibility_stopped", true).commit()' in ACTIVITY
    assert "resumeEmergencyStopLocally(p)" in ACTIVITY
    assert "Resume failed to persist; UI control remains stopped." in ACTIVITY


def test_password_fields_are_redacted_and_never_autotyped():
    assert 'node.isPassword() ? "[REDACTED]"' in SERVICE
    assert 'throw new SecurityException("typing into password fields is blocked")' in SERVICE


def test_ui_tree_is_bounded_and_screenshot_payload_is_opt_in():
    assert "MAX_TREE_NODES = 500" in SERVICE
    assert "depth > 12" in SERVICE
    assert 'optBoolean("include_base64", false)' in SERVICE
    assert "AtomicBoolean abandoned" in SERVICE
    assert "synchronized (captureLock)" in SERVICE
    assert "bufferRef.getAndSet(null)" in SERVICE


def test_accessibility_service_is_not_exported_and_requires_system_binding():
    assert 'android:exported="false"' in MANIFEST
    assert 'android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"' in MANIFEST
def test_action_audit_is_committed_before_execution_and_payload_is_not_logged():
    audit_call = BRIDGE.index('service.recordAudit(action, "attempt", nonce)')
    action_call = BRIDGE.index("service.handle(action, body.optJSONObject")
    assert audit_call < action_call
    assert "accessibility_audit_events" in SERVICE
    assert '"nonce_fingerprint"' in SERVICE
    assert 'put("payload"' not in SERVICE
