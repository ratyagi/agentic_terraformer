# A2A message passing + routing
"""
core.message_bus

MessageBus for registering agents and routing AgentMessage objects between them.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from core.models import AgentMessage

logger = logging.getLogger(__name__)


class MessageBus:
    """
    MessageBus

    Simple in-memory message bus:
    - register_agent(name, instance)
    - send(message)
    - run(session_id=None) to dispatch messages to agents.
    """

    def __init__(self) -> None:
        self.agents: Dict[str, object] = {}
        self.queue: List[AgentMessage] = []

    # --- Agent registration ---

    def register_agent(self, name: str, agent: object) -> None:
        """
        Register an agent with a unique name.
        The agent must implement `handle_message(self, msg, bus)`.
        """
        if name in self.agents:
            logger.warning("Overwriting existing agent registration: %s", name)
        self.agents[name] = agent
        logger.info("Registered agent: %s", name)

    # --- Message queue operations ---

    def send(self, msg: AgentMessage) -> None:
        """Enqueue a message to be dispatched later."""
        logger.debug(
            "Enqueued message %s from %s to %s (session %s)",
            msg.type,
            msg.sender,
            msg.receiver,
            msg.session_id,
        )
        self.queue.append(msg)

    # --- Dispatch loop ---

    def run(self, session_id: Optional[str] = None, max_steps: Optional[int] = None) -> None:
        """
        Dispatch messages in FIFO order.

        Args:
            session_id: if provided, only messages for this session are processed.
            max_steps: safety limit to avoid infinite loops; None = no limit.
        """
        steps = 0

        while self.queue:
            if max_steps is not None and steps >= max_steps:
                logger.warning("MessageBus reached max_steps=%d, stopping dispatch", max_steps)
                break

            msg = self.queue.pop(0)

            if session_id is not None and msg.session_id != session_id:
                # Put it back at the end of the queue for another run
                self.queue.append(msg)
                steps += 1
                continue

            receiver_name = msg.receiver
            agent = self.agents.get(receiver_name)
            if agent is None:
                logger.error(
                    "No registered agent named '%s' for message type %s (session %s)",
                    receiver_name,
                    msg.type,
                    msg.session_id,
                )
                steps += 1
                continue

            logger.debug(
                "Dispatching message %s from %s to %s (session %s)",
                msg.type,
                msg.sender,
                msg.receiver,
                msg.session_id,
            )

            try:
                # Agents are expected to implement handle_message(msg, bus)
                agent.handle_message(msg, self)  # type: ignore[attr-defined]
            except Exception as e:  # noqa: BLE001
                logger.exception(
                    "Error handling message %s by agent %s: %s",
                    msg.type,
                    receiver_name,
                    e,
                )

            steps += 1
