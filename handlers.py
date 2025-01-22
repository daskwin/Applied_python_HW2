from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from states import ProfileStates, FoodLogStates
from config import API_KEY_WEATHER
from utils import (
    get_current_temperature,
    calc_daily_water,
    calc_daily_calories,
    get_food_info,
    get_calories_burned_ninjas
)

users = {}

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "Добро пожаловать! Используйте /set_profile, чтобы ввести свои данные."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "<b>Доступные команды:</b>\n\n"
        "⚙️ <b>/set_profile</b> — настроить ваш профиль.\n"
        "❓ <b>/help</b> — сообщение с командами.\n\n"
        "📝 <b>Логирование:</b>\n"
        "💧 <b>/log_water</b> — записать выпитую воду.\n"
        "🥗 <b>/log_food</b> — записать съеденный продукт.\n"
        "🔥 <b>/log_workout</b> — записать тренировку.\n\n"
        "📊 <b>/check_progress</b> — проверить ваш текущий прогресс по воде и калориям."
    )
    await message.reply(help_text, parse_mode="HTML")


@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    """
    Начало настройки профиля.
    """
    # Запрос веса пользователя
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(ProfileStates.weight)


@router.message(ProfileStates.weight)
async def process_weight(message: Message, state: FSMContext):
    """
    Обработка веса и запрос роста.
    """
    # Проверка на корректность ввода веса, тип - float
    try:
        weight = float(message.text.replace(',', '.'))
    except ValueError:
        # Повторный ввод, если значение не корретно
        return await message.reply("Пожалуйста, введите число.")

    user_id = message.from_user.id
    # Инициализация записи для пользователя
    if user_id not in users:
        users[user_id] = {}

    # Сохранение веса пользователя
    users[user_id]["weight"] = weight

    # Запрос на ввод роста
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(ProfileStates.height)


@router.message(ProfileStates.height)
async def process_height(message: Message, state: FSMContext):
    """
    Обработка роста и запрос возраста.
    """
    # Проверка на корректность ввода роста, тип - float
    try:
        height = float(message.text.replace(',', '.'))
    except ValueError:
        return await message.reply("Пожалуйста, введите число.")

    user_id = message.from_user.id
    # Сохранение веса пользователя
    users[user_id]["height"] = height

    # Запрос на ввод возраста
    await message.reply("Введите ваш возраст:")
    await state.set_state(ProfileStates.age)


@router.message(ProfileStates.age)
async def process_age(message: Message, state: FSMContext):
    """
    Обработка возраста и запрос пола.
    """
    # Проверка на корректность ввода возраста, тип - int
    try:
        age = int(message.text)
    except ValueError:
        return await message.reply("Пожалуйста, введите целое число.")

    user_id = message.from_user.id
    # Сохранение возраста пользователя
    users[user_id]["age"] = age

    # Селектор пола
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мужской", callback_data="gender_male")],
            [InlineKeyboardButton(text="Женский", callback_data="gender_female")]
        ]
    )
    await message.reply("Выберите ваш пол:", reply_markup=keyboard)
    await state.set_state(ProfileStates.gender)


