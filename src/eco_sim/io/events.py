from __future__ import annotations

import json
from typing import List

from eco_sim.models import Event


class EventLog:
    def __init__(self) -> None:
        self.events: List[Event] = []

    def append(self, event: Event) -> None:
        self.events.append(event)

    def save(self, path: str) -> None:
        data = []
        for e in self.events:
            data.append({
                "tick": e.tick,
                "kind": e.kind,
                "agent_id": e.agent_id,
                "payload": e.payload,
            })
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r") as f:
            data = json.load(f)
        self.events = []
        for d in data:
            e = Event(
                tick=d["tick"],
                kind=d["kind"],
                agent_id=d["agent_id"],
                payload=d.get("payload", {}),
            )
            self.events.append(e)

