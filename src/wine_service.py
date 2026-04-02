import json
import boto3
from models import BarboraWine, VivinoWine, BarboraVivinoWine


def get_list_of_wines(file_name: str) -> list[BarboraVivinoWine]:
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='winebot', Key=file_name + '.json')
    bw_wines_json = json.loads(response['Body'].read().decode('utf-8'))

    result = []
    for bw_wine in bw_wines_json:
        barbora_wine = BarboraWine(
            bw_wine['barbora_wine']['id'],
            bw_wine['barbora_wine']['title'],
            bw_wine['barbora_wine']['brand_name'],
            bw_wine['barbora_wine']['price'],
            bw_wine['barbora_wine']['url'],
            bw_wine['barbora_wine']['category_path_url'],
            bw_wine['barbora_wine']['image'],
            bw_wine['barbora_wine']['status']
        )

        vivino_wines = [
            VivinoWine(
                v['id'], v['name'], v['rate'],
                v['grapes'], v['alcohol'], v['image']
            )
            for v in bw_wine['vivino_wines'] if v is not None
        ]

        result.append(BarboraVivinoWine(barbora_wine, vivino_wines, bw_wine['verified']))

    return result


def get_top_rated_wines(wines: list[BarboraVivinoWine], count: int) -> list[BarboraVivinoWine]:
    wines_with_ratings = [w for w in wines if len(w.vivino_wines) > 0]
    sorted_wines = sorted(wines_with_ratings, key=lambda x: x.vivino_wines[0].rate, reverse=True)
    active_wines = [w for w in sorted_wines if w.barbora_wine.status == 'active']
    return active_wines[:count]
