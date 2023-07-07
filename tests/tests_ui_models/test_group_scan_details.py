import unittest
from unittest.mock import MagicMock

from ui_models import GroupScanDocDetailsScreen
from ui_utils import HashMap
from main import noClass
from hs_services import HsService

from data_for_tests.utils_for_tests import hashMap


class TestGroupScanDocDetailsScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = GroupScanDocDetailsScreen(self.hash_map, self.rs_settings)

    def test_can_call_communication_and_return_true(self):
        answer = HsService.HttpAnswer(
            error=False,
            error_text='',
            status_code=200,
            url='')

        HsService.communication_test = MagicMock(return_value=answer)
        self.sut.hs_service.http_answer = answer
        res = self.sut._check_connection()
        self.assertTrue(res)
        HsService.communication_test.assert_called_once_with(timeout=1)

    def test_can_call_communication_and_return_false(self):
        answer = HsService.HttpAnswer(
            error=True,
            error_text='',
            status_code=404,
            url='')

        HsService.communication_test = MagicMock(return_value=answer)
        self.sut.hs_service.http_answer = answer
        res = self.sut._check_connection()
        self.assertFalse(res)
        HsService.communication_test.assert_called_once_with(timeout=1)


        HsService.communication_test = MagicMock(side_effect=Exception('err'))
        with self.assertRaises(Exception) as context:
            res = self.sut._check_connection()

            self.assertEqual('err', context)

        self.assertFalse(res)






