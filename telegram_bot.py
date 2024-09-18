import telebot
from telebot import types
import sqlite3
import random

bot = telebot.TeleBot('7485799682:AAGreHWISYkjkBq8fCxt7c4ZvxdrNObM5Tk')

def init_db():
    conn = sqlite3.connect('quest_bot.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users(user_id int primary key, status_user int, visited_locations text)')
    cur.execute('CREATE TABLE IF NOT EXISTS locations(location_id int primary key, name text, map_link text, status_location int)')

    for i in range(1, 6):
        location_name = ['Площа Знань','Фізико-технічний інститут (Корпус 11)','Пам\'ятник Шарі','Корпус №1','Центр культури і мистецтв']
        map_link = ['http://surl.li/dlznjt','http://surl.li/fyxzte','http://surl.li/yuuenu','http://surl.li/gvahyc','http://surl.li/vioixy']
        cur.execute('INSERT OR IGNORE INTO locations (location_id, name, map_link, status_location) VALUES (?, ?, ?, ?)', (i, location_name[i-1], map_link[i-1], 0))

    conn.commit()
    conn.close()

init_db()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    button1 = types.KeyboardButton("Почати")
    button2 = types.KeyboardButton("Відвідав")
    markup.row(button1, button2)
    bot.send_message(message.chat.id, 'Вас вітає "Квест-Бот" для студентів НН ФТІ', reply_markup=markup)

@bot.message_handler(func = lambda message: message.text in ["Почати", "Відвідав"])
def check_button_click(message):
    user_id = message.from_user.id

    if message.text == "Почати":
        bot.send_message(user_id, "Будь ласка, введіть код доступу:")
        bot.register_next_step_handler(message, check_code)

    elif message.text == "Відвідав":
        visit_location(message)


def check_code(message):
    user_id = message.from_user.id
    code = message.text

    if code == "FTI_123":
        conn = sqlite3.connect('quest_bot.sql')
        cur = conn.cursor()
        cur.execute('SELECT status_user, visited_locations FROM users WHERE user_id = ?', (user_id,))
        user = cur.fetchone()

        if user and user[0]:
            bot.send_message(user_id, 'Ви вже почали квест!')
        else:
            cur.execute('INSERT OR IGNORE INTO users (user_id, status_user, visited_locations) VALUES (?, ?, ?)',(user_id, 1, ''))
            conn.commit()

            cur.execute('SELECT location_id FROM locations WHERE status_location = 0')
            available_locations = cur.fetchall()

            if available_locations:
                location_id = random.choice(available_locations)[0]
                cur.execute('UPDATE locations SET status_location = 1 WHERE location_id = ?', (location_id,))

                cur.execute('SELECT name, map_link FROM locations WHERE location_id = ?', (location_id,))
                location_details = cur.fetchone()
                location_name = location_details[0]
                map_link = location_details[1]

                cur.execute('SELECT visited_locations FROM users WHERE user_id = ?', (user_id,))
                visited_locations = cur.fetchone()[0]
                visited_locations += f'{location_id},'
                cur.execute('UPDATE users SET visited_locations = ? WHERE user_id = ?', (visited_locations, user_id))
                conn.commit()
                bot.send_message(user_id, f"Квест розпочато! Ваша локація: {location_name}. Посилання на мапу: {map_link}.")
            else:
                bot.send_message(user_id, "Вільних локацій немає, зачекайте, будь ласка.")
        conn.close()
    else:
        bot.send_message(user_id, 'Неправильний код доступу. Оберіть кнопку "Почати" та спробуйте знов.')


def visit_location(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('quest_bot.sql')
    cur = conn.cursor()
    cur.execute('SELECT status_user, visited_locations FROM users WHERE user_id = ?', (user_id,))
    user = cur.fetchone()

    if user and user[0]:
        visited_locations = user[1]
        visited_locations_list = [loc for loc in visited_locations.split(',') if loc]
        visited_count = len(visited_locations_list)

        if visited_count > 0:
            placeholders = ', '.join(['?'] * visited_count)
            query = f'SELECT location_id FROM locations WHERE status_location = 0 AND location_id NOT IN ({placeholders})'
            cur.execute(query, visited_locations_list)
        else:
            cur.execute('SELECT location_id FROM locations WHERE status_location = 0')

        available_locations = cur.fetchall()

        if available_locations:
            location_id = random.choice(available_locations)[0]
            cur.execute('UPDATE locations SET status_location = 1 WHERE location_id = ?', (location_id,))

            cur.execute('SELECT name, map_link FROM locations WHERE location_id = ?', (location_id,))
            location_details = cur.fetchone()
            location_name = location_details[0]
            map_link = location_details[1]

            visited_locations += f'{location_id},'
            cur.execute('UPDATE users SET visited_locations = ? WHERE user_id = ?', (visited_locations, user_id))
            conn.commit()
            bot.send_message(user_id, f"Ваша нова локація: {location_name}. Посилання на мапу: {map_link}.")
        else:
            bot.send_message(user_id, "Вітаємо, квест завершено!")

    else:
        bot.send_message(user_id, 'Ви не почали квест!')

    conn.close()


bot.infinity_polling()