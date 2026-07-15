import os
import base64
import random
import telebot
import requests
from api import API_TOKEN
from jinja2 import Template
from flask import Flask, request
from playwright.sync_api import sync_playwright
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply


bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
browser =  sync_playwright.chromium.launch(executable_path="/snap/bin/chromium")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

options = [
    "suggest anime",
    "about me",
    "channel"
]

anime_id = None
template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Document</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Bungee&display=swap" rel="stylesheet">

<style>
html, body {
    margin: 0;
    width: 1280px;
    height: 720px;
    overflow: hidden;
    display: grid;
}
body {
    position: relative;
    border: 2px solid black;
    border-radius: 10px;
}

body::before {
    content: "";
    position: absolute;
    inset: 0;

    background-image: url("data:image/png;base64,{{ background_base64 }}");
    background-size: cover;
    background-position: center;

    filter: blur(10px);
    transform: scale(1.1); /* جلوگیری از لبه‌های سفید بعد از blur */

    z-index: -1;
}

#title-div {
    text-align: center;
    height: fit-content;
    padding: 8px 20px;
    border-radius: 15px;

    background: rgba(255, 105, 180, 0.35);

    box-shadow:
        0 15px 23px rgba(255, 105, 180, 0.8);

    border: 1px solid rgba(255, 182, 193, 0.7);
}
#text_title {
    margin: 0px;

    font-family: 'Bebas Neue', sans-serif;
    font-size: 35px;
    font-weight: 200;
    letter-spacing: 1px;
}
#anime_name{
    margin: 0px;
    font-family: 'Bungee';
    font-size: 29px;
    font-weight: 100;
    
}

#suggestions {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    grid-template-rows: repeat(2, auto);
    gap: 18px;
    padding: 25px;
    position: relative;
    z-index: 1;
}


.anime-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px;
    border-radius: 15px;
    background: rgba(255, 182, 193, 0.22);
    border: 1px solid rgba(255, 182, 193, 0.35);
    backdrop-filter: blur(6px);
    box-shadow:
        0 8px 20px rgba(255, 105, 180, 0.25);
    transition: 0.3s ease;

    min-width: 0;
}


.anime-card:hover {
    transform: translateY(-5px);
    box-shadow:
        0 15px 30px rgba(255, 105, 180, 0.45);
}


.anime-card img {
    width: 160px;
    height: 210px;
    object-fit: cover;
    border-radius: 12px;
    box-shadow:
        0 5px 15px rgba(0,0,0,0.3);
}


.anime-card span {
    margin-top: 12px;
    width: 100%;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-align: center;
    color: #3a1f2f;
    text-shadow:
        0 1px 3px rgba(255, 255, 255, 0.7);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>

</head>
<body>
    <div id="title-div">
        <span id="text_title">Best anime that are like: <span id="anime_name">{anime_name}</span></span>
    </div>

    <div id="suggestions">
        {% for anime in animes %}
            <div class="anime-card">
                <img src="data:image/jpeg;base64,{{ anime.image_base64 }}">
                <span>{{ anime.id }}. {{ anime.name }}</span>
            </div>
        {% endfor %}

    </div>
</body>
</html>
""")

background_images_path = [os.path.join("/images/sakura_backgrounds", image_name) for image_name in os.listdir("/images/sakura_backgrounds")]
background_images_base64 = []

for image_path in background_images_path:
    with open(image_path, "rb") as image:
        background_images_base64.append(base64.b64encode(image.read()).decode("utf-8"))

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
        

        anime_sugetion_request = requests.get(f"https://api.jikan.moe/v4/anime/{anime_id}/recommendations")
        if anime_sugetion_request.status_code == 200:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            x = 0 
            raw_top_animes = anime_sugetion_request.json()["data"][:10]
            top_animes = []

            for anime in raw_top_animes:
                x += 1 
                anime_title = anime["entry"]["title"]
                image_url = list(anime["entry"]["images"]["jpg"].values())[-1]
                image_base64 = None

                image_request = requests.get(image_url)
                if image_request.status_code == 200:
                    image_base64 = base64.b64encode(image_request.content)

                top_animes.append({"id": x, "name": anime_title, "image_base64": image_base64})



            html = template.render(background_base64=random.choice(background_images_base64) ,animes= top_animes)
            new_page = browser.new_page(viewport={
                "width": 1280,
                "height": 720
            })
            new_page.set_content(html)
            photo = new_page.screenshot()
            new_page.close()

            anime_titles = [f"{anime['id']}. {anime['name']}" for anime in top_animes]
            text = (
                "Here are your adorable animes! ⛩️🌸🍥\n"
                f"{'\n'.join(anime_titles)}"
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
        else:
            bot.send_message(chat_id=chat_id, text="something went wrong")
            return
        
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