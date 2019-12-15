import pygame
import game
import asyncio

RADIUS = 5
GAP = 10
OFF_COLOR = (0,0,0)
ON_COLOR = (0,255,0)
PADDLE_COLOR = (255,255,255)
AVAILABLE_COLOR = (0,0,255)
VERTICAL_TRACK_OFFSET = 20
HORIZONTAL_TRACK_OFFSET = 20

class GUI:

    def __init__(self, width: int, height: int):
        pygame.init()
        self.surface = pygame.display.set_mode((width, height))
        self.surface.fill((100,100,100))
        self.width = width
        self.height = height
        pygame.display.set_caption('Ping')

    def handle_input(self, loop, event_queue): 
        while True:
            event = pygame.event.wait()
            asyncio.run_coroutine_threadsafe(event_queue.put(event), loop=loop)

    def led_count(self):
        return int((self.width - HORIZONTAL_TRACK_OFFSET * 2 + GAP) / (RADIUS * 2 + GAP))

    def render(self, the_game, time):
        led_count = self.led_count()

        def draw_track(track, track_index):
            active_puck_locations = []
            stored_puck_locations = []

            for i in range(len(track.pucks[game.LEFT])):
                stored_puck_locations.insert(0, i)

            for i in range(len(track.pucks[game.RIGHT])):
                stored_puck_locations.insert(0, led_count - (i + 1))

            for puck in track.pucks[game.ACTIVE]:
                index = int(puck.location / track.width * led_count)
                active_puck_locations.insert(0, index)

            for i in range(led_count):
                pygame.draw.circle(self.surface, (OFF_COLOR, ON_COLOR)[i in active_puck_locations], (HORIZONTAL_TRACK_OFFSET + (i * (GAP + RADIUS * 2)), (track_index + 1) * VERTICAL_TRACK_OFFSET), RADIUS, 0)
                if i in stored_puck_locations:
                    pygame.draw.circle(self.surface, AVAILABLE_COLOR, (HORIZONTAL_TRACK_OFFSET + (i * (GAP + RADIUS * 2)), (track_index + 1) * VERTICAL_TRACK_OFFSET), RADIUS, 0)

            if track.paddles[game.LEFT].is_active(time):
                pygame.draw.circle(self.surface, PADDLE_COLOR, (HORIZONTAL_TRACK_OFFSET, (track_index + 1) * VERTICAL_TRACK_OFFSET), RADIUS, 0)

            if track.paddles[game.RIGHT].is_active(time):
                pygame.draw.circle(self.surface, PADDLE_COLOR, (HORIZONTAL_TRACK_OFFSET + ((led_count - 1) * (GAP + RADIUS * 2)), (track_index + 1) * VERTICAL_TRACK_OFFSET), RADIUS, 0)

        for i in range(len(the_game.tracks)):
            track = the_game.tracks[i]
            draw_track(track, i)

        pygame.display.update()

    def quit(self):
        pygame.quit()