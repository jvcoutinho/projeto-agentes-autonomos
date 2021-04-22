import sc2
from sc2 import UnitTypeId

from abstracts.Manager import Manager


# Define criação e funcionamento de estruturas
class StructureManager(Manager):
    MAXIMUM_NUMBER_TOWNHALLS = 6
    MAXIMUM_NUMBER_ASSIMILATORS = 3
    MAXIMUM_NUMBER_PYLONS = 10
    MAXIMUM_NUMBER_FORGES = 2
    MAXIMUM_NUMBER_GATEWAYS = 2
    MAXIMUM_NUMBER_CYBERNETICSCORE = 1
    MAXIMUM_NUMBER_STARGATES = 1
    MAXIMUM_NUMBER_PHOTON_CANNONS = 5
    MAXIMUM_NUMBER_TWILIGHT_COUNCILS = 1
    MAXIMUM_NUMBER_DARK_SHRINES = 1
    SUPPLY_THRESHOLD_FOR_PYLON = 5

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        await self.build_pylons()
        await self.build_gas_buildings()
        await self.build_townhalls()
        await self.build_forge()
        await self.build_cybernetics_core()
        await self.build_gateway()
        await self.build_stargate()
        # await self.build_photon_cannon()
        # await self.build_twilight_council()
        # await self.build_dark_shrine()

    async def build_townhalls(self):
        """
        Create another Nexus whenever possible, up until a limit.
        """
        if (
            self.count_with_pending_structure(UnitTypeId.NEXUS) < self.MAXIMUM_NUMBER_TOWNHALLS
            and self.agent.can_afford(UnitTypeId.NEXUS)
        ):
            await self.agent.expand_now()

    async def build_gas_buildings(self):
        """
        Create an Assimilator whenever possible on a random Nexus, up until a limit.
        """
        townhalls = self.agent.townhalls.ready
        if not townhalls.exists:
            return

        random_nexus = self.agent.townhalls.ready.random
        close_vespene_geysers = self.agent.vespene_geyser.closer_than(15, random_nexus)

        for vespene_geyser in close_vespene_geysers:
            if (
                self.agent.structures(UnitTypeId.ASSIMILATOR).amount < self.MAXIMUM_NUMBER_ASSIMILATORS
                and self.agent.can_afford(UnitTypeId.ASSIMILATOR)
                and not self.agent.gas_buildings.closer_than(1, vespene_geyser).exists
            ):
                await self.agent.build(UnitTypeId.ASSIMILATOR, max_distance=1, near=vespene_geyser)

    async def build_pylons(self):
        """
        Create a Pylon whenever the supply is low on a random Nexus, up until a limit.
        """
        townhalls = self.agent.townhalls
        if not townhalls.exists:
            return

        if (
            self.agent.supply_left <= self.SUPPLY_THRESHOLD_FOR_PYLON
            and self.count_with_pending_structure(UnitTypeId.PYLON) < self.MAXIMUM_NUMBER_PYLONS
            and self.agent.can_afford(UnitTypeId.PYLON)
        ):
            random_nexus = townhalls.random
            await self.agent.build(UnitTypeId.PYLON, near=random_nexus, placement_step=7)

    async def build_pylons_near_inactive_structures(self):
        """
        Create a Pylon whenever a structure goes inactive (a Pylon near got destroyed, for example).
        """
        pass

    async def build_forge(self):
        """
        Create a Forge whenever possible near a random Pylon, up until a limit.
        """
        await self.build_structure_near_random_pylon(UnitTypeId.FORGE, self.MAXIMUM_NUMBER_FORGES)

    async def build_gateway(self):
        """
        Create a Gateway whenever possible near a random Pylon, up until a limit.
        """
        await self.build_structure_near_random_pylon(UnitTypeId.GATEWAY, self.MAXIMUM_NUMBER_GATEWAYS)

    async def build_cybernetics_core(self):
        """
        Create a single Cybernetics Core near a random Pylon if there is a ready Gateway.
        """
        if (
            self.agent.structures(UnitTypeId.GATEWAY).ready.exists
            and not self.agent.structures(UnitTypeId.CYBERNETICSCORE).exists
        ):
            await self.build_structure_near_random_pylon(UnitTypeId.CYBERNETICSCORE,
                                                         self.MAXIMUM_NUMBER_CYBERNETICSCORE)

    async def build_stargate(self):
        """
        Create a Stargate whenever possible near a random Pylon, up until a limit.
        """
        await self.build_structure_near_random_pylon(UnitTypeId.STARGATE, self.MAXIMUM_NUMBER_STARGATES)

    async def build_twilight_council(self):
        """
        Create a Twilight Council whenever possible near a random Pylon, up until a limit.
        """
        await self.build_structure_near_random_pylon(UnitTypeId.TWILIGHTCOUNCIL, self.MAXIMUM_NUMBER_TWILIGHT_COUNCILS)

    async def build_dark_shrine(self):
        """
        Create a Dark Shrine whenever possible near a random Pylon, up until a limit.
        """
        await self.build_structure_near_random_pylon(UnitTypeId.DARKSHRINE, self.MAXIMUM_NUMBER_DARK_SHRINES)

    async def build_photon_cannon(self):
        """
        Create a Photon Cannon whenever possible near a random Pylon, up until a limit.
        """
        await self.build_structure_near_random_pylon(UnitTypeId.PHOTONCANNON, self.MAXIMUM_NUMBER_PHOTON_CANNONS)

    async def build_structure_near_random_pylon(self, unit_type_id, limit: int, placement_step: int = 2):
        pylons = self.agent.structures(UnitTypeId.PYLON).ready
        if (
            pylons.exists
            and self.count_with_pending_structure(unit_type_id) < limit
            and self.agent.can_afford(unit_type_id)
        ):
            await self.agent.build(unit_type_id, near=pylons.random, placement_step=placement_step)

    def count_with_pending_structure(self, unit_type_id) -> int:
        return self.agent.structures(unit_type_id).amount + self.agent.already_pending(unit_type_id)


