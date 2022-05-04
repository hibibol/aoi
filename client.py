import os

import interactions

TOKEN = os.getenv("TOKEN")

bot = interactions.Client(token=TOKEN)
