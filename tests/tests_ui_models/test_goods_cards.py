import unittest
from unittest.mock import MagicMock

from ui_models import GoodsListScreen
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class TestModelGoodsListScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = GoodsListScreen(self.hash_map, self.rs_settings)

    def test_on_back_pressed_must_set_hash_map_value_BackScreen(self):
        # init test data
        self.sut.listener = 'ON_BACK_PRESSED'

        # execute test method
        self.sut.on_input()
        actual = self.hash_map.containsKey('FinishProcess')

        # assert test method results
        self.assertTrue(actual)

    def test_on_select_type_good_hash_map_value_ShowScreen(self):

        expect = 'Выбор категории товаров'

        # init test data
        self.sut.listener = 'select_goods_type'

        # execute test method
        self.sut.on_input()

        # init test data
        actual = self.hash_map['ShowScreen']

        # assert test method results
        self.assertEqual(expect, actual)

    def test_on_cards_click_hash_map_values_selected_card(self):
        # init test data
        self.sut.listener = 'CardsClick'
        selected_card_data = {
            'key': 'key_id_123',
            'code': 'code_123',
            'name': 'name_123',
            'art': 'art_123',
            'unit': 'unit_123',
            'type_good': 'type_good_123',
            'description': 'description_123'
        }
        self.sut.hash_map.put("selected_card_data", selected_card_data, to_json=True)
        expect = 'key_id_123'

        # execute test method
        self.sut.on_input()
        taken_card_data = self.hash_map.get('selected_card_data', from_json=True)
        actual = taken_card_data['key']

        # assert test method results
        self.assertEqual(expect, actual)

    #TODO Олег: Тест ввод баркода

