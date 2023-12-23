import json
from datetime import datetime
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


def check_time(time_to_check, AMPM, opening_hours, closing_hours):
    if AMPM is not None:
        if ':' in time_to_check:
            time_format = '%I:%M %p'
        else:
            time_format = '%I %p'
        try:
            time_to_check = datetime.strptime(time_to_check + ' ' + AMPM, time_format).strftime('%H:%M')
        except ValueError:
            return False

    opening_hours = datetime.strptime(str(opening_hours), '%H').time()
    closing_hours = datetime.strptime(str(closing_hours), '%H').time()

    try:
        time_to_check = datetime.strptime(time_to_check, '%H:%M').time()
    except ValueError:
        return False

    if opening_hours <= time_to_check <= closing_hours:
        return True
    else:
        return False


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Hello World!")

        return []


class ActionShowOpenHours(Action):

    def name(self) -> Text:
        return "show_open_hours"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        with open("data\\opening_hours.json", 'r') as opening_hours_file:
            opening_hours_data = json.load(opening_hours_file)

        data = opening_hours_data.get("items")

        response = "Here are our current operating hours:\n\n"
        for day, hour in data.items():
            response += f"{day} from {hour['open']} till {hour['close']}\n"

        dispatcher.utter_message(text=response)

        return []


class ActionShowOpeningHoursOnParticularDay(Action):
    def name(self) -> Text:
        return "show_opening_hours_on_particular_day"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        with open("data\\opening_hours.json", 'r') as opening_hours_file:
            opening_hours_data = json.load(opening_hours_file)

        data = opening_hours_data.get("items")

        day = next(tracker.get_latest_entity_values("day"), None)
        hour = next(tracker.get_latest_entity_values("hour"), None)
        time_ampm = next(tracker.get_latest_entity_values("time"), None)

        if day is not None and day in data:
            is_open = check_time(hour, time_ampm, data[day]['open'], data[day]['close'])
            if is_open:
                dispatcher.utter_message(text="We are open at this time.")
            else:
                dispatcher.utter_message(text="We are closed at this time.")
        else:
            dispatcher.utter_message(text="I didn't understand your hour format, please provide it in HH:MM AM/PM")

        return []


class ActionListMenu(Action):
    def name(self) -> Text:
        return "action_list_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        with open("data\\menu.json", 'r') as menu_file:
            menu_file_data = json.load(menu_file)

        print(menu_file_data)
        data = menu_file_data.get('items', [])

        response = "Here are our menu:\n\n"
        print(data)

        for meal in data:
            response += f"{meal.get('name')} price: {meal.get('price')}. We need approximately {meal.get('preparation_time')} hours to prepare this dish.\n"

        dispatcher.utter_message(text=response)

        return []


class ActionOrderFood(Action):
    def name(self) -> Text:
        return "action_order_food"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        with open("data\\menu.json", 'r') as menu_file:
            menu_file_data = json.load(menu_file)

        ordered_meal = next(tracker.get_latest_entity_values("food"), None)
        amount = next(tracker.get_latest_entity_values("amount"), None)
        additional_request = next(tracker.get_latest_entity_values("additional_request"), None)
        data = menu_file_data.get('items', [])

        for meal in data:
            if meal.get('name').lower() == ordered_meal.lower():
                response = "I confirm your order for " + (str(amount) + " " if amount is not None else "") + meal.get(
                    'name').lower() + (" " + str(additional_request) if additional_request is not None else "")
                preparation_time = meal.get('preparation_time')
                response += ". We need approximately " + str(
                    preparation_time) + " hours to prepare a meal for you. I'll notify you when the order will be ready!"
                dispatcher.utter_message(text=response)

                return []

        dispatcher.utter_message(text="We will try to prepare this meal for you in 1 hour. I'll notify you when the "
                                      "order will be ready!")

        return []
