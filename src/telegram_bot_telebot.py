import json
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загрузка рецептов из JSON файла
def load_recipes():
    try:
        with open('recipes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Сохранение рецептов в JSON файл
def save_recipes(recipes):
    with open('recipes.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=4)

# Загружаем рецепты из файла
recipes = load_recipes()

# Состояния пользователя для хранения поисковых параметров
user_states = {}

def get_recipes_by_ingredients(ingredient):
    return [recipe for recipe in recipes if ingredient.lower() in recipe["ingredients"].lower()]

def get_recipes_by_time(time):
    return [recipe for recipe in recipes if recipe["time"] == time]

def get_recipes_by_ingredients_and_time(ingredient, time):
    return [recipe for recipe in recipes if ingredient.lower() in recipe["ingredients"].lower() and recipe["time"] == time]

# Инициализация бота
bot = telebot.TeleBot('7548239128:AAEfLI8i7fmnWjCv8iSnUfYoknDyX97HuOA')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Привет! Я бот-помощник по рецептам.\n"
        "Напишите ингредиент или время приготовления, чтобы найти рецепт.\n"
        "Например: 'курица' или '30 минут'.\n"
        "Также можно комбинировать: 'курица 30 минут'."
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(
        message,
        "Доступные команды:\n"
        "/start - начать работу с ботом\n"
        "Для поиска рецепта:\n"
        "- Напишите ингредиент (например, 'курица')\n"
        "- Напишите время приготовления (например, '30 минут')\n"
        "- Комбинируйте (например, 'курица 30 минут')"
    )

@bot.message_handler(func=lambda message: True)
def search_recipes(message):
    query = message.text.lower()
    
    # Разделяем запрос на ингредиент и время
    ingredient = None
    time = None
    
    if "минут" in query:
        time_parts = query.split()
        for part in time_parts:
            if part.isdigit():
                time = f"{part} минут"
                break
        if time:
            ingredient = query.replace(time, "").replace("минут", "").strip()
    else:
        ingredient = query

    # Ищем рецепты
    if ingredient and time:
        matching_recipes = get_recipes_by_ingredients_and_time(ingredient, time)
    elif ingredient:
        matching_recipes = get_recipes_by_ingredients(ingredient)
    elif time:
        matching_recipes = get_recipes_by_time(time)
    else:
        matching_recipes = []

    if matching_recipes:
        recipe = random.choice(matching_recipes)
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("Еще", callback_data=f"next_{ingredient}_{time}"))
        
        message_text = f"{recipe['name']}\n\n"
        message_text += f"Время приготовления: {recipe['time']}\n\n"
        message_text += f"Ингредиенты: {recipe['ingredients']}\n\n"
        message_text += f"Инструкция: {recipe['instructions']}"
        
        bot.reply_to(message, message_text, reply_markup=keyboard)
        
        # Сохраняем состояние пользователя
        user_states[message.from_user.id] = {
            "matching_recipes": matching_recipes,
            "current_index": matching_recipes.index(recipe)
        }
    else:
        bot.reply_to(message, "Извините, рецепты не найдены. Попробуйте другой запрос.")

@bot.callback_query_handler(func=lambda call: True)
def button_callback(call):
    if call.message:
        data = call.data
        
        if data.startswith("next_"):
            # Получаем параметры из callback_data
            _, ingredient, time = data.split("_", 2)
            
            # Получаем состояние пользователя
            state = user_states.get(call.from_user.id, {})
            matching_recipes = state.get("matching_recipes", [])
            current_index = state.get("current_index", 0)
            
            if matching_recipes:
                next_index = (current_index + 1) % len(matching_recipes)
                recipe = matching_recipes[next_index]
                
                keyboard = InlineKeyboardMarkup()
                keyboard.row(InlineKeyboardButton("Еще", callback_data=f"next_{ingredient}_{time}"))
                
                message_text = f"{recipe['name']}\n\n"
                message_text += f"Время приготовления: {recipe['time']}\n\n"
                message_text += f"Ингредиенты: {recipe['ingredients']}\n\n"
                message_text += f"Инструкция: {recipe['instructions']}"
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=message_text,
                    reply_markup=keyboard
                )
                
                # Обновляем состояние
                user_states[call.from_user.id]["current_index"] = next_index

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен!")
    bot.polling(none_stop=True)
