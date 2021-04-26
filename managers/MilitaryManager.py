from typing import Union

import sc2
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from abstracts.Manager import Manager


# Define estratégias de combate
class MilitaryManager(Manager):

    DEFEND_THRESHOLD = 0.6
    COMBATENTS_PUSH_THRESHOLD = 16
    COMBATENTS_SHIELD_THRESHOLD = 0.3
    COMBATENTS_HEALTH_THRESHOLD = 0.6

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        pass

    async def update(self, iteration: int):
        # Training #
        self.train_units_on_structure([UnitTypeId.DARKTEMPLAR, UnitTypeId.STALKER,UnitTypeId.OBSERVER, UnitTypeId.SENTRY, UnitTypeId.ZEALOT], UnitTypeId.GATEWAY)
        self.train_units_on_structure([UnitTypeId.VOIDRAY], UnitTypeId.STARGATE)
        self.train_units_on_structure([UnitTypeId.OBSERVER], UnitTypeId.ROBOTICSFACILITY)

        # Combat #
        self.defend_base()
        self.attack_procedure()

    def train_units_on_structure(self, unit_type_ids, structure_type_id):
        """
        Train an array of units in a structure who trains them. Due to the
        resources, units at the start of the array should be more costly.
        """
        for unit_id in unit_type_ids:
            for structure in self.agent.structures(structure_type_id).ready.idle:
                if self.agent.can_afford(unit_id):
                    structure.train(unit_id)

    def defend_base(self):
        """
        If there are enemies too close to a Nexus, then defend if there are enough units nearby.
        """
        for townhall in self.agent.townhalls:
            close_enemies = self.get_enemies().closer_than(15, townhall)
            if not close_enemies.exists:
                continue

            close_combatents = self.get_combatents().closer_than(60, townhall)
            if close_combatents.amount >= close_enemies.amount * self.DEFEND_THRESHOLD:
                for combatent in close_combatents:
                    combatent.attack(close_enemies.closest_to(combatent))

    def attack_procedure(self):
        """
        If the army contains a certain number, then make a push to the enemy base.
        Retreat whenever too damaged; attack units first; attack structures last.
        """
        combatents = self.get_combatents().idle

        if combatents.amount < self.COMBATENTS_PUSH_THRESHOLD:
            return

        for combatent in combatents:
            if self.is_healthy(combatent):
                target = self.get_attack_target(combatent)
                self.use_abilities(combatent, target)
                combatent.attack(target)
            else:
                pylons = self.agent.structures(UnitTypeId.PYLON).ready
                if pylons.exists:
                    combatent.move(pylons.closest_to(combatent))

    def get_combatents(self) -> Units:
        return (
            self.agent.units(UnitTypeId.VOIDRAY) |
            self.agent.units(UnitTypeId.ZEALOT) |
            self.agent.units(UnitTypeId.DARKTEMPLAR) |
            self.agent.units(UnitTypeId.STALKER) |
            self.agent.units(UnitTypeId.SENTRY) |
            self.agent.units(UnitTypeId.OBSERVER)
        )

    def get_enemies(self) -> Units:
        return (self.agent.enemy_units | self.agent.enemy_structures).filter(lambda t: t.can_be_attacked)

    def get_attack_target(self, combatent: Unit) -> Union[Unit, Point2]:
        if self.agent.enemy_units.exists:
            return self.agent.enemy_units.closest_to(combatent)
        if self.agent.enemy_structures.exists:
            return self.agent.enemy_structures.random
        return self.agent.enemy_start_locations[0]

    def is_healthy(self, combatent: Unit) -> bool:
        return (
            combatent.shield_percentage >= self.COMBATENTS_SHIELD_THRESHOLD
            or combatent.health_percentage >= self.COMBATENTS_HEALTH_THRESHOLD
        )

    def use_abilities(self, combatent: Unit, target: Unit):
        if combatent.type_id == UnitTypeId.STALKER and combatent.in_ability_cast_range(AbilityId.EFFECT_BLINK_STALKER, target):
            combatent(AbilityId.EFFECT_BLINK_STALKER, target)

        if target.distance_to(combatent) < 10:
            if combatent.type_id == UnitTypeId.VOIDRAY:
                combatent(AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT)

            if combatent.type_id == UnitTypeId.SENTRY:
                combatent(AbilityId.GUARDIANSHIELD_GUARDIANSHIELD)



