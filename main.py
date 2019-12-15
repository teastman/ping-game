import asyncio
import game
import gui
from pygame import locals
from rx.scheduler.eventloop import AsyncIOScheduler
from typing import Optional

UPDATE_FPS = 30
RENDER_FPS = 60
SHOW_GUI = True

the_game = game.Game()

if SHOW_GUI:
    GUI = gui.GUI(800, 50)


async def handle_input():
    loop = asyncio.get_running_loop()
    input_queue = asyncio.Queue()

    if SHOW_GUI:
        loop.run_in_executor(None, GUI.handle_input, loop, input_queue)

    while True:
        input_event = await input_queue.get()
        # if input_event.type == locals.KEYDOWN:
        #     print(input_event.key)
        if input_event.type == locals.QUIT:
            loop.stop()
        if input_event.type == locals.KEYDOWN and input_event.key == 276:
            loop.create_task(the_game.tracks[0].paddles[game.LEFT].press(loop.time()))
        if input_event.type == locals.KEYDOWN and input_event.key == 275:
            loop.create_task(the_game.tracks[0].paddles[game.RIGHT].press(loop.time()))
        

async def update_state() -> None:
    def do_work(time: float) -> None:
        the_game.update(time)
    await fps_loop(do_work, UPDATE_FPS)

async def render() -> None:
    def do_work(time: float) -> None:
        if SHOW_GUI:
            GUI.render(the_game, time)
    await fps_loop(do_work, RENDER_FPS)

async def fps_loop(do_work, fps: int = 60, loop: Optional[asyncio.events.AbstractEventLoop] = None) -> None:
    if loop is None:
        loop = asyncio.get_running_loop()
    last_time = loop.time()
    while True:
        do_work(loop.time())
        loop_time = loop.time()
        sleep_time = (1.0 / fps) - (loop_time - last_time)
        last_time = loop.time()
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

# async def main():
loop = asyncio.get_event_loop()
loop.create_task(handle_input())
loop.create_task(update_state())
loop.create_task(render())
loop.run_forever()

# asyncio.run(main())
quit()