import unittest

from core.brain.internal_brain_team import InternalBrainTeam
from core.diagnostics.flow_tracker import recent_dispatches


class DiagnosticFlowTrackerTests(unittest.TestCase):
    def test_real_handler_dispatch_is_recorded_without_request_payload(self):
        team = InternalBrainTeam()
        team.register_handler("math", lambda request, context: {"answer": 4})
        before = len(recent_dispatches(100))
        result = team.dispatch("math", "2 + 2", {"private": "do-not-record"},
                               authorization_passed=True, verification_passed=True)
        self.assertTrue(result.accepted)
        events = recent_dispatches(100)
        self.assertEqual(len(events), before + 1)
        event = events[-1]
        self.assertEqual(event["role_id"], "math")
        self.assertEqual(event["status"], "HANDLER_RETURNED_UNVERIFIED")
        self.assertNotIn("2 + 2", repr(event))
        self.assertNotIn("do-not-record", repr(event))
        self.assertIn("duration_ms", event)

    def test_authorization_denial_is_not_logged_as_handler_execution(self):
        team = InternalBrainTeam()
        team.register_handler("math", lambda request, context: {"answer": 4})
        before = len(recent_dispatches(100))
        result = team.dispatch("math", "2 + 2", authorization_passed=False,
                               verification_passed=True)
        self.assertFalse(result.accepted)
        self.assertEqual(len(recent_dispatches(100)), before)

    def test_handler_exception_is_recorded_without_exception_message(self):
        team = InternalBrainTeam()
        def fail(request, context):
            raise RuntimeError("private request data")
        team.register_handler("math", fail)
        before = len(recent_dispatches(100))
        result = team.dispatch("math", "safe test", authorization_passed=True,
                               verification_passed=True)
        self.assertFalse(result.accepted)
        event = recent_dispatches(100)[-1]
        self.assertEqual(len(recent_dispatches(100)), before + 1)
        self.assertEqual(event["status"], "HANDLER_ERROR:RuntimeError")
        self.assertNotIn("private request data", repr(event))


if __name__ == "__main__":
    unittest.main()
