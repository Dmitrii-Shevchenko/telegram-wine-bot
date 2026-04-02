import json
from wine_service import get_list_of_wines, get_top_rated_wines
from telegram_client import send_message, send_wine

MAX_WINES = 20
VALID_WINE_TYPES = ['red', 'white', 'rose']


def process_event(event):
    message = json.loads(event['body'])
    chat_id = message['message']['chat']['id']
    text = message['message']['text']

    send_message(chat_id, "Processing may take a few minutes...")

    try:
        args = text.split(' ')
        wine_type = args[0].lower()
        count = int(args[1])
    except:
        send_message(chat_id, "Wrong input. There are only 3 options: red, white, rose. Example: 'White 5'")
        return

    if wine_type not in VALID_WINE_TYPES:
        send_message(chat_id, "Wrong input. There are only 3 options: red, white, rose. Example: 'White 5'")
        return

    if count > MAX_WINES:
        send_message(chat_id, f"Output limit is {MAX_WINES} wines.")
        return

    try:
        wines = get_list_of_wines(f'{wine_type}_wines')
        top_wines = get_top_rated_wines(wines, count)
        for wine in top_wines:
            send_wine(chat_id, wine)
    except:
        send_message(chat_id, "Something goes wrong :(")


def lambda_handler(event, context):
    process_event(event)
    return {'statusCode': 200}
