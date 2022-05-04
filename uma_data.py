import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import List, TypedDict

import aiohttp

JST = timezone(timedelta(hours=+9), "JST")


class DB(TypedDict):
    players: list
    supports: list
    skills: List["SkillData"]
    updateTime: list
    races: list
    buffs: list
    effects: list
    events: List["EventData"]


class SkillData(TypedDict):
    name: str
    imgUrl: str
    rare: str
    describe: str
    id: str
    condition: str
    rarity: int
    db_id: int
    icon_id: int
    ability_value: int
    ability_time: int
    cooldown: int
    ability: dict
    need_skill_point: int
    grade_value: int
    condition2: str
    ability2: list


class EventData(TypedDict):
    name: str
    choiceList: list
    id: str
    pid: str


class UmaData:
    players: list = []
    supports: list = []
    skills: List["SkillData"] = []
    updateTime: list = []
    races: list = []
    buffs: list = []
    effects: list = []
    events: List["EventData"] = []


async def get_uma_data():
    url = "https://raw.githubusercontent.com/wrrwrr111/pretty-derby/master/src/assert/db.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
            uma_data: DB = json.loads(text)
            UmaData.players = uma_data["players"]
            UmaData.supports = uma_data["supports"]
            UmaData.skills = uma_data["skills"]
            UmaData.updateTime = uma_data["updateTime"]
            UmaData.races = uma_data["races"]
            UmaData.buffs = uma_data["buffs"]
            UmaData.effects = uma_data["effects"]
            UmaData.events = uma_data["events"]


async def update_uma_data():
    while True:
        if datetime.now(JST).strftime("%H:%M") == "11:45" or not UmaData.players:
            print("read data")
            await get_uma_data()
        await asyncio.sleep(60)