@router.callback_query(StateFilter(ProfileStates.gender))
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработка выбор пола и запрос активности.
    """
    user_id = callback_query.from_user.id
    if callback_query.data == "gender_male":
        # Сохранение если выбран мужской пол
        users[user_id]["gender"] = "male"
        gender_text = "Мужской"
    elif callback_query.data == "gender_female":
        # Сохранение если выбран женский пол
        users[user_id]["gender"] = "female"
        gender_text = "Женский"
    else:
        await callback_query.answer("Некорректный выбор.")
        return

    await callback_query.message.reply(f"Вы выбрали: {gender_text}")
    await callback_query.answer(f"Вы выбрали: {gender_text}")

    # Запрос минут активности
    await callback_query.message.reply("Сколько минут активности у вас в день?")
    await state.set_state(ProfileStates.activity_minutes)


@router.message(ProfileStates.activity_minutes)
async def process_activity_minutes(message: Message, state: FSMContext):
    """
    Обработка активности и выбор уровня активности.
    """
    # Проверка на корректность ввода возраста, тип - int
    try:
        activity_minutes = int(message.text)
    except ValueError:
        return await message.reply("Пожалуйста, введите целое число.")

    user_id = message.from_user.id
    # Сохранение активности (мин.) пользователя
    users[user_id]["activity_minutes"] = activity_minutes

    # Селектор уровня активности
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Лёгкая", callback_data="activity_light")],
            [InlineKeyboardButton(text="Умеренная", callback_data="activity_middle")],
            [InlineKeyboardButton(text="Высокая", callback_data="activity_high")]
        ]
    )
    await message.reply("Выберите уровень активности:", reply_markup=keyboard)
    await state.set_state(ProfileStates.activity_level)


@router.callback_query(StateFilter(ProfileStates.activity_level))
async def process_activity_level(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработка выбор уровня активности и запрос города.
    """
    user_id = callback_query.from_user.id
    if callback_query.data == "activity_light":
        users[user_id]["activity_level"] = "light"
        activity_text = "Лёгкая"
    elif callback_query.data == "activity_middle":
        users[user_id]["activity_level"] = "middle"
        activity_text = "Умеренная"
    elif callback_query.data == "activity_high":
        users[user_id]["activity_level"] = "high"
        activity_text = "Высокая"
    else:
        await callback_query.answer("Некорректный выбор.")
        return

    await callback_query.message.reply(f"Вы выбрали уровень активности: {activity_text}")
    await callback_query.answer(f"Вы выбрали уровень активности: {activity_text}")

    # Запрос города
    await callback_query.message.reply("В каком городе вы находитесь?")
    await state.set_state(ProfileStates.city)


@router.message(ProfileStates.city)
async def process_city(message: Message, state: FSMContext):
    """
    Обработка города и завершение диалога FSMContext.
    """
    user_id = message.from_user.id
    city = message.text.strip()

    users[user_id]["city"] = city

    users[user_id].setdefault("logged_water", 0)
    users[user_id].setdefault("logged_calories", 0)
    users[user_id].setdefault("burned_calories", 0)

    temp_result_api = get_current_temperature(city, API_KEY_WEATHER)

    # Проверка получения текущей температуры, если не нашло - берем температуру 20°C
    if isinstance(temp_result_api, dict):
        await message.reply(f"Не удалось получить температуру для '{city}'. "
                            f"Считаем, что на улице 20°C.")
        temperature = 20
    else:
        temperature = temp_result_api

    weight = users[user_id]["weight"]
    height = users[user_id]["height"]
    age = users[user_id]["age"]
    activity_minutes = users[user_id]["activity_minutes"]
    activity_level = users[user_id]["activity_level"]
    gender = users[user_id]["gender"]

    # Подсчет дневных норм
    water_goal = calc_daily_water(weight, activity_minutes, temperature)
    calorie_goal = calc_daily_calories(weight, height, age, activity_minutes, activity_level, gender)

    users[user_id]["water_goal"] = int(water_goal)
    users[user_id]["calorie_goal"] = int(calorie_goal)

    summary = (
        "<b>Ваш профиль успешно сохранён!</b>\n"
        f"⚖️ <b>Вес:</b> {weight} кг\n"
        f"📏 <b>Рост:</b> {height} см\n"
        f"🌟 <b>Возраст:</b> {age}\n"
        f"👤 <b>Пол:</b> {'Мужской' if gender == 'male' else 'Женский'}\n"
        f"💪️ <b>Активность:</b> {activity_minutes} мин/день ({activity_level.capitalize()})\n"
        f"🏙️ <b>Город:</b> {city} (температура: {temperature}°C)\n\n"
        f"Рассчитанные нормы:\n"
        f"💧 <b>Вода:</b> {users[user_id]['water_goal']} мл/день\n"
        f"🥗 <b>Калории:</b> {users[user_id]['calorie_goal']} ккал/день\n"
    )

    await message.reply(summary, parse_mode="HTML")
    await state.clear()


