import sc2
from sc2 import UnitTypeId

from abstracts.Manager import Manager


# Define estratégias de combate
class MilitaryManager(Manager):

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        # Training #
        self.train_units_on_structure([UnitTypeId.STALKER, UnitTypeId.ZEALOT], UnitTypeId.GATEWAY)
        self.train_units_on_structure([UnitTypeId.VOIDRAY], UnitTypeId.STARGATE)
        self.train_units_on_structure([UnitTypeId.DARKTEMPLAR], UnitTypeId.DARKSHRINE)

        # Combat #
        pass

    def train_units_on_structure(self, unit_type_ids, structure_type_id):
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
