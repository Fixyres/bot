import telebot
from telebot import types
import random
import logging

TOKEN = '6499777167:AAG0JngqHDIrRo2gu1OtuCVSTSkNODZ5srU'

logging.basicConfig(level=logging.INFO)

bot = telebot.TeleBot(TOKEN)

board_sizes = {
    "3*3": {"size": 3, "win_condition": [3]},
    "4*4": {"size": 4, "win_condition": [3, 4]},
    "5*5": {"size": 5, "win_condition": [3, 4, 5]},
    "6*6": {"size": 6, "win_condition": [3, 4, 5, 6]},
    "7*7": {"size": 7, "win_condition": [3, 4, 5, 6, 7]},
    "8*8": {"size": 8, "win_condition": [3, 4, 5, 6, 7, 8]}
}


rules_dict = {
    "П1": "🌟 Любые оскорбления и провокации запрещены [мут 60-180+варн]",
    "П2": "🚫 Спам/флуд [мут 60-120+варн]. Общение только на русском/украинском/английском языках.",
    "П3": "⛔ Оскорбление родителей [бан😐]",
    "П4": "⚙️ Копание, открывание кейсов и создание зелий в личных сообщениях бота [мут 30]",
    "П5": "🔞 Любой контент 18+ в любом виде [мут 120-180+варн]. Зоофилия и т.д. также запрещены, как в обычных сообщениях, так и в гифках и стикерах.",
    "П6": "📣 Политические дискуссии, ссоры и разногласия решаются в личных сообщениях [мут 60-120+варн]",
    "П7": "🕗 Скримаки запрещено отправлять после 20:00 по мск [мут 60]",
    "П8": "📛 Реклама запрещена. Чтобы поделиться ссылкой на видео и т.д., спросите разрешение у админов [мут 60-180+варн]",
    "П9": "🚫 Раскрытие ссылок на чат и информации о клане [бан☠️]",
    "П10": "🛑 Запрещено отправлять что-то, из-за чего вылетает тг или взлом [мут 60+варн-бан👩‍💻]",
    "П12": "🚷 Не размещайте в группе фотографии, видео или другие данные другого человека без его разрешения [мут 60-бан🫤]",
    "П17": "(Присутствует [1-60 минут (модераторам - 30)])"
}

@bot.message_handler(regexp=r'^Правило \d+$')
def send_rule_by_number(message):
    rule_number = message.text.split()[1]
    rule_key = f"П{rule_number}"
    if rule_key in rules_dict:
        rule_text = rules_dict[rule_key]
        bot.reply_to(message, rule_text, parse_mode='Markdown')
    else:
        bot.reply_to(message, "Такого правила не существует.")

@bot.message_handler(regexp=r'^П\d+$')
def send_rule_by_number(message):
    rule_number = message.text[1:]
    rule_key = f"П{rule_number}"
    if rule_key in rules_dict:
        rule_text = rules_dict[rule_key]
        bot.reply_to(message, rule_text, parse_mode='Markdown')
    else:
        bot.reply_to(message, "Такого правила не существует.")

@bot.message_handler(regexp=r'^Правила$')
def send_all_rules(message):
    rules_text = "Список всех правил:\n\n" + "\n\n".join([f"{key}: {value}" for key, value in rules_dict.items()])
    bot.reply_to(message, rules_text, parse_mode='Markdown')

games = {}

class TicTacToeGame:
    def __init__(self, game_id, player_x, size, win_condition):
        self.game_board = [[' ' for _ in range(size)] for _ in range(size)]
        self.players = {'X': player_x, 'O': None}
        self.current_player = None
        self.player_symbols = {'X': '', 'O': ''}
        self.player_names = {'X': '', 'O': ''}
        self.game_active = False
        self.leave_button_added = False
        self.game_id = game_id
        self.size = size
        self.win_condition = win_condition

    def render_board(self):
        keyboard = types.InlineKeyboardMarkup()
        for row in range(self.size):
            buttons = []
            for col in range(self.size):
                symbol = self.player_symbols[self.game_board[row][col]] if self.game_board[row][col] in self.player_symbols else ' '
                callback_data = f"move:{row}:{col}:{self.game_id}"
                buttons.append(types.InlineKeyboardButton(text=symbol, callback_data=callback_data))
            keyboard.row(*buttons)

        return keyboard

    def check_winner(self, sign):
        for row in self.game_board:
            if any(row[i:i + self.win_condition] == [sign] * self.win_condition for i in range(self.size - self.win_condition + 1)):
                return True

        for col in range(self.size):
            if any(all(self.game_board[row][col] == sign for row in range(row, row + self.win_condition)) for row in range(self.size - self.win_condition + 1)):
                return True

        for i in range(self.size - self.win_condition + 1):
            if all(self.game_board[i + j][i + j] == sign for j in range(self.win_condition)):
                return True
            if all(self.game_board[i + j][self.size - i - j - 1] == sign for j in range(self.win_condition)):
                return True

        return False

    def check_draw(self):
        return all(self.game_board[row][col] != ' ' for row in range(self.size) for col in range(self.size))

    def reset_game(self):
        self.game_board = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.players = {'X': None, 'O': None}
        self.current_player = None
        self.player_names = {'X': '', 'O': ''}
        self.game_active = False
        self.leave_button_added = False