@router.message(Command("log_water"))
async def cmd_log_water(message: Message, command: CommandObject):
    """
    Логирует выпитую пользователем воду.

    Пример: /log_water 250

    Args:
        message (Message): Сообщение от пользователя.
        command (CommandObject): Объект команды, содержащий аргументы команды (количество выпитой воды в мл.).
    """
    user_id = message.from_user.id

    # Если нет профиля - перенаправляет на команду /set_profile
    if user_id not in users or "water_goal" not in users[user_id]:
        await message.reply("Сначала настройте профиль командой /set_profile.")
        return

    # Если нет аргументов
    if not command.args:
        await message.reply("Укажите количество воды в миллилитрах, например:\n/log_water 300")
        return

    # Проверка на целочисленность
    try:
        water_amount = int(command.args)
    except ValueError:
        await message.reply("Пожалуйста, введите целое число мл.")
        return

    users[user_id]["logged_water"] += water_amount

    water_goal = users[user_id]["water_goal"]
    logged_water = users[user_id]["logged_water"]
    delta = water_goal - logged_water

    if delta > 0:
        msg = (
            f"Вы добавили {water_amount} мл. воды.\n"
            f"Всего выпито: {logged_water} мл.\n"
            f"Осталось до нормы: {delta} мл."
        )
    else:
        msg = (
            f"Вы добавили {water_amount} мл. воды.\n"
            f"Всего выпито: {logged_water} мл.\n"
            f"Поздравляю!🎊 Вы достигли (или превысили) дневную норму воды."
        )

    await message.reply(msg)


@router.message(Command("log_food"))
async def cmd_log_food(message: Message, command: CommandObject, state: FSMContext):
    """
    Логирует съеденную пользователем еду.

    Пример: /log_food банан

    Args:
        message (Message): Сообщение от пользователя.
        command (CommandObject): Объект команды, содержащий аргументы команды (наименование продукта).
        state (FSMContext): Для сохранения данных между шагами.
    """
    user_id = message.from_user.id

    # Если нет профиля - перенаправляет на команду /set_profile
    if user_id not in users or "calorie_goal" not in users[user_id]:
        await message.reply("Сначала настройте профиль командой /set_profile.")
        return

    # Если нет аргументов
    if not command.args:
        await message.reply("Формат: /log_food <название продукта>\nНапример: /log_food банан")
        return

    product_name = command.args.strip()
    info = get_food_info(product_name)

    # Продукт не найден
    if not info:
        await message.reply(f"Не удалось найти продукт '{product_name}' в базе OpenFoodFacts.")
        return

    # Для следующего шага
    await state.update_data(
        product_name=info["name"],
        calories_per_100=info["calories"]
    )

    # Вызов граммовки съеденного
    await message.reply(
        f"Найдено: {info['name']}.\n"
        f"Калорийность: {info['calories']} ккал на 100 г.\n"
        "Сколько грамм вы съели?"
    )
    await state.set_state(FoodLogStates.waiting_for_grams)


@router.message(FoodLogStates.waiting_for_grams)
async def process_food_grams(message: Message, state: FSMContext):
    """
    Ввод количества граммов съеденного продукта.
    """
    user_id = message.from_user.id

    # Проверка на корректность ввода граммов, тип - float
    try:
        grams = float(message.text)
    except ValueError:
        await message.reply("Введите число (количество граммов).")
        return

    data = await state.get_data()
    product_name = data.get("product_name")
    cals_per_100 = data.get("calories_per_100")

    if cals_per_100 is None:
        await message.reply(f"Не удалось получить данные о калорийности для продукта: {product_name}.")
        await state.clear()
        return

    try:
        cals_per_100 = float(cals_per_100)
    except (ValueError, TypeError):
        await message.reply(f"Неверное значение калорийности для продукта: {product_name}.")
        await state.clear()
        return

    total_cals = (cals_per_100 * grams) / 100.0

    users[user_id]["logged_calories"] = users[user_id].get("logged_calories") + total_cals

    total_cals_rounded = round(total_cals, 1)
    total_logged = round(users[user_id]["logged_calories"], 1)

    await message.reply(
        f"Записано: {product_name} ~ {grams} г = {total_cals_rounded} ккал.\n"
        f"Всего за сегодня: {total_logged} ккал."
    )

    await state.clear()


