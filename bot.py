import config
import telebot
import sqlite3
import random
from telebot import types

bot = telebot.TeleBot(config.TOKEN)

# Команда «Старт»
@bot.message_handler(commands=["start"])
def start(m, res=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Показать задания")
    btn2 = types.KeyboardButton("Создать задание")
    btn3 = types.KeyboardButton("Выполнить задание")
    btn4 = types.KeyboardButton("Мой счет")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    cursor.execute(f"select name from users where id={m.chat.id}")
    name = "".join(cursor.fetchone())
    bot.send_message(m.chat.id, text=f"Привет, {name}! Я тестовый бот. Выбери команду.", reply_markup=markup)

def registration(message):
    if users_dict.get(message.chat.id, {}).get("registration", False):
        cursor.execute(f"INSERT INTO users(id, name) values({message.chat.id}, '{message.text}')")
        sqlite_connection.commit()
        bot.send_message(message.chat.id, "Регистрация прошла успешно")
    else:
        bot.send_message(message.chat.id, "Введите имя пользователя")
        users_dict[message.chat.id]={'registration':True}

def add(message):
    if users_dict.get(message.chat.id, {}).get('create_task', False) and message.chat.id in users_dict and not(users_dict.get(message.chat.id, {}).get('price', False)):
        cursor.execute(f"INSERT INTO tasks(title) values('{message.text}')")
        users_dict[message.chat.id]['price'] = cursor.lastrowid
        bot.send_message(message.chat.id, 'Введите стоимость')
    elif users_dict.get(message.chat.id, {}).get('price', False) and message.chat.id in users_dict:
        cursor.execute(f"select * from users")
        scores = cursor.fetchall()
        minim = 1000000
        for i in scores:
            if i[2]<minim:
                minim = i[2]
        users_id = []
        for y in scores:
            if y[2]==minim:
                users_id.append(y[0])
        rand_id = random.choice(users_id)
        cursor.execute(f"update tasks SET price = {message.text} where id = ({users_dict[message.chat.id]['price']})")
        cursor.execute(f"update tasks SET executor_id = {rand_id} where id = ({users_dict[message.chat.id]['price']})")
        del users_dict[message.chat.id]['create_task']
        del users_dict[message.chat.id]['price']
    sqlite_connection.commit()


def complete(message):
    if users_dict.get(message.chat.id, {}).get('complete_task', False) and message.chat.id in users_dict and not(users_dict.get(message.chat.id, {}).get('task_id', False)):
        users_dict[message.chat.id]['task_id'] = message.text
        bot.send_message(message.chat.id, f'Вы уверены, что выполнили это {message.text} задание? да/нет')
    elif users_dict.get(message.chat.id, {}).get('task_id', False) and message.chat.id in users_dict:
        if message.text.lower() == "да":
            cursor.execute(f"update tasks SET is_done = 1 where id = ({users_dict[message.chat.id]['task_id']})")
            sqlite_connection.commit()
            bot.send_message(message.chat.id, f"Задание {users_dict[message.chat.id]['task_id']} выполнено")
        else:
            bot.send_message(message.chat.id, "Операция отменена")
        del users_dict[message.chat.id]['complete_task']
        del users_dict[message.chat.id]['task_id']




@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли
    print(message.text)
    cursor.execute(f"select * from users where id={message.chat.id}")
    if not len(cursor.fetchall()):
        registration(message)
        return

    if users_dict.get(message.chat.id, {}).get("create_task", False):
        add(message)

    if users_dict.get(message.chat.id, {}).get("complete_task", False):
        complete(message)

   # bot.send_message(message.chat.id, message.text)
    if (message.text=="Показать задания"):
        res =""
        cursor.execute("SELECT id, title, price, executor_id, is_done FROM tasks;")
        all_results = cursor.fetchall()
        for x in all_results:
            cursor.execute(f"select name from users where id = {x[3]}")
            name = cursor.fetchone()[0]
            res = res + '\n' + "".join([f"{x[0]} \t {x[1]} \t {x[2]} \t {name} \t {x[4]}"])
        bot.send_message(message.chat.id, f"id \t title \t price \t executor \t is_done \n {res}")
        #bot.send_message(message.chat.id, res)
        print(all_results)

    if (message.text=="Мой счет"):
        cursor.execute("select name, score from users")
        all_results = cursor.fetchall()
        res = "\n".join([f"{x[0]}: {x[1]}" for x in all_results])
        bot.send_message(message.chat.id, res)
        print(all_results)


    if (message.text=="Выполнить задание"):
        bot.send_message(message.chat.id, "Введите id задания")
        users_dict[message.chat.id] = users_dict.get(message.chat.id, {})
        users_dict[message.chat.id]['complete_task'] = True

    if (message.text == "Создать задание"):
        bot.send_message(message.chat.id, "Введите название задания")
        users_dict[message.chat.id] = users_dict.get(message.chat.id, {})
        users_dict[message.chat.id]['create_task'] = True

if __name__ == "__main__":
    users_dict = {}
    sqlite_connection = sqlite3.connect('bot_bd.db', check_same_thread=False)
    cursor = sqlite_connection.cursor()
    tasks_query = '''CREATE TABLE if not exists tasks (
                                    id INTEGER PRIMARY KEY,
                                    title TEXT NOT NULL,
                                    date_creation timestamp NOT NULL default current_timestamp,
                                    price INTEGER,
                                    executor_id TEXT,
                                    is_done INTEGER not null default 0);'''

    users_query = '''CREATE TABLE if not exists users (
                                        id INTEGER PRIMARY KEY,
                                        name TEXT NOT NULL,
                                        score INTEGER NOT NULL default 0
                                        );'''

    cursor.execute(tasks_query)
    cursor.execute(users_query)
    sqlite_connection.commit()
    cursor.execute("select id from users")
    all_results = cursor.fetchall()
    users_dict = {x[0]: {} for x in all_results}
    print(users_dict)
    bot.polling(none_stop=True)