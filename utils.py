import requests
from config import API_KEY_TRAIN

def get_current_temperature(city: str, api_key_current: str) -> dict[str, str]:
    """
    Получение текущей температуры для города через API OpenWeatherMap.

    Args:
        city (str): Название города.
        api_key_current (str): API ключ для доступа к OpenWeatherMap.

    Returns:
        float: Температура в градусах Цельсия, если запрос успешен.
        dict: Словарь с ключом "error", если произошла ошибка.
    """
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key_current,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 401:
            return {
                "cod": "401",
                "message": (
                    "Invalid API key. Please see "
                    "https://openweathermap.org/faq#error401 for more info."
                )
            }

        if response.status_code == 200:
            return data['main']['temp']

    except Exception as e:
        return {"error": str(e)}

    return {"error": "Unexpected error occurred."}


def calc_daily_water(weight_kg: float, activity_minutes: int, temperature: float) -> float:
    """
    Рассчитывает дневную норму воды в мл. на основе веса,
    уровня активности и температуры.

    Формула:
        1) Базовая норма: вес (в кг) * 30 мл/кг.
        2) Дополнительно +500 мл за каждые полные 30 минут активности.
        3) Увеличение нормы в зависимости от температуры:
            - Если t <= 25°C - 0 мл.
            - Если 25°C < t <= 30°C:
              500 мл + 100 мл за каждый градус выше 25°C.
            - Если температура > 30°C - 1000 мл.

    Args:
        weight_kg (float): Вес человека в кг.
        activity_minutes (int): Длительность активности в мин.
        temperature (float): Температура в °C.

    Returns:
        float: Рекомендуемое количество воды в мл.
    """
    water = weight_kg * 30
    water += (activity_minutes // 30) * 500

    if 25 < temperature <= 30:
        temp_coefficient = 500 + (temperature - 25) * 100
        water += temp_coefficient
    elif temperature > 30:
        water += 1000

    return water


def calc_daily_calories(weight_kg: float, height_cm: float, age: int, activity_minutes: int, activity_level: str, gender: str) -> float:
    """
    Рассчитывает дневную норму калорий на текущий день с учётом известной активности и пола.

    Формула:
        1) Базовая норма:
           - Для мужчин: BMR = 10 * Вес (кг) + 6.25 * Рост (см) - 5 * Возраст + 5.
           - Для женщин: BMR = 10 * Вес (кг) + 6.25 * Рост (см) - 5 * Возраст - 161.
        2) Калории за физическую активность:
           - 'light': +4 ккал за минуту.
           - 'moderate': +8 ккал за минуту.
           - 'high': +12 ккал за минуту.

    Args:
        weight_kg (float): Вес.
        height_cm (float): Рост.
        age (int): Возраст.
        activity_minutes (int): Количество минут физической активности в день.
        activity_level (str): Уровень активности ('light', 'middle', 'high').
        gender (str): Пол пользователя ('male' или 'female').

    Возвращает:
        float: Рекомендуемое количество калорий в день.
    """
    if gender.lower() == "male":
        base_calories = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    elif gender.lower() == "female":
        base_calories = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_calories_per_minute = {
        "light": 4,  # Лёгкая активность
        "middle": 8,  # Умеренная активность
        "high": 12  # Высокая активность
    }

    calories_per_minute = activity_calories_per_minute.get(activity_level.lower())
    if calories_per_minute is None:
        raise ValueError("Уровень активности должен быть 'light', 'middle' или 'high'.")

    activity_calories = activity_minutes * calories_per_minute

    total_calories = base_calories + activity_calories
    return total_calories


def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:
            first_product = products[0]
            return {
                'name': first_product.get('product_name'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g')
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None


def get_calories_burned_ninjas(activity: str, user_time_min: int, user_weight_kg: float) -> float:
    """
    Запрос в API Ninjas по названию активности (англ.).
    """
    url = "https://api.api-ninjas.com/v1/caloriesburned"
    headers = {"X-Api-Key": API_KEY_TRAIN}
    params = {"activity": activity}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or not isinstance(data, list) or len(data) == 0:
            return 0.0

        item = data[0]
        cph = item.get("calories_per_hour", 0)
        if cph <= 0:
            return 0.0

        # Преобразуем вес в фунты
        user_weight_lbs = user_weight_kg * 2.2

        # Расход для данного веса
        burned = (user_weight_lbs / 160.0) * (user_time_min / 60.0) * cph
        return burned

    except Exception as e:
        print(f"Ошибка при запросе к API Ninjas: {e}")
        return 0.0