@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message, command: CommandObject):
    """
    Логирование тренировки через API Ninjas.
    Пример и формат: /log_workout <activity> <minutes>
                     /log_workout running 30
    """
    user_id = message.from_user.id

    # Если нет профиля - перенаправляет на команду /set_profile
    if user_id not in users or "calorie_goal" not in users[user_id] or "water_goal" not in users[user_id]:
        await message.reply("Сначала настройте профиль командой /set_profile.")
        return

    if not command.args:
        await message.reply("Используйте: /log_workout <activity> <minutes>\nНапример: /log_workout running 30 (Только английский!)")
        return

    parts = command.args.split()
    if len(parts) < 2:
        await message.reply("Нужно указать 2 аргумента: /log_workout <activity> <minutes>")
        return

    activity = parts[0]

    try:
        minutes = int(parts[1])
    except ValueError:
        await message.reply("Минуты должны быть числом.")
        return

    if minutes <= 0:
        await message.reply("Время тренировки должно быть > 0.")
        return

    user_weight_kg = users[user_id]["weight"]

    burned_cals = get_calories_burned_ninjas(activity, minutes, user_weight_kg)

    if burned_cals == 0.0:
        await message.reply(f"Не удалось найти/рассчитать калории для '{activity}'.")
        return

    users[user_id]["burned_calories"] += burned_cals
    extra_water = (minutes // 30) * 200
    users[user_id]["water_goal"] += extra_water

    water_goal = users[user_id]["water_goal"]
    burned_rounded = round(burned_cals, 1)
    total_rounded = round(users[user_id]["burned_calories"], 1)
    total_water = users[user_id]["logged_water"]

    response_text = (
        f"Тренировка: {activity} ({activity}), {minutes} мин.\n"
        f"Сожжено (примерно): {burned_rounded} ккал.\n"
        f"Всего сожжено за сегодня: {total_rounded} ккал.\n\n"
    )

    if extra_water > 0:
        response_text += (
            f"Дополнительно: +{extra_water} мл. воды (по 200 мл за каждые 30 минут).\n"
            f"Всего выпито: {total_water} мл.\n"
            f"Осталось выпить: {water_goal-total_water} мл."
        )
    else:
        response_text += (
            f"До 30 минут — без добавки воды.\n"
            f"Всего выпито: {total_water} мл."
            f"Осталось выпить: {water_goal-total_water} мл."
        )

    await message.answer(response_text)


@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message):
    """
    Текущие показатели воды и калорий.
    """
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Сначала настройте свой профиль командой /set_profile.")
        return

    user_data = users[user_id]

    # Достаём данные
    water_goal = user_data.get("water_goal")
    logged_water = user_data.get("logged_water")

    calorie_goal = user_data.get("calorie_goal")
    logged_calories = user_data.get("logged_calories")
    burned_calories = user_data.get("burned_calories")

    water_delta = water_goal - logged_water
    if water_delta < 0:
        water_delta = 0

    net_calories = logged_calories - burned_calories

    progress_text = (
        "<b>📊 Прогресс</b>\n\n"
        f"<u>💧 Вода</u>:\n"
        f"- Выпито: {logged_water} мл из {water_goal} мл\n"
        f"- Осталось: {water_delta} мл\n\n"

        f"<u>🥗 Калории</u>:\n"
        f"- Потреблено: {logged_calories} ккал из {calorie_goal} ккал\n"
        f"- Сожжено: {burned_calories} ккал\n"
        f"- Баланс (потреблённые - сожжённые): {net_calories} ккал\n"
    )

    await message.answer(progress_text, parse_mode="HTML")


def setup_handlers(dp):
    dp.include_router(router)
