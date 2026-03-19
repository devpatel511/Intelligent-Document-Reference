"""Chat memory system for session-scoped conversation history.

Stores user queries and assistant responses with timestamps.
Provides context building with full recent turns + summarized older turns.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChatTurn:
    """Single turn in a conversation (user query + assistant response)."""

    user_query: str
    assistant_response: str
    timestamp: datetime
    metadata: Optional[dict] = None


class ChatHistory:
    """In-memory chat history for a session with context building and summarization."""

    def __init__(self, window_size: int = 5, max_summary_length: int = 100):
        """Initialize chat history.

        Args:
            window_size: Number of recent full turns to keep before summarization.
            max_summary_length: Maximum character length of summarized turn.
        """
        self.window_size = window_size
        self.max_summary_length = max_summary_length
        self._turns: List[ChatTurn] = []

    def add_turn(
        self, user_query: str, assistant_response: str, metadata: Optional[dict] = None
    ) -> None:
        """Add a new turn to chat history.

        Args:
            user_query: User's question.
            assistant_response: Assistant's response.
            metadata: Optional metadata dict (e.g., model, backend used).
        """
        turn = ChatTurn(
            user_query=user_query,
            assistant_response=assistant_response,
            timestamp=datetime.now(),
            metadata=metadata,
        )
        self._turns.append(turn)
        logger.debug(f"Added chat turn #{len(self._turns)}: {user_query[:50]}...")

    def get_context(self) -> str:
        """Build conversation context for LLM.

        Returns:
            Formatted string with recent full turns + summarized older turns.
            Returns empty string if no history.
        """
        if not self._turns:
            return ""

        context_parts = []

        # If fewer turns than window, include all
        if len(self._turns) <= self.window_size:
            for turn in self._turns:
                context_parts.append(self._format_turn(turn, is_summary=False))
        else:
            # Include summarized older turns
            older_turns = self._turns[: len(self._turns) - self.window_size]
            if older_turns:
                summary = self._summarize_turns(older_turns)
                context_parts.append(summary)

            # Include recent full turns
            recent_turns = self._turns[-self.window_size :]
            for turn in recent_turns:
                context_parts.append(self._format_turn(turn, is_summary=False))

        context_str = "\n".join(context_parts)
        return context_str

    def get_full_history(self) -> List[ChatTurn]:
        """Return entire conversation history (for debugging/export).

        Returns:
            List of all ChatTurn objects.
        """
        return list(self._turns)

    def clear(self) -> None:
        """Clear all chat history (e.g., on new session)."""
        self._turns.clear()
        logger.info("Chat history cleared")

    def _format_turn(self, turn: ChatTurn, is_summary: bool = False) -> str:
        """Format a single turn for display.

        Args:
            turn: ChatTurn to format.
            is_summary: If True, extract key phrases; otherwise full text.

        Returns:
            Formatted turn string with timestamp.
        """
        time_str = turn.timestamp.strftime("%H:%M:%S")

        if is_summary:
            # Extract first N chars of query/response
            query_snippet = turn.user_query[:40]
            response_snippet = turn.assistant_response[:40]
            return f"[{time_str}] User: {query_snippet}... → Assistant: {response_snippet}..."
        else:
            return f"[{time_str}] User: {turn.user_query}\n[{time_str}] Assistant: {turn.assistant_response}"

    def _summarize_turns(self, turns: List[ChatTurn]) -> str:
        """Summarize older turns into condensed form.

        Args:
            turns: List of turns to summarize.

        Returns:
            Single-line summary string.
        """
        summaries = []
        for turn in turns:
            # Extract key phrases from query (first 30 chars) and response (first 30 chars)
            query_key = turn.user_query[:30].strip()
            if len(turn.user_query) > 30:
                query_key += "…"

            response_key = turn.assistant_response[:30].strip()
            if len(turn.assistant_response) > 30:
                response_key += "…"

            time_str = turn.timestamp.strftime("%H:%M")
            summary = (
                f"[{time_str}] User asked: {query_key}; Assistant said: {response_key}"
            )
            summaries.append(summary)

        return "--- Earlier conversation --- \n" + " | ".join(summaries)

    def get_turn_count(self) -> int:
        """Return number of turns in history."""
        return len(self._turns)
