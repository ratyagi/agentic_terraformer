# A2A message passing + routing
class MessageBus:
    def __init__(self):
        self.agents = {}
        self.queue = []

    def register_agent(self, name: str, agent):
        self.agents[name] = agent

    def send(self, msg: AgentMessage):
        self.queue.append(msg)

    def run(self, session_id: str):
        while self.queue:
            msg = self.queue.pop(0)
            if msg.receiver in self.agents:
                self.agents[msg.receiver].handle_message(msg, self)
