import sc2
from sc2 import UnitTypeId
from sc2.units import Units

from abstracts.Manager import Manager


# Define estratégias de combate
class MilitaryManager(Manager):

    DEFEND_THRESHOLD = 0.6

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        # Training #
        self.train_units_on_structure([UnitTypeId.DARKTEMPLAR, UnitTypeId.STALKER, UnitTypeId.ZEALOT], UnitTypeId.GATEWAY)
        self.train_units_on_structure([UnitTypeId.VOIDRAY], UnitTypeId.STARGATE)

        # Combat #
        await self.defend_base()

    def train_units_on_structure(self, unit_type_ids, structure_type_id):
        """
        Train an array of units in a structure who trains them. Due to the
        resources, units at the start of the array should be more costly.
        """
        for unit_id in unit_type_ids:
            for structure in self.agent.structures(structure_type_id).ready.idle:
                if self.agent.can_afford(unit_id):
                    structure.train(unit_id)

    async def worker_kamikaze_attack(self):
        """
        If there is no more nexuses, then make a suicide attack.
        """
        if not self.agent.townhalls.ready:
            for worker in self.agent.workers:
                worker.attack(self.agent.enemy_start_locations[0])

    async def defend_base(self):
        """
        If there are enemies too close to a Nexus, then defend if there are enough units. Otherwise, flee to another Nexus.
        """
        for townhall in self.agent.townhalls:
            close_enemies = self.enemies().closer_than(15, townhall)
            if not close_enemies.exists:
                continue

            close_combatents = self.combatents().closer_than(40, townhall)
            if close_combatents.amount >= close_enemies.amount * self.DEFEND_THRESHOLD:
                for combatent in close_combatents:
                    combatent.attack(close_enemies.closest_to(combatent))
            # elif self.agent.townhalls.amount > 1:
            #     neighbour_townhall = self.agent.townhalls.filter(lambda t: t != townhall).closest_to(townhall)
            #     for combatent in close_combatents:
            #         combatent.move(neighbour_townhall)

    def combatents(self) -> Units:
        return (
            self.agent.units(UnitTypeId.VOIDRAY) |
            self.agent.units(UnitTypeId.ZEALOT) |
            self.agent.units(UnitTypeId.DARKTEMPLAR) |
            self.agent.units(UnitTypeId.STALKER)
        )

    def enemies(self) -> Units:
        return (self.agent.enemy_units | self.agent.enemy_structures).filter(lambda t: t.can_be_attacked)

