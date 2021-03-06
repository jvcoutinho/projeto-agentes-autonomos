import sc2
from sc2 import UnitTypeId

from abstracts.Manager import Manager


# Define estratégias de coleta de recursos
class ResourcesManager(Manager):

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        await self.train_workers()
        await self.distribute_workers()

    async def train_workers(self):
        """
        Train probes on nexuses which are idle and missing workers
        """
        for townhall in self.agent.townhalls.idle:
            if (
                townhall.assigned_harvesters < townhall.ideal_harvesters
                and self.agent.can_afford(UnitTypeId.PROBE)
            ):
                townhall.train(UnitTypeId.PROBE)

    async def distribute_workers(self):
        """
        Distribute workers if some are idle
        """
        if self.agent.idle_worker_count > 0:
            await self.agent.distribute_workers()
