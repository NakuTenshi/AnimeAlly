import requests
import telebot
from telebot.types import InlineKeyboardButton,InlineKeyboardMarkup,ForceReply
from ApiToken import API_TOKEN

bot = telebot.TeleBot(API_TOKEN)
options = [
    "suggest anime",
    "about me",
    "channel"
]

def StartForm(chat_id , message_id):
    with open("./images/start_photo.jpg" , "rb") as photo:
        start_text = (
            "Hii there! Welcome to your super cute bot! :3\n"
            "With this bot, you can discover an *anime* that matches your *unique personality*! 🎉✨\n"
            "Yay! Please pick an option! 💖😊"
        )
        markup = InlineKeyboardMarkup()
        item1 = InlineKeyboardButton(options[0] , callback_data=options[0])
        item2 = InlineKeyboardButton(options[1] , callback_data=options[1])
        item3 = InlineKeyboardButton(options[2] , callback_data=options[2])

        markup.row(item1)
        markup.row(item2,item3)


        bot.send_photo(chat_id=chat_id, 
                        reply_to_message_id=message_id,
                        parse_mode="Markdown",
                        photo=photo, 
                        caption=start_text , 
                        reply_markup=markup)

def TakeAnimeName(chat_id , message_id):
    with open("./images/give_photo.jpg" , "rb") as photo:
        text = (
            "what is your favorite anime? ⛩️🌸🍥:)"
        )

        markup = ForceReply(selective=False)
        bot.send_photo(chat_id=chat_id,
                    photo=photo,
                    caption=text,
                    reply_markup=markup)
        bot.delete_message(chat_id=chat_id,message_id=message_id) #deleting start message

# start command
@bot.message_handler(commands=['start'])
def Start(message):
   chat_id = message.chat.id 
   message_id = message.message_id 
   StartForm(chat_id=chat_id , message_id=message_id)


@bot.message_handler(func= lambda message:True)
def MessageHandle(message):
    global anime_id
    chat_id = message.chat.id 
    message_id = message.message_id 
    
    if message.reply_to_message:
        # photo_image_id = message.reply_to_message.message_id
        if message.reply_to_message.caption == "what is your favorite anime? ⛩️🌸🍥:)":
            # bot.delete_message(chat_id=chat_id,message_id=message_id) # delete user's input
            # bot.delete_message(chat_id=chat_id,message_id=photo_image_id) # delete bot's anime's name question
            anime_name = message.text
            req = requests.get(f"https://api.jikan.moe/v4/anime?q={anime_name}")
            if req.status_code == 200:
                anime_info = req.json()['data'][0]
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
                yes = InlineKeyboardButton("yes" , callback_data="yes")
                no = InlineKeyboardButton("no" , callback_data="no")
                markup.row(yes,no)

                bot.send_photo(chat_id=chat_id, 
                            photo=anime_image, 
                            caption=text, 
                            reply_markup=markup,
                            parse_mode="Markdown"
                            )
            else:
                bot.send_message(chat_id=chat_id , text="something went wrong")


@bot.callback_query_handler(func= lambda call:True)
def CallBackHandle(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == options[0]: # suggest anime
        TakeAnimeName(chat_id=chat_id , message_id=message_id)

    elif call.data == options[1]: # about me
        text = (
            "Hi there! My name is *Ehsan*.\n"
            "People on the internet know me as *Naku Tenshi*. \n\n"
            "Here are some of my social media links:\n"
            "📱 *Telegram*: [@EhsanNaderlou](tg://resolve?domain=EhsanNaderlou)📱\n"
            "📸 *Instagram*: [ehsan.aidev](https://www.instagram.com/ehsan.aidev)📸\n"
            "💻 *GitHub*: [EhsanAiDev](https://github.com/EhsanAiDev)💻\n"
        )

        bot.send_message(chat_id=chat_id,
                         text=text,
                         parse_mode="Markdown")
        
    elif call.data == options[2]: # channel
        bot.send_message(chat_id=chat_id,
                        text="channel's link: t.me/AnimeAlly")

    elif call.data == "yes":
        req = requests.get(f"https://api.jikan.moe/v4/anime/{anime_id}/recommendations")

        if req.status_code == 200:
            bot.delete_message(chat_id=chat_id , message_id=message_id) 
            with open("./images/suggest_photo.jpg" , "rb") as photo:
                animes = "\n".join([f'*{lenght}.* {anime["entry"]["title"]}' for lenght,anime in zip(range(1,11), req.json()["data"][:10])])
                text=(
                    "Here are your adorable animes! ⛩️🌸🍥\n"
                    f"{animes}"
                    "\nEnjoy your anime adventures! 💕"
                )

                markup = InlineKeyboardMarkup()
                back = InlineKeyboardButton(text="Back" , callback_data="back")
                markup.row(back)

                bot.send_photo(chat_id=chat_id,
                            photo=photo,
                            caption=text,
                            reply_markup=markup,
                            parse_mode="Markdown")
        else:
            bot.send_message(chat_id=chat_id , text="something went wrong")

    elif call.data == "no":
        TakeAnimeName(chat_id=chat_id , message_id=message_id)
    
    elif call.data == "back":
        StartForm(chat_id=chat_id , message_id=message_id)

print("starting bot ...")
bot.infinity_polling()