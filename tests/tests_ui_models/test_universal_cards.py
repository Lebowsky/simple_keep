import json
import unittest
from unittest.mock import MagicMock
from data_for_tests.utils_for_tests import DataCreator

from ui_models import UniversalCardsScreen
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class TestUniversalCardsScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DataCreator()
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings')
        self.sut = UniversalCardsScreen(self.hash_map, self.rs_settings)

        self.service.drop_all_tables()
        self.service.create_tables()

    @unittest.skip
    def test_get_views_data(self):
        self.service.insert_data(*['RS_goods', 'RS_units', 'RS_types_goods'])

        from main import universal_cards_on_start
        universal_cards_on_start(self.hash_map)
        expect = json.loads(self.hash_map['cards'])

        self.sut.table_name = 'RS_goods'
        self.sut.on_start()
        actual = json.loads(self.hash_map['cards'])

        self.assertEqual(expect, actual)
