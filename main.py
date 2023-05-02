import os
import telebot
from telebot import types
from translate import Translator
import random
import pandas as pd
import random

BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
translator= Translator(to_lang="ru")

########################################################
################### BOT CONST ##########################
########################################################

BOT_SHORT_HISTORY = {}
MAX_LEN_HISTORY = 10

with open(__file__.replace("test.py", "english-nouns.txt"), "r") as f:
    ENGLISH_NOUNS = f.read().split("\n")
SCORE_DATABASE = pd.DataFrame([{"noun": noun, "score": 0} for noun in ENGLISH_NOUNS])


########################################################
################### BOT UTILS ##########################
########################################################

def add_history(key, message):
    if key in BOT_SHORT_HISTORY:
        BOT_SHORT_HISTORY[key].append(message)
    else:
        BOT_SHORT_HISTORY[key] = [message]
    if len(BOT_SHORT_HISTORY[key]) > MAX_LEN_HISTORY:
        dif = len(BOT_SHORT_HISTORY[key]) - MAX_LEN_HISTORY
        BOT_SHORT_HISTORY[key] = BOT_SHORT_HISTORY[key][dif:]
    assert len(BOT_SHORT_HISTORY[key]) <= MAX_LEN_HISTORY
    print(BOT_SHORT_HISTORY)

########################################################
################### BOT MAIN ###########################
########################################################

@bot.message_handler(commands=['start', 'help'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=3)
    itembtn1 = types.KeyboardButton('Учить новые слова')
    itembtn2 = types.KeyboardButton('Вспомнить старые слова')
    itembtn3 = types.KeyboardButton('Посмотреть статистику')
    markup.add(itembtn1, itembtn2, itembtn3)
    bot.send_message(message.chat.id, "Выберите чем хотите заняться?", reply_markup=markup)

########################################################
################### BOT ASKING #########################
########################################################
@bot.message_handler(func= lambda m: m.text == "Учить новые слова")
def learn_new_words(message): 
    random_words = random.choice(SCORE_DATABASE[SCORE_DATABASE["score"] == 0]["noun"].tolist())
    response = {
        "message": f"Как переводится слово: {random_words}?", 
        "entity": translator.translate(random_words),
        "entity_eng": random_words,
    }
    bot.send_message(message.chat.id, response["message"])
    add_history(message.chat.id, response)

@bot.message_handler(func= lambda m: m.text == "Вспомнить старые слова")
def remember_old_word(message):
    random_words = SCORE_DATABASE[SCORE_DATABASE["score"] < 0]["noun"].tolist()
    if len(random_words) == 0:
        random_words = random.choice(SCORE_DATABASE[SCORE_DATABASE["score"] == 0]["noun"].tolist())
    else:
        random_words = random.choice(random_words)
    response = {
        "message": f"Со словом  {random_words} были проблемы, помнишь как оно переводится?", 
        "entity": translator.translate(random_words),
        "entity_eng": random_words,
    }
    bot.send_message(message.chat.id, response["message"])
    add_history(message.chat.id, response)

@bot.message_handler(func= lambda m: m.text == "Посмотреть статистику")
def get_statistic(message):
    tmp_dict = {
        "bad": SCORE_DATABASE[SCORE_DATABASE["score"] < 0]["noun"].tolist(),
        "good": SCORE_DATABASE[SCORE_DATABASE["score"] > 0]["noun"].tolist(),
        "zero": SCORE_DATABASE[SCORE_DATABASE["score"] == 0]["noun"].tolist()
    }
    bot.send_message(message.chat.id, f"#######################")
    if len(tmp_dict["bad"]) == 0:
        word = ""
    else:
        word = random.choice(tmp_dict["bad"])
    num = len(tmp_dict["bad"])
    bot.send_message(
        message.chat.id, 
        f"Количество ошибок: {num}({word})"
    )
    bot.send_message(message.chat.id, f"#######################")
    num = len(tmp_dict["good"])
    bot.send_message(
        message.chat.id, 
        f"Количество верных ответов: {num}"
    )
    bot.send_message(message.chat.id, f"#######################")
    num = len(tmp_dict["zero"])
    bot.send_message(
        message.chat.id, 
        f"Еще слов впереди: {num}"
    )
    bot.send_message(message.chat.id, f"#######################")

########################################################
################### BOT RESPONSE #######################
########################################################

@bot.message_handler(func= lambda m: BOT_SHORT_HISTORY[m.chat.id][-1]["entity"] == m.text)
def great_again(message):
    index = SCORE_DATABASE[SCORE_DATABASE["noun"] == BOT_SHORT_HISTORY[message.chat.id][-1]["entity_eng"]].index
    SCORE_DATABASE.loc[index, "score"] += 1 
    random_words = random.choice(SCORE_DATABASE[SCORE_DATABASE["score"] == 0]["noun"].tolist())
    response = {
        "message": f"О, ты отлично запомнил слово) А, как переводится слово:{random_words}?", 
        "entity": translator.translate(random_words),
        "entity_eng": random_words,
    }
    bot.send_message(message.chat.id, response["message"])
    add_history(message.chat.id, response)

@bot.message_handler(func= lambda m: BOT_SHORT_HISTORY[m.chat.id][-1]["entity"] != m.text)
def bad_again(message):
    index = SCORE_DATABASE[SCORE_DATABASE["noun"] == BOT_SHORT_HISTORY[message.chat.id][-1]["entity_eng"]].index
    SCORE_DATABASE.loc[index, "score"] -= 1
    if len(SCORE_DATABASE[SCORE_DATABASE["score"] < 0]["noun"].tolist()) <= 3:
        random_words = random.choice(SCORE_DATABASE[SCORE_DATABASE["score"] == 0]["noun"].tolist())
    else:
        random_words = random.choice(SCORE_DATABASE[SCORE_DATABASE["score"] < 0]["noun"].tolist())
    old_words = translator.translate(BOT_SHORT_HISTORY[message.chat.id][-1]["entity"])
    response = {
        "message": f"К сожалению ты опять ошибся. Слово переводится: {old_words}. Давай дальше, как переводится слово: {random_words}?", 
        "entity": translator.translate(random_words),
        "entity_eng": random_words,
    }
    bot.send_message(message.chat.id, response["message"])
    add_history(message.chat.id, response)



bot.infinity_polling()