import sc2
from abstracts.Manager import Manager


# Define estratégias de scouting
class ScoutingManager(Manager):

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        pass
