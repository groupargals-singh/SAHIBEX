from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ConversationTurn:
    user: str
    assistant: str
    intent: str
    timestamp: str


@dataclass
class ContextManager:
    max_turns: int = 20
    history: list[ConversationTurn] = field(default_factory=list)

    def add_turn(
        self,
        user: str,
        assistant: str,
        intent: str,
    ) -> None:
        turn = ConversationTurn(
            user=user,
            assistant=assistant,
            intent=intent,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self.history.append(turn)

        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def update_latest_assistant(self, assistant: str) -> bool:
        """Replace the latest turn's assistant text without creating a duplicate turn."""
        if not isinstance(assistant, str):
            raise TypeError("assistant must be a string")
        if not self.history:
            return False
        self.history[-1].assistant = assistant
        return True

    def recent(self, count: int = 5) -> list[ConversationTurn]:
        return self.history[-count:]

    def clear(self) -> None:
        self.history.clear()

    def summary(self) -> dict:
        return {
            "turn_count": len(self.history),
            "recent_intents": [
                turn.intent for turn in self.recent(5)
            ],
        }
