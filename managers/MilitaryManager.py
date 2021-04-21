import sc2
from abstracts.Manager import Manager


# Define estratégias de combate
class MilitaryManager(Manager):

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        await self.worker_kamikaze_attack()

    async def worker_kamikaze_attack(self):
        """
        If there is no more nexuses, then make a suicide attack.
        """
        if not self.agent.townhalls.ready:
            for worker in self.agent.workers:
                worker.attack(self.agent.enemy_start_locations[0])
