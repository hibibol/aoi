import asyncio

from client import bot


from tag import (
    tag_command,
    tag_list_command,
    tag_menu_response,
    create_tag_command,
    create_tag_response,
)
from event import event_command, event_menu_response
from skill import skill_command, skill_menu_response
from uma_data import update_uma_data

import logging

logging.basicConfig(level=logging.CRITICAL)

loop = asyncio.get_event_loop()
task2 = loop.create_task(update_uma_data())
task1 = loop.create_task(bot._ready())

gathered = asyncio.gather(task1, task2, loop=loop)
loop.run_until_complete(gathered)
