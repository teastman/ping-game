import rx
import asyncio
import time
from math import copysign
from typing import Optional
from rx import operators as ops

LEFT = 0
RIGHT = 1
ACTIVE = 2

class Game:

    def __init__(self):

        self.players = (Player(), Player())
        self.tracks = [Track(2, 2, 0.2)] 

        for track in self.tracks:
            track.get_observable().pipe(
                ops.filter(lambda e: e.get('goal') is not None)
            ).subscribe(lambda event: self.goal(event))

    def goal(self, event):
        scoring_side = 1 - event['goal']
        self.players[scoring_side].goal()

    def update(self, time: float):
        for track in self.tracks:
            track.update(time)


class Player:

    def __init__(self):
        self.score = 0

    def goal(self):
        self.score += 1


class Puck:

    MAX_VELOCITY = 5.0
    INITIAL_VELOCITY = 1.0

    def __init__(self, location: Optional[float] = None, velocity: float = 0.0):

        """
        Parameters:
            location (float): The starting location of the puck.
            velocity (float): The speed and direction of the puck in m/s
        """

        self.location = location
        self.velocity = velocity
        self.color = (0, 255, 0)

    def update(self, time_delta: float) -> None:
        
        """
        Updates the location of the puck.

        Parameters:
            time_delta (float): The amount of time that has passed since the last update in seconds.
        """

        if self.location is not None:
            self.location = self.get_linear_location(time_delta)

    def get_linear_location(self, time_delta):
        return self.location + min(Puck.MAX_VELOCITY, self.velocity) * time_delta


class Paddle: 

    SPEED_MULTIPLIER = 0.1

    def __init__(self, length: float = 0.2):
        
        """
        Parameters:
            length (float):  The amount of time in seconds the paddle should persist.
        """

        self.length = length
        self.activated = None
        self.subscriptions = []
        self.deactive_time = 0.1
        self.color = (255, 255, 255)

    async def press(self, time) -> None:

        """
        Toggles the paddle into an activated state if it isn't already.  
        The paddle cannot be activated again for DEACTIVE_TIME after deactivating.
        """

        if self.is_locked(time):
            return

        self.activated = time
        for observer in self.subscriptions:
            observer.on_next({'paddle_on': time})
        await asyncio.sleep(self.length)
        for observer in self.subscriptions:
            observer.on_next({'paddle_off': time})
        await asyncio.sleep(self.deactive_time)

    def get_observable(self) -> rx.Observable:
        def register_observer(observer, scheduler = None):
            self.subscriptions.insert(0, observer)
        return rx.create(register_observer)

    def get_rebound_speed(self, time) -> float:
        self.rebounded = True
        return self.length / (time - self.activated + 0.00000001) * Paddle.SPEED_MULTIPLIER

    def is_active(self, time) -> bool:
        return self.get_next_off_time() > time

    def is_locked(self, time) -> bool:
        return self.get_next_available_time() > time

    def get_next_off_time(self) -> float:
        if self.activated is None:
            return 0.0
        return self.activated + self.length

    def get_next_available_time(self) -> float:
        return self.get_next_off_time() + self.deactive_time
        
    
class Track:

    POST_GOAL_FIRE_WAIT = 0.5

    def __init__(self, width: float, puck_count: int = 1, paddle_time: float = 0.2):  
        
        """
        Parameters:
            width (float):  The width of the track in meters.
            puck_count (int):  The number of pucks available to play on the track.
            paddle_time (float): The number of seconds the paddle is present upon activation. 
        """
        self.width = width

        self.pucks = ([],[],[])

        for i in range(puck_count):
            self.pucks[i % 2].insert(0, Puck())

        self.paddles = (Paddle(paddle_time), Paddle(paddle_time))

        self.last_goals = {LEFT:None, RIGHT:None}

        def subscribe_to_paddle(side):
            self.paddles[side].get_observable().pipe(
                ops.filter(lambda e: 'paddle_on' in e)
            ).subscribe(lambda event: self.attempt_fire_puck(side, event['paddle_on']))

        subscribe_to_paddle(LEFT)
        subscribe_to_paddle(RIGHT)

        self.subscriptions = []

        self.last_update = None

    def attempt_fire_puck(self, side, time):
        if len(self.pucks[side]) == 0:
            return

        should_fire = True

        # Check if a puck just scored.
        if self.last_goals[side] is not None and time - self.last_goals[side] < Track.POST_GOAL_FIRE_WAIT:
            should_fire = False

        # Check if the puck will rebound.
        rebound_delta = self.paddles[side].get_next_available_time() - time
        for puck in self.pucks[ACTIVE]:
            location = puck.get_linear_location(rebound_delta)
            if rebound_delta > 0 and (location < 0, location > self.width)[side]:
                should_fire = False
                break

        if should_fire is False:
            return

        puck = self.pucks[side][0]
        puck.velocity = Puck.INITIAL_VELOCITY * (1, -1)[side]
        puck.location = (0, self.width)[side]
        self.pucks[side].remove(puck)
        self.pucks[ACTIVE].insert(0, puck)

    def update(self, time: float):

        """
        Updates the track state.

        Parameters:
            time (float):  The current clock time in seconds.
        """
        if self.last_update is None:
            self.last_update = time
            return

        time_delta = time - self.last_update
        self.last_update = time

        def goal(puck, side):
            puck.location = None
            puck.velocity = 0
            self.pucks[ACTIVE].remove(puck)
            self.pucks[side].insert(0,puck)
            self.last_goals[side] = time
            for observer in self.subscriptions:
                observer.on_next({'goal': side, 'time': time})

        def rebound(puck, side):
            puck.velocity = -1 * copysign(self.paddles[side].get_rebound_speed(time), puck.velocity)
            puck.location = (0, self.width)[side]
            for observer in self.subscriptions:
                observer.on_next({'rebound': side})

        for puck in self.pucks[ACTIVE]:
            puck.update(time_delta)
            if puck.location > self.width or puck.location < 0:
                side = int(puck.location > self.width)
                if self.paddles[side].is_active(time):
                    rebound(puck, side)
                else:
                    goal(puck, side)

    def get_observable(self) -> rx.Observable:
        def register_observer(observer, scheduler = None):
            self.subscriptions.insert(0, observer)
        return rx.create(register_observer)
         
