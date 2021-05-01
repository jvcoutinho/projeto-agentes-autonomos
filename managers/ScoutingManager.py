import random

import sc2
from sc2 import UnitTypeId
from sc2.units import Units

from abstracts.Manager import Manager


# Define estratégias de scouting
class ScoutingManager(Manager):
    CURRENTY_ROUTE = True
    probobservers = []
    haveobservers = True
    route = []

    def __init__(self, agent: sc2.BotAI):
        super().__init__(agent)

    async def start(self):
        splited = self.agent.enemy_start_locations[0].sort_by_distance(self.agent.expansion_locations_list)
        splitedt = []
        for x in splited:
            if(x != (142.5,33.5) and x != (144.5,58.5) and x != (31.5,113.5) and x != (33.5,138.5)):
                splitedt.append(x)
        splitedt = [splitedt[i::2] for i in range(2)]
        self.route.append(splitedt[0][:6])
        self.route.append(splitedt[1][:6])
        
        if(len(self.route[0])>1):
            self.route[0].append(self.route[0][0])
        if(len(self.route[1])>1):
            self.route[0].append(self.route[0][0])

        self.route.append(self.route[0][::-1])
        self.route.append(self.route[1][::-1])


    async def update(self, iteration: int):
        await self.movementScouts()

    async def movementScouts(self):
        observer = self.get_observers().idle
        if(not self.haveobservers):
            probe = self.get_prob().idle
            if(len(probe)>0):
                if(len(self.probobservers) == 0):
                    self.probobservers.append(probe[0])
                    y = random.randint(0,len(self.route)-1)
                    for x in self.route[y]:
                        self.probobservers[0].patrol(x, queue = True)
                else:
                    if(self.probobservers[0].health == 0):
                        self.probobservers[0] = probe[0]
                        y = random.randint(0,len(self.route)-1)
                        for x in self.route[y]:
                            self.probobservers[0].patrol(x, queue = True)

        if(len(observer) > 0 ):
            # self.haveobservers = True
            observer = observer[0]
            y = random.randint(0,len(self.route)-1)
            for x in self.route[y]:
                observer.patrol(x, queue = True)
        else:
            pass
    def get_observers(self) -> Units:
        return (
            self.agent.units(UnitTypeId.OBSERVER)
        )
    def get_prob(self) -> Units:
        return (
            self.agent.units(UnitTypeId.PROBE)
        )
