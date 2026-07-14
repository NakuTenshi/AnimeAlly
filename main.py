import os
import telebot
import requests
from api import API_TOKEN
from jinja2 import Template
from flask import Flask, request
from playwright.sync_api import sync_playwright
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply


bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

options = [
    "suggest anime",
    "about me",
    "channel"
]

anime_id = None


def StartForm(chat_id, message_id):
    photo_path = os.path.join(BASE_DIR, "images", "start_photo.jpg")
    with open(photo_path, "rb") as photo:
        start_text = (
            "Hii there! Welcome to your super cute bot! :3\n"
            "With this bot, you can discover an *anime* that matches your *unique personality*! 🎉✨\n"
            "Yay! Please pick an option! 💖😊"
        )
        markup = InlineKeyboardMarkup()
        item1 = InlineKeyboardButton(options[0], callback_data=options[0])
        item2 = InlineKeyboardButton(options[1], callback_data=options[1])
        item3 = InlineKeyboardButton(options[2], callback_data=options[2])

        markup.row(item1)
        markup.row(item2, item3)

        bot.send_photo(
            chat_id=chat_id,
            reply_to_message_id=message_id,
            parse_mode="Markdown",
            photo=photo,
            caption=start_text,
            reply_markup=markup
        )


def TakeAnimeName(chat_id, message_id, NotFound=False):
    if NotFound:
        photo_path = os.path.join(BASE_DIR, "images", "notfound_photo.jpg")
        with open(photo_path, "rb") as photo:
            text = (
                "your anime is not found *:(*\n"
                "please try again :),*Sooo*\n"
                "what is your favorite anime? ⛩️🌸🍥:)"
            )
            markup = ForceReply(selective=True)
            bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_to_message_id=message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
    else:
        photo_path = os.path.join(BASE_DIR, "images", "give_photo.jpg")
        with open(photo_path, "rb") as photo:
            text = "what is your favorite anime? ⛩️🌸🍥:)"
            markup = ForceReply(selective=True)
            bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=markup
            )
            bot.delete_message(chat_id=chat_id, message_id=message_id)


def handle_start(message):
    chat_id = message.chat.id
    message_id = message.message_id
    StartForm(chat_id, message_id)


def handle_text_message(message):
    global anime_id

    chat_id = message.chat.id
    message_id = message.message_id

    if not message.reply_to_message:
        return

    replied = message.reply_to_message.caption or ""
    if replied.split('\n')[-1] != "what is your favorite anime? ⛩️🌸🍥:)":
        return

    message_replied_id = message.reply_to_message.message_id
    anime_name = message.text

    req = requests.get(f"https://api.jikan.moe/v4/anime?q={anime_name}")
    if req.status_code != 200:
        bot.send_message(chat_id=chat_id, text="something went wrong")
        return

    try:
        anime_info = req.json()["data"][0]
    except Exception:
        TakeAnimeName(chat_id=chat_id, message_id=message_id, NotFound=True)
        bot.delete_message(chat_id=chat_id, message_id=message_replied_id)
        return

    anime_id = anime_info["mal_id"]
    anime_title = anime_info["titles"][0]["title"]
    anime_description = anime_info["synopsis"].split("\n")[0]
    anime_image = anime_info["images"]["jpg"]["large_image_url"]

    text = (
        f"*title:* {anime_title}\n"
        f"*description:* {anime_description}\n"
        "\n*is that correct?*"
    )

    markup = InlineKeyboardMarkup()
    yes = InlineKeyboardButton("yes", callback_data="yes")
    no = InlineKeyboardButton("no", callback_data="no")
    markup.row(yes, no)

    bot.send_photo(
        chat_id=chat_id,
        photo=anime_image,
        caption=text,
        reply_to_message_id=message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.delete_message(chat_id=chat_id, message_id=message_replied_id)


def handle_callback(call):
    global anime_id

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == options[0]:
        TakeAnimeName(chat_id=chat_id, message_id=message_id)

    elif call.data == options[1]:
        text = (
            "Hi there! My name is *Ehsan*.\n"
            "People on the internet know me as *Naku Tenshi* or *None_0x00*. \n\n"
            "Here are some of my social media links:\n"
            "📱 *Telegram*: [@None_0x00](tg://resolve?domain=None_0x00)📱\n"
            "📸 *Instagram*: [naku_tenshii](https://www.instagram.com/naku_tenshii)📸\n"
            "💻 *GitHub*: [NakuTenshi](https://github.com/nakutenshi)💻\n"
        )
        bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

    elif call.data == options[2]:
        bot.send_message(chat_id=chat_id, text="channel's link: t.me/AnimeAlly")

    elif call.data == "yes":
        if anime_id is None:
            bot.send_message(chat_id=chat_id, text="something went wrong")
            return

        req = requests.get(f"https://api.jikan.moe/v4/anime/{anime_id}/recommendations")
        if req.status_code != 200:
            bot.send_message(chat_id=chat_id, text="something went wrong")
            return

        bot.delete_message(chat_id=chat_id, message_id=message_id)

        photo_path = os.path.join(BASE_DIR, "images", "suggest_photo.jpg")
        with open(photo_path, "rb") as photo:
            animes = "\n".join([
                f'*{i}.* {anime["entry"]["title"]}'
                for i, anime in zip(range(1, 11), req.json()["data"][:10])
            ])
            text = (
                "Here are your adorable animes! ⛩️🌸🍥\n"
                f"{animes}"
                "\nEnjoy your anime adventures! 💕"
            )

            markup = InlineKeyboardMarkup()
            back = InlineKeyboardButton(text="Back", callback_data="back")
            markup.row(back)

            bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
    elif call.data == "no":
        TakeAnimeName(chat_id=chat_id, message_id=message_id)
    elif call.data == "back":
        StartForm(chat_id=chat_id, message_id=message_id)
        
def route_update(update):
    if update.message:
        message = update.message
        if message.text == "/start":
            handle_start(message)
        else:
            handle_text_message(message)
    elif update.callback_query:
        handle_callback(update.callback_query)
        
@app.route("/webhook", methods=["POST"])
def webhook():
    json_update = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_update)
    route_update(update)
    return "OK", 200