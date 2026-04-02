import os
import requests
from models import BarboraVivinoWine

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_API = "https://api.telegram.org/bot" + TELEGRAM_TOKEN


def send_message(chat_id, text: str):
    requests.get(f"{TELEGRAM_API}/sendMessage", params={
        "chat_id": chat_id,
        "text": text,
    })


def send_wine(chat_id, wine: BarboraVivinoWine):
    title = wine.barbora_wine.title
    image = wine.barbora_wine.image
    price = wine.barbora_wine.price
    rate = wine.vivino_wines[0].rate
    verified = wine.verified
    vivino_links = ''.join(
        f'<a href="https:{v.image}">{v.name}</a>\n'
        for v in wine.vivino_wines
    )
    caption = (
        f'{title}\n'
        f'Price: <strong>{price}\n</strong>'
        f'Rate: <b>{rate}\n</b>'
        f'<em>Verified: {verified}\n\n</em>'
        f'Vivino matched photo:\n{vivino_links}'
    )
    requests.get(f"{TELEGRAM_API}/sendPhoto", params={
        "chat_id": chat_id,
        "photo": image,
        "caption": caption,
        "parse_mode": "HTML",
    })
