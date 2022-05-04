import re
from typing import List, Optional

import interactions

from client import bot
from uma_data import EventData, UmaData


def get_event_triger(event_id: str):
    """eventの元となっているサポートやウマ娘を取得する

    Parameters
    ----------
    event_id : str
    """
    for player in UmaData.players:
        if event_id in player["eventList"]:
            return player

    for support in UmaData.supports:
        if event_id in support["eventList"]:
            return support


def create_event_embed(event_data: EventData, event_triger):
    if event_triger:
        return interactions.Embed(
            title=event_data["name"],
            thumbnail={
                "url": f"https://github.com/wrrwrr111/pretty-derby/blob/master/public/{event_triger['imgUrl']}?raw=true"
            },
            fields=[
                interactions.EmbedField(name=choice[0], value="\n".join(choice[1]))
                for choice in event_data["choiceList"]
            ],
        )
    else:
        return interactions.Embed(
            title=event_data["name"],
            fields=[
                interactions.EmbedField(name=choice[0], value="\n".join(choice[1]))
                for choice in event_data["choiceList"]
            ],
        )


@bot.command(
    name="event",
    description="イベントを検索します",
    options=[
        interactions.Option(
            name="event_name",
            description="検索したいイベントの名前を入力してください",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def event_command(
    ctx: interactions.ComponentContext, event_name: Optional[str] = None
):
    events = [
        event
        for event in UmaData.events
        if re.search(event_name, event["name"], re.IGNORECASE)
    ]
    if len(events) == 0:
        await ctx.send("イベントが見つかりませんでした。")
    elif len(events) == 1:
        embed = create_event_embed(events[0], get_event_triger(events[0]["id"]))
        await ctx.send(embeds=embed)
    else:
        i = 0
        while i < len(events):
            event_options = []
            for event in events[i : i + 20]:
                triger = get_event_triger(event["id"])
                if triger:
                    rare = (
                        f"星{triger['rare']}"
                        if triger["rare"].isdecimal()
                        else triger["rare"]
                    )
                    desc = f"{rare} [{triger['name']}] {triger['charaName']}"
                    event_options.append(
                        interactions.SelectOption(
                            label=event["name"], value=event["id"], description=desc
                        )
                    )
                else:
                    event_options.append(
                        interactions.SelectOption(
                            label=event["name"], value=event["id"]
                        )
                    )
            if event_options:
                menu = interactions.SelectMenu(
                    custom_id="event_menu", options=event_options
                )
                await ctx.send(components=menu)
            i += 20


@bot.component(component="event_menu")
async def event_menu_response(ctx: interactions.CommandContext, skill_id: List[str]):
    for event in UmaData.events:
        if event["id"] == skill_id[0]:
            embed = create_event_embed(event, get_event_triger(event["id"]))
            await ctx.send(embeds=embed)
            return
