import sc2
from sc2 import UnitTypeId

from abstracts.Manager import Manager


# Define criação e funcionamento de estruturas
class StructureManager(Manager):

    MAXIMUM_NUMBER_TOWNHALLS = 3
    MAXIMUM_NUMBER_ASSIMILATORS = 3
    MAXIMUM_NUMBER_PYLONS = 10
    SUPPLY_THRESHOLD_FOR_PYLON = 5

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        await self.build_pylons()
        await self.build_gas_buildings()
        await self.build_townhalls()

    async def build_townhalls(self):
        """
        Create another Nexus whenever possible, up until a limit.
        """
        if (
            self.agent.structures(UnitTypeId.NEXUS).amount < self.MAXIMUM_NUMBER_TOWNHALLS
            and self.agent.can_afford(UnitTypeId.NEXUS)
        ):
            await self.agent.expand_now()

    async def build_gas_buildings(self):
        """
        Create an Assimilator whenever possible on a random Nexus, up until a limit.
        """
        random_nexus = self.agent.townhalls.random
        close_vespene_geysers = self.agent.vespene_geyser.closer_than(15, random_nexus)

        for vespene_geyser in close_vespene_geysers:
            if self.agent.structures(UnitTypeId.ASSIMILATOR).amount >= self.MAXIMUM_NUMBER_ASSIMILATORS:
                break

            if not self.agent.can_afford(UnitTypeId.ASSIMILATOR):
                break

            if not self.agent.gas_buildings.closer_than(1, vespene_geyser):
                await self.agent.build(UnitTypeId.ASSIMILATOR, max_distance=1, near=vespene_geyser)

    async def build_pylons(self):
        """
        Create a Pylon whenever the supply is low on a random Nexus, up until a limit.
        """
        if self.agent.supply_left > self.SUPPLY_THRESHOLD_FOR_PYLON:
            return

        if self.agent.structures(UnitTypeId.PYLON).amount + self.agent.already_pending(UnitTypeId.PYLON) \
                >= self.MAXIMUM_NUMBER_PYLONS:
            return

        if not self.agent.can_afford(UnitTypeId.PYLON):
            return

        random_nexus = self.agent.townhalls.random
        await self.agent.build(UnitTypeId.PYLON, near=random_nexus)
