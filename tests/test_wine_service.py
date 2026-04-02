import json
import os
import sys
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import BarboraVivinoWine, BarboraWine, VivinoWine
from wine_service import get_list_of_wines, get_top_rated_wines

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def load_json(wine_type: str):
    with open(os.path.join(DATA_DIR, wine_type + '_wines.json')) as f:
        return json.load(f)


def make_mock_s3(raw_data: list):
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {
        'Body': BytesIO(json.dumps(raw_data).encode('utf-8'))
    }
    return mock_s3


def make_wine(rate: float, status: str = 'active', vivino_count: int = 1) -> BarboraVivinoWine:
    barbora = BarboraWine(
        id='1', title='Test Wine', brand_name='Brand',
        price=10.0, url='url', category_path_url='cat',
        image='img.png', status=status
    )
    vivino_wines = [
        VivinoWine(id=str(i), name=f'Vivino {i}', rate=rate,
                   grapes=None, alcohol=12.0, image='img.jpg')
        for i in range(vivino_count)
    ]
    return BarboraVivinoWine(barbora, vivino_wines)


# ---------------------------------------------------------------------------
# get_list_of_wines
# ---------------------------------------------------------------------------

class TestGetListOfWines(unittest.TestCase):

    @patch('wine_service.boto3')
    def test_returns_all_wines(self, mock_boto3):
        raw = load_json('rose')
        mock_boto3.client.return_value = make_mock_s3(raw)
        wines = get_list_of_wines('rose_wines')
        self.assertEqual(len(wines), len(raw))

    @patch('wine_service.boto3')
    def test_barbora_fields_mapped_correctly(self, mock_boto3):
        raw = load_json('rose')
        mock_boto3.client.return_value = make_mock_s3(raw)
        wines = get_list_of_wines('rose_wines')

        first = wines[0]
        raw_b = raw[0]['barbora_wine']
        self.assertEqual(first.barbora_wine.id, raw_b['id'])
        self.assertEqual(first.barbora_wine.title, raw_b['title'])
        self.assertEqual(first.barbora_wine.price, raw_b['price'])
        self.assertEqual(first.barbora_wine.status, raw_b['status'])
        self.assertEqual(first.barbora_wine.image, raw_b['image'])

    @patch('wine_service.boto3')
    def test_vivino_fields_mapped_correctly(self, mock_boto3):
        raw = load_json('rose')
        mock_boto3.client.return_value = make_mock_s3(raw)
        wines = get_list_of_wines('rose_wines')

        first = wines[0]
        raw_v = [v for v in raw[0]['vivino_wines'] if v is not None]
        self.assertEqual(len(first.vivino_wines), len(raw_v))
        self.assertEqual(first.vivino_wines[0].rate, raw_v[0]['rate'])
        self.assertEqual(first.vivino_wines[0].name, raw_v[0]['name'])

    @patch('wine_service.boto3')
    def test_verified_flag_mapped(self, mock_boto3):
        raw = load_json('rose')
        mock_boto3.client.return_value = make_mock_s3(raw)
        wines = get_list_of_wines('rose_wines')
        for wine, raw_wine in zip(wines, raw):
            self.assertEqual(wine.verified, raw_wine['verified'])

    @patch('wine_service.boto3')
    def test_null_vivino_entries_skipped(self, mock_boto3):
        raw = load_json('rose')
        mock_boto3.client.return_value = make_mock_s3(raw)
        wines = get_list_of_wines('rose_wines')
        for wine in wines:
            self.assertTrue(all(v is not None for v in wine.vivino_wines))

    @patch('wine_service.boto3')
    def test_s3_called_with_correct_params(self, mock_boto3):
        raw = load_json('rose')
        mock_s3 = make_mock_s3(raw)
        mock_boto3.client.return_value = mock_s3
        get_list_of_wines('rose_wines')
        mock_s3.get_object.assert_called_once_with(Bucket='winebot', Key='rose_wines.json')

    @patch('wine_service.boto3')
    def test_all_wine_types_load(self, mock_boto3):
        for wine_type in ['red', 'white', 'rose']:
            raw = load_json(wine_type)
            mock_boto3.client.return_value = make_mock_s3(raw)
            wines = get_list_of_wines(f'{wine_type}_wines')
            self.assertGreater(len(wines), 0)