@bot.message_handler(commands=['t'])
def start_game(message):
    chat_id = message.chat.id

    if chat_id not in games:
        games[chat_id] = {'count': 0, 'data': {}}

    markup = types.InlineKeyboardMarkup(row_width=2)
    for size_label, size_info in board_sizes.items():
        callback_data = f'choose_size:{size_info["size"]}'
        button = types.InlineKeyboardButton(size_label, callback_data=callback_data)
        markup.add(button)

    bot.send_message(chat_id, "🔮 Размер игрового поля:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('choose_size'))
def choose_size(call):
    chat_id = call.message.chat.id

    size = int(call.data.split(':')[1])

    game_id = games[chat_id]['count']
    games[chat_id]['count'] += 1

    win_condition = 3
    new_game = TicTacToeGame(game_id, call.from_user.id, size, win_condition)
    games[chat_id]['data'][game_id] = new_game

    user = call.from_user
    new_game.player_names['X'] = user.first_name

    win_condition_buttons = types.InlineKeyboardMarkup(row_width=3)
    for win_condition in board_sizes[f"{size}*{size}"]["win_condition"]:
        callback_data = f'choose_win_condition:{win_condition}:{game_id}'
        button = types.InlineKeyboardButton(str(win_condition), callback_data=callback_data)
        win_condition_buttons.add(button)

    text = f"🏆 В ряд для победы:"
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=win_condition_buttons, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('choose_win_condition'))
def choose_win_condition(call):
    chat_id = call.message.chat.id

    win_condition = int(call.data.split(':')[1])
    game_id = int(call.data.split(':')[2])

    current_game = games[chat_id]['data'].get(game_id)
    if current_game:
        current_game.win_condition = win_condition

        join_button = types.InlineKeyboardButton('🤝 Присоединиться', callback_data=f'join:{game_id}')
        markup = types.InlineKeyboardMarkup().add(join_button)
        text = f"🎮 [{call.from_user.first_name}](tg://user?id={call.from_user.id}), ожидание второго игрока... 🕒\n⬜ Размер поля: {current_game.size}x{current_game.size}\n🚧 {win_condition} в ряд!"
        message = bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')
        current_game.message_id = message.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith('join'))
