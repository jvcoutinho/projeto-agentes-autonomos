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
    COMBATENTS_PUSH_WITH_VOIDRAY_THRESHOLD = 15
    COMBATENTS_PUSH_WITHOUT_VOIDRAY_THRESHOLD = 30
    VOIDRAY_PUSH_THRESHOLD = 3
    COMBATENTS_SHIELD_THRESHOLD = 0.3
    COMBATENTS_HEALTH_THRESHOLD = 0.6
    COMBATENT_ABILITY_CAST_RANGE = 20

    MAXIMUM_NUMBER_SENTRIES = 1000
    MAXIMUM_NUMBER_OBSERVERS = 2

    DEFFENSE_CHAT_SENT = False
    ATTACK_CHAT_SENT = False
    TEMPEST_CHAT_SENT = False
    DARKSHRINE_CHAT_SENT = False
    VOIDRAY_CHAT_SENT = False

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)
        self.abilities = [
            (UnitTypeId.STALKER, AbilityId.EFFECT_BLINK_STALKER),
            (UnitTypeId.VOIDRAY, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT),
            (UnitTypeId.SENTRY, AbilityId.GUARDIANSHIELD_GUARDIANSHIELD)
        ]


    async def start(self):
        pass


    async def update(self, iteration: int):
        # Training #
        self.train_units_on_structure([UnitTypeId.TEMPEST, UnitTypeId.VOIDRAY], UnitTypeId.STARGATE)
        self.train_units_on_structure(
            [UnitTypeId.DARKTEMPLAR, UnitTypeId.STALKER, UnitTypeId.SENTRY, UnitTypeId.ZEALOT], UnitTypeId.GATEWAY)
        self.train_units_on_structure([UnitTypeId.OBSERVER], UnitTypeId.ROBOTICSFACILITY)

        # Combat #
        on_deffense = self.defend_base()

        if on_deffense and not self.DEFFENSE_CHAT_SENT:
            self.DEFFENSE_CHAT_SENT = True
            await self.agent.chat_send("YOU... SHALL NOT... PASS!")

        await self.attack_procedure()


    def train_units_on_structure(self, unit_type_ids, structure_type_id):
        """
        Train an array of units in a structure who trains them. Due to the
        resources, units at the start of the array should be more costly.
        """
        for unit_id in unit_type_ids:
            if (
                (unit_id == UnitTypeId.SENTRY and self.agent.units(
                    UnitTypeId.SENTRY).amount >= self.MAXIMUM_NUMBER_SENTRIES)
                or (unit_id == UnitTypeId.OBSERVER and self.agent.units(
                UnitTypeId.OBSERVER).amount >= self.MAXIMUM_NUMBER_OBSERVERS)
            ):
                continue

            for structure in self.agent.structures(structure_type_id).ready.idle:
                if self.agent.can_afford(unit_id):
                    structure.train(unit_id)


    def defend_base(self):
        """
        If there are enemies too close to a Nexus, then defend if there are enough units nearby.
        """
        defending = False

        for townhall in self.agent.townhalls:
            close_enemies = self.get_enemies().closer_than(15, townhall)
            if not close_enemies.exists:
                defending |= False
                continue

            close_combatents = self.get_combatents().closer_than(60, townhall)
            if close_combatents.amount >= close_enemies.amount * self.DEFEND_THRESHOLD:
                defending |= True
                for combatent in close_combatents:
                    combatent.attack(close_enemies.closest_to(combatent))

        return defending


    async def attack_procedure(self):
        """
        If the army contains a certain number, then make a push to the enemy base.
        Retreat whenever too damaged; attack units first; attack structures last.
        """
        combatents = self.get_combatents()

        if not self.is_sufficient_amount(combatents.amount):
            return

        if not self.ATTACK_CHAT_SENT:
            self.ATTACK_CHAT_SENT = True
            await self.agent.chat_send("LEEROOOOOOOOOOOY JENKINS")

        for combatent in combatents:
            if self.is_healthy(combatent):
                target = self.get_attack_target(combatent, combatents.amount)
                if target is not None:
                    combatent.attack(target)
                    if self.agent.enemy_units.closer_than(10, combatent):
                        await self.use_abilities(combatent, target)
            else:
                pylons = self.agent.structures(UnitTypeId.PYLON).ready
                if pylons.exists:
                    combatent.patrol(pylons.closest_to(combatent))


    def get_combatents(self) -> Units:
        return (
            self.agent.units(UnitTypeId.VOIDRAY) +
            self.agent.units(UnitTypeId.ZEALOT) +
            self.agent.units(UnitTypeId.DARKTEMPLAR) +
            self.agent.units(UnitTypeId.STALKER) +
            self.agent.units(UnitTypeId.SENTRY) +
            self.agent.units(UnitTypeId.TEMPEST)
        )


    def get_enemies(self) -> Units:
        return (self.agent.enemy_units + self.agent.enemy_structures).filter(lambda unit: unit.can_be_attacked)


    def get_attack_target(self, combatent: Unit, amount_combatents: int) -> Union[Unit, Point2, None]:
        enemy_units = self.agent.enemy_units.closer_than(50, combatent).filter(lambda unit: unit.can_be_attacked)
        enemy_structures = self.agent.enemy_structures.filter(lambda unit: unit.can_be_attacked)

        if enemy_units.exists:
            return enemy_units.closest_to(combatent)
        if enemy_structures.exists:
            return enemy_structures.closest_to(combatent)
        return self.agent.enemy_start_locations[0]


    def is_healthy(self, combatent: Unit) -> bool:
        return (
            combatent.shield_percentage >= self.COMBATENTS_SHIELD_THRESHOLD
            or combatent.health_percentage >= self.COMBATENTS_HEALTH_THRESHOLD
        )


    async def use_abilities(self, combatent: Unit, target: Unit):
        for (unit, ability) in self.abilities:
            if (
                unit == combatent.type_id
                and await self.agent.can_cast(combatent, ability)
                and not combatent.is_using_ability(ability)
            ):
                if combatent.type_id == UnitTypeId.STALKER:
                    combatent(ability, target)
                else:
                    combatent(ability)


    def is_sufficient_amount(self, amount: int):
        number_voidrays = self.agent.units(UnitTypeId.VOIDRAY).ready.amount

        if number_voidrays >= self.VOIDRAY_PUSH_THRESHOLD:
            return amount >= self.COMBATENTS_PUSH_WITH_VOIDRAY_THRESHOLD

        return amount >= self.COMBATENTS_PUSH_WITHOUT_VOIDRAY_THRESHOLD

    async def on_unit_created(self, unit: Unit):
        if unit.type_id == UnitTypeId.TEMPEST and not self.TEMPEST_CHAT_SENT:
            self.TEMPEST_CHAT_SENT = True
            await self.agent.chat_send("Release the KRAKEN!")
        
        if unit.type_id == UnitTypeId.DARKTEMPLAR and not self.DARKSHRINE_CHAT_SENT:
            self.DARKSHRINE_CHAT_SENT = True
            await self.agent.chat_send("Didn't see that comming?")

        if unit.type_id == UnitTypeId.VOIDRAY and not self.VOIDRAY_CHAT_SENT:
            self.VOIDRAY_CHAT_SENT = True
            await self.agent.chat_send("Bring the Cavalry!")

