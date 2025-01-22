from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity_minutes = State()
    city = State()
    calorie_goal = State()
    gender = State()
    activity_level = State()


class FoodLogStates(StatesGroup):
    waiting_for_grams = State()