def join_game(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    game_id = int(call.data.split(':')[1])

    current_game = games[chat_id]['data'].get(game_id)

    if current_game and not current_game.game_active and current_game.players['O'] is None and user_id != current_game.players['X']:
        current_game.players['O'] = user_id
        current_game.player_names['O'] = call.from_user.first_name
        current_game.current_player = random.choice(['X', 'O'])
        current_game.player_symbols['X'] = '❌' if random.random() < 0.5 else '⭕'
        current_game.player_symbols['O'] = '⭕' if current_game.player_symbols['X'] == '❌' else '❌'

        markup = current_game.render_board()

        text = f"🔪  [{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']})  {current_game.player_symbols['O']} 🗡️\n\n⏳ Текущий ход: [{current_game.player_names[current_game.current_player]}](tg://user?id={current_game.players[current_game.current_player]})\n🚧 {current_game.win_condition} в ряд!"

        message = bot.edit_message_text(chat_id=chat_id, message_id=current_game.message_id, text=text, reply_markup=markup, parse_mode='Markdown')
        current_game.message_id = message.message_id
        current_game.game_active = True
    else:
        bot.answer_callback_query(call.id, "Игра уже началась или вы уже участвуете. 🚫")

@bot.message_handler(commands=['leave'])
def leave_game(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in games or 'data' not in games[chat_id]:
        return

    for game_id, current_game in games[chat_id]['data'].items():
        if current_game and current_game.game_active and (user_id == current_game.players['X'] or user_id == current_game.players['O']):
            text = f"👋 [{message.from_user.first_name}](tg://user?id={message.from_user.id}) покинул(а) игру!\n😞 Игра окончена.\n\n🔪 [{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']} 🗡️\n🚧 {current_game.win_condition} в ряд!"

            markup = None
            if not current_game.check_winner(current_game.current_player) and not current_game.check_draw():
                markup = current_game.render_board()

            bot.edit_message_text(chat_id=chat_id, message_id=current_game.message_id, text=text, reply_markup=markup, parse_mode='Markdown')
            del games[chat_id]['data'][game_id]
            current_game.reset_game()
            return

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if chat_id not in games or 'data' not in games[chat_id]:
        return

    query_data = call.data.split(':')
    action = query_data[0]

    if action == 'join':
        game_id = int(query_data[1])
        current_game = games[chat_id]['data'].get(game_id)

        if current_game and not current_game.game_active and current_game.players['O'] is None and user_id != current_game.players['X']:
            current_game.players['O'] = user_id
            current_game.player_names['O'] = call.from_user.first_name
            current_game.current_player = random.choice(['X', 'O'])
            current_game.player_symbols['X'] = '❌' if random.random() < 0.5 else '⭕'
            current_game.player_symbols['O'] = '⭕' if current_game.player_symbols['X'] == '❌' else '❌'

            markup = current_game.render_board()

            text = f"🔪  [{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']})  {current_game.player_symbols['O']} 🗡️\n\n⏳ Текущий ход: [{current_game.player_names[current_game.current_player]}](tg://user?id={current_game.players[current_game.current_player]})\n🚧 {current_game.win_condition} в ряд!"

            message = bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')
            current_game.message_id = message.message_id
            current_game.game_active = True
        else:
            bot.answer_callback_query(call.id, "Игра уже началась или вы уже участвуете. 🚫")
        return

    if action == 'leave':
        game_id = int(query_data[1])
        current_game = games[chat_id]['data'].get(game_id)

        if current_game and current_game.game_active and (user_id == current_game.players['X'] or user_id == current_game.players['O']):
            text = f"👋 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) покинул(а) игру!\n😞 Игра окончена.\n\n🔪 [{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']} 🗡️\n🚧 {current_game.win_condition} в ряд!"

            markup = None
            if not current_game.check_winner(current_game.current_player) and not current_game.check_draw():
                markup = current_game.render_board()

            bot.edit_message_text(chat_id=chat_id, message_id=current_game.message_id, text=text, reply_markup=markup, parse_mode='Markdown')
            del games[chat_id]['data'][game_id]
            current_game.reset_game()
        return

    if action == 'move':
        game_id = int(query_data[3])
        current_game = games[chat_id]['data'].get(game_id)

        if current_game and current_game.game_active:
            row, col = map(int, query_data[1:3])
            if current_game.players[current_game.current_player] != user_id:
                bot.answer_callback_query(call.id, "⛔ Сейчас не ваш ход или вы не участвыете в этой игре!")
                return
            if current_game.game_board[row][col] != ' ':
                bot.answer_callback_query(call.id, "#️⃣ Клетка уже занята!")
                return

            current_game.game_board[row][col] = current_game.current_player
            if current_game.check_winner(current_game.current_player):
                winner_name = current_game.player_names[current_game.current_player]
                text = f"🏆 [{winner_name}](tg://user?id={current_game.players[current_game.current_player]}) победил(а)!\n\n🔪 [{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']} 🗡️\n🚧 {current_game.win_condition} в ряд!"
                bot.edit_message_text(chat_id=chat_id, message_id=current_game.message_id, text=text, reply_markup=current_game.render_board(), parse_mode='Markdown')
                del games[chat_id]['data'][game_id]
                current_game.reset_game()
                return

            if current_game.check_draw():
                text = f"😐 Ничья!\n\n🔪 [{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']} 🗡️\n🚧 {current_game.win_condition} в ряд!"
                bot.edit_message_text(chat_id=chat_id, message_id=current_game.message_id, text=text, reply_markup=current_game.render_board(), parse_mode='Markdown')
                del games[chat_id]['data'][game_id]
                current_game.reset_game()
                return

            current_game.current_player = 'X' if current_game.current_player == 'O' else 'O'
            markup = current_game.render_board()
            text = f"🔪 [{current_game.player_names['X']}](tg://user?id={current_game.players['X']})  {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']} 🗡️\n\n⏳ Текущий ход: [{current_game.player_names[current_game.current_player]}](tg://user?id={current_game.players[current_game.current_player]})\n🚧 {current_game.win_condition} в ряд!"
            bot.edit_message_text(chat_id=chat_id, message_id=current_game.message_id, text=text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(regexp=r'^Кнб камень')
def play_rock(message):
    play_game(message, "камень"+'!')

@bot.message_handler(regexp=r'^Кнб ножницы')
def play_scissors(message):
    play_game(message, "ножницы"+'!')

@bot.message_handler(regexp=r'^Кнб бумага')
def play_paper(message):
    play_game(message, "бумага"+'!')

def play_game(message, user_choice):
    choices = ["камень!", "ножницы!", "бумага!"]
    bot_choice = random.choice(choices)

    result = get_result(user_choice, bot_choice)

    bot.reply_to(message, f"🙋‍♂️ Твой выбор: {user_choice}\n🤖 Мой выбор: {bot_choice}\n{result}")

def get_result(user_choice, bot_choice):
    if user_choice == bot_choice:
        return "😐 Ничья!"
    elif (user_choice == "камень!" and bot_choice == "ножницы!") or \
         (user_choice == "ножницы!" and bot_choice == "бумага!") or \
         (user_choice == "бумага!" and bot_choice == "камень!"):
        return "🏆 Ты выиграл!"
    else:
        return "🙁 Ты проиграл!"

bot.infinity_polling()
