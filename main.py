import asyncio
import os
import re
from typing import List, Optional

import interactions

from const import SKILL_TYPE
from uma_data import EventData, SkillData, UmaData, update_uma_data

TOKEN = os.getenv("TOKEN")
bot = interactions.Client(token=TOKEN)


def get_skill_events(skill_id: str):
    return [
        event["id"]
        for event in UmaData.uma_data["events"]
        if skill_id in event.get("skills", [])
    ]


def get_has_skill_players(skill_id: str):
    """初期からスキルを持っているキャラ

    Parameters
    ----------
    skill_id : str
    """
    return [
        player
        for player in UmaData.uma_data["players"]
        if skill_id in player.get("skillList", [])
    ]


def get_event_skill_players(skill_id: str):
    return [
        player
        for player in UmaData.uma_data["players"]
        if any(
            event_id in player.get("eventList", [])
            for event_id in get_skill_events(skill_id)
        )
    ]


def get_event_skill_support(skill_id: str):
    return [
        support
        for support in UmaData.uma_data["supports"]
        if skill_id in support.get("trainingEventSkill", [])
    ]


def get_training_skill_support(skill_id: str):
    return [
        support
        for support in UmaData.uma_data["supports"]
        if skill_id in support.get("possessionSkill", [])
    ]


def create_skill_embed(s: SkillData):
    embed_fields = [
        interactions.EmbedField(
            name="発動条件",
            value=s["condition"],
        ),
        interactions.EmbedField(
            name="効果時間",
            value=str(s["ability_time"] / 10000 if s["ability_time"] > 0 else -1) + "秒",
        ),
        *[
            interactions.EmbedField(
                name=SKILL_TYPE.get(ability["type"], "不明な効果"),
                value=ability["value"],
            )
            for ability in s["ability"]
        ],
    ]
    if has_skill_players := get_has_skill_players(s["id"]):
        embed_fields.append(
            interactions.EmbedField(
                name="スキルを所持しているウマ娘",
                value="\n".join(
                    "[" + player["name"] + "] " + player["charaName"]
                    for player in has_skill_players
                ),
            )
        )
    if event_skill_players := get_event_skill_players(s["id"]):
        embed_fields.append(
            interactions.EmbedField(
                name="イベントで取得可能なウマ娘",
                value="\n".join(
                    "[" + player["name"] + "] " + player["charaName"]
                    for player in event_skill_players
                ),
            )
        )
    if training_skill_supports := get_training_skill_support(s["id"]):
        embed_fields.append(
            interactions.EmbedField(
                name="練習で取得可能なサポート",
                value="\n".join(
                    support["rare"]
                    + " ["
                    + support["name"]
                    + "] "
                    + support["charaName"]
                    for support in training_skill_supports
                ),
            )
        )

    if event_skill_supports := get_event_skill_support(s["id"]):
        embed_fields.append(
            interactions.EmbedField(
                name="イベントで取得可能なサポート",
                value="\n".join(
                    support["rare"]
                    + " ["
                    + support["name"]
                    + "] "
                    + support["charaName"]
                    for support in event_skill_supports
                ),
            )
        )

    embed = interactions.Embed(
        title=s["name"],
        description=s["describe"],
        thumbnail={
            "url": f"https://github.com/wrrwrr111/pretty-derby/blob/master/public/{s['imgUrl']}?raw=true"
        },
        fields=embed_fields,
    )
    return embed


@bot.command(
    name="skill",
    description="スキルを検索します",
    options=[
        interactions.Option(
            name="skill_name",
            description="検索したいスキルの名前を入力してください",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def skill_command(ctx: interactions.CommandContext, skill_name: str):

    skills = [
        skill
        for skill in UmaData.uma_data["skills"]
        if re.search(skill_name, skill["name"], re.IGNORECASE)
    ]
    if len(skills) == 0:
        await ctx.send(f"{skill_name}とマッチするスキルは見つかりませんでした")
    elif len(skills) == 1:
        s = skills[0]
        embed = create_skill_embed(s)
        await ctx.send(embeds=embed)
    else:
        menu = interactions.SelectMenu(
            custom_id="skill_menu",
            options=[
                interactions.SelectOption(label=skill["name"], value=skill["id"])
                for skill in skills
            ],
        )
        await ctx.send(components=menu)


@bot.component(component="skill_menu")
async def skill_menu_response(ctx: interactions.CommandContext, skill_id: List[str]):
    for skill in UmaData.uma_data["skills"]:
        if skill["id"] == skill_id[0]:
            embed = create_skill_embed(skill)
            await ctx.send(embeds=embed)
            return


def get_event_triger(event_id: str):
    """eventの元となっているサポートやウマ娘を取得する

    Parameters
    ----------
    event_id : str
    """
    for player in UmaData.uma_data["players"]:
        if event_id in player["eventList"]:
            return player

    for support in UmaData.uma_data["supports"]:
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
        for event in UmaData.uma_data["events"]
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
async def skill_menu_response(ctx: interactions.CommandContext, skill_id: List[str]):
    for event in UmaData.uma_data["events"]:
        if event["id"] == skill_id[0]:
            embed = create_event_embed(event, get_event_triger(event["id"]))
            await ctx.send(embeds=embed)
            return


loop = asyncio.get_event_loop()
asyncio.ensure_future(update_uma_data())
asyncio.ensure_future(bot._ready())
loop.run_forever()
