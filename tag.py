import json
import re
from typing import Dict

import interactions

from client import bot


def get_tag_data() -> Dict[int, Dict[str, str]]:
    with open("tag_data.json") as f:
        tag_data: Dict[int, Dict[str, str]] = json.load(f)
    return tag_data


@bot.command(
    name="tag",
    description="keyに紐付けた文字列を返します",
    options=[
        interactions.Option(
            name="key",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def tag_command(ctx: interactions.ComponentContext, key: str):
    tag_data = get_tag_data()
    match_keys = []
    for tag_key in tag_data.get(ctx.guild_id, {}).keys():
        if re.search(key, tag_key):
            match_keys.append(key)

    if len(match_keys) == 0:
        return await ctx.send(f"{key}に一致するtagは見つかりませんでした")
    elif len(match_keys) == 1:
        return await ctx.send(tag_data[ctx.guild_id][key])
    else:
        i = 0
        while i < len(match_keys):
            key_options = []
            for tag_key in match_keys[i : i + 20]:
                key_options.append(
                    interactions.SelectOption(label=tag_key, value=tag_key)
                )
            if key_options:
                menu = interactions.SelectMenu(
                    custom_id="tag_menu", options=key_options
                )
                await ctx.send(components=menu)
            i += 20


@bot.component(component="tag_menu")
async def tag_menu_response(ctx: interactions.CommandContext, key: str):
    tag_data = get_tag_data()

    if value := tag_data.get(ctx.guild_id, {}).get(key):
        return await ctx.send(value)
    return await ctx.send(f"{key}に一致するtagは見つかりませんでした")


@bot.command(
    name="create_tag",
    description="tagとして文字列を登録します",
    options=[
        interactions.Option(
            name="key",
            description="呼び出す際の鍵となる文字列",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="value",
            description="呼び出したい文字列",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def create_tag_command(ctx: interactions.ComponentContext, key: str, value: str):
    tag_data = get_tag_data()

    if ctx.guild_id not in tag_data:
        tag_data[ctx.guild_id] = {}
    tag_data[ctx.guild_id][key] = value

    with open("tag_data.json", "w") as f:
        json.dump(tag_data, f, ensure_ascii=False, indent=2)
    return await ctx.send("タグを登録しました")


@bot.command(
    name="tag_list",
    description="tagに登録されているkeyの一覧を出力します",
    options=[
        interactions.Option(
            name="pattern",
            description="keyのパターン",
            type=interactions.OptionType.STRING,
            required=False,
        ),
    ],
)
async def tag_list_command(ctx: interactions.ComponentContext, pattern: str = ""):
    tag_data = get_tag_data()
    if keys := "\n".join(
        key for key in tag_data.get(ctx.guild_id, {}) if re.search(pattern, key)
    ):
        return await ctx.send(keys)  # TODO デカすぎるのでpagenationしたい
    return await ctx.send("タグは見つかりませんでした")
