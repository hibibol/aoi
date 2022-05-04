import re
from typing import List

import interactions

from client import bot
from const import SKILL_TYPE
from uma_data import SkillData, UmaData


def get_skill_events(skill_id: str):
    return [
        event["id"] for event in UmaData.events if skill_id in event.get("skills", [])
    ]


def get_has_skill_players(skill_id: str):
    """初期からスキルを持っているキャラ

    Parameters
    ----------
    skill_id : str
    """
    return [
        player for player in UmaData.players if skill_id in player.get("skillList", [])
    ]


def get_event_skill_players(skill_id: str):
    return [
        player
        for player in UmaData.players
        if any(
            event_id in player.get("eventList", [])
            for event_id in get_skill_events(skill_id)
        )
    ]


def get_event_skill_support(skill_id: str):
    return [
        support
        for support in UmaData.supports
        if skill_id in support.get("trainingEventSkill", [])
    ]


def get_training_skill_support(skill_id: str):
    return [
        support
        for support in UmaData.supports
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
        for skill in UmaData.skills
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
    for skill in UmaData.skills:
        if skill["id"] == skill_id[0]:
            embed = create_skill_embed(skill)
            await ctx.send(embeds=embed)
            return
