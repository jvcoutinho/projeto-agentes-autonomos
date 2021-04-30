import sc2
from sc2.unit import Unit


class Manager:

    def __init__(self, agent: sc2.BotAI):
        self.agent = agent


    async def start(self):
        pass


    async def update(self, iteration: int):
        pass


    async def on_structure_built(self, unit: Unit):
        pass


    async def on_structure_destroyed(self, unit_tag: int):
        pass