# ---------------------------------------------------------------------------
# get_top_rated_wines
# ---------------------------------------------------------------------------

class TestGetTopRatedWines(unittest.TestCase):

    def test_returns_correct_count(self):
        wines = [make_wine(rate) for rate in [3.5, 4.2, 4.5, 3.8]]
        self.assertEqual(len(get_top_rated_wines(wines, 2)), 2)

    def test_sorted_by_rating_descending(self):
        wines = [make_wine(rate) for rate in [3.5, 4.2, 4.5, 3.8]]
        result = get_top_rated_wines(wines, 4)
        rates = [w.vivino_wines[0].rate for w in result]
        self.assertEqual(rates, sorted(rates, reverse=True))

    def test_filters_inactive_wines(self):
        wines = [make_wine(4.5, status='inactive'), make_wine(4.2, status='active')]
        result = get_top_rated_wines(wines, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].vivino_wines[0].rate, 4.2)

    def test_filters_wines_without_vivino_match(self):
        wine_no_vivino = make_wine(4.5)
        wine_no_vivino.vivino_wines = []
        wine_with_vivino = make_wine(4.2)
        result = get_top_rated_wines([wine_no_vivino, wine_with_vivino], 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].vivino_wines[0].rate, 4.2)

    def test_count_larger_than_available_returns_all(self):
        wines = [make_wine(rate) for rate in [4.5, 4.2]]
        self.assertEqual(len(get_top_rated_wines(wines, 10)), 2)

    def test_empty_input_returns_empty(self):
        self.assertEqual(get_top_rated_wines([], 5), [])

    def test_all_inactive_returns_empty(self):
        wines = [make_wine(4.5, status='inactive'), make_wine(4.2, status='inactive')]
        self.assertEqual(get_top_rated_wines(wines, 2), [])

    def test_count_zero_returns_empty(self):
        wines = [make_wine(rate) for rate in [4.5, 4.2]]
        self.assertEqual(get_top_rated_wines(wines, 0), [])

    def test_wine_with_multiple_vivino_matches_uses_first_rate(self):
        wine = make_wine(rate=4.8, vivino_count=3)
        wine.vivino_wines[0].rate = 4.8
        wine.vivino_wines[1].rate = 3.5
        wine.vivino_wines[2].rate = 2.0
        result = get_top_rated_wines([wine], 1)
        self.assertEqual(result[0].vivino_wines[0].rate, 4.8)


# ---------------------------------------------------------------------------
# get_top_rated_wines with real JSON data
# ---------------------------------------------------------------------------

class TestGetTopRatedWinesRealData(unittest.TestCase):

    @patch('wine_service.boto3')
    def _load(self, wine_type, mock_boto3):
        raw = load_json(wine_type)
        mock_boto3.client.return_value = make_mock_s3(raw)
        return get_list_of_wines(f'{wine_type}_wines')

    def test_results_are_sorted_by_rate(self):
        for wine_type in ['red', 'white', 'rose']:
            wines = self._load(wine_type)
            result = get_top_rated_wines(wines, 10)
            rates = [w.vivino_wines[0].rate for w in result]
            self.assertEqual(rates, sorted(rates, reverse=True), f'Failed for {wine_type}')

    def test_results_are_all_active(self):
        for wine_type in ['red', 'white', 'rose']:
            wines = self._load(wine_type)
            result = get_top_rated_wines(wines, 10)
            for wine in result:
                self.assertEqual(wine.barbora_wine.status, 'active', f'Failed for {wine_type}')

    def test_results_all_have_vivino_match(self):
        for wine_type in ['red', 'white', 'rose']:
            wines = self._load(wine_type)
            result = get_top_rated_wines(wines, 10)
            for wine in result:
                self.assertGreater(len(wine.vivino_wines), 0, f'Failed for {wine_type}')


if __name__ == '__main__':
    unittest.main()
