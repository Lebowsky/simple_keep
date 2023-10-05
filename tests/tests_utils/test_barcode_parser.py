import unittest

from unittest.mock import MagicMock
from ui_utils import BarcodeParser, BarcodeWorker, BarcodeAdrWorker
from ui_barcodes import parse_barcode
from java import jclass

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


class TestBarcodeParser(unittest.TestCase):
    def setUp(self):
        self.sut = BarcodeParser
        self.gs1 = chr(29)
        self.barcodes = [
            '2000000058177',
            '00000046198488X?io+qCABm8wAYa',
            '010460043993125621JgXJ5.T{}8005112000{}93Mdlr'.format(self.gs1, self.gs1),
            ''
        ]

    def test_must_return_ean13_result(self):
        barcode = '2000000058177'

        expect = {'BARCODE': '2000000058177', 'SCHEME': 'EAN13', 'GTIN': '2000000058177'}
        actual = self.sut(barcode=barcode).parse()

        self.assertEqual(expect, actual)

    def test_must_return_unknown_result(self):
        expect = {'SCHEME': 'UNKNOWN'}
        actual = self.sut(barcode='').parse()

        self.assertEqual(expect, actual)

        expect = {'BARCODE': 'fdg54454g', 'GTIN': 'fdg54454g', 'SCHEME': 'UNKNOWN'}
        actual = self.sut(barcode='fdg54454g').parse()

        self.assertEqual(expect, actual)

    @unittest.skip
    def test_must_return_gs1_result(self):
        expect = {
            'BARCODE': '04012922851574EsmtWOcADvofO3q',
            'SCHEME': 'GS1',
            'CHECK': 'fO3q',
            'MRC': 'ADvo',
            'SERIAL': 'EsmtWOc',
            'GTIN': '04012922851574'
        }
        actual = self.sut(barcode='0102000000058436215xgL0BTbeQE&v').parse()
        self.assertEqual(expect, actual)

    def test_tobacco_pack(self):
        expect = {
            'BARCODE': '00000046198488X?io+qCABm8wAYa',
            'SCHEME': 'GS1',
            'CHECK': 'wAYa',
            'MRC': 'ABm8',
            'SERIAL': 'X?io+qC',
            'GTIN': '00000046198488'
        }

        actual = self.sut(barcode='00000046198488X?io+qCABm8wAYa').parse()

        self.assertEqual(expect, actual)

    def test_tobacco_block(self):
        barcode = '010460043993125621JgXJ5.T{}8005112000{}93Mdlr'.format(self.gs1, self.gs1)

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'CHECK': 'Mdlr',
            'NHRN': '112000',
            'SERIAL': 'JgXJ5.T',
            'GTIN': '04600439931256'
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_tobacco_transport_package(self):
        barcode = '011460043993762021NH9X1JF{}1012940183'.format(self.gs1, self.gs1)

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'BATCH': '12940183',
            'SERIAL': 'NH9X1JF',
            'GTIN': '14600439937620'
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_light_industry(self):
        barcode = ('010460780959150821sSBmxTYIFT(eq{}91FFD0{}92testtesttest'
                   .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'SERIAL': 'sSBmxTYIFT(eq',
            'GTIN': '04607809591508',
            'CHECK': 'testtesttest',
            'NHRN': 'FFD0'
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_perfume_and_toilet_water(self):
        barcode = ('010460780959133121e/Fw:xeo47NK2{}91F010{}92Afwuf6d3c9oszbRy/Vb+hRUl1wokz/8UOthdpBYw9A0='
                   .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04607809591331',
            'SERIAL': 'e/Fw:xeo47NK2',
            'NHRN': 'F010',
            'CHECK': 'Afwuf6d3c9oszbRy/Vb+hRUl1wokz/8UOthdpBYw9A0='
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_shoes(self):
        barcode = ('010406047769798721QkmvHY.+O5crD{}918097{}92Za6ZlkdG3zynfnllYpMQSrbZ7Gu+OKqJ9fCRZu+X5A7V7D7Th7ROcrRPbmLHpqV2BLI0YWuUTPYKadnk40Zjqw=='
                   .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04060477697987',
            'SERIAL': 'QkmvHY.+O5crD',
            'NHRN': '8097',
            'CHECK': 'Za6ZlkdG3zynfnllYpMQSrbZ7Gu+OKqJ9fCRZu+X5A7V7D7Th7ROcrRPbmLHpqV2BLI0YWuUTPYKadnk40Zjqw=='
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    @unittest.skip
    def test_fur_coats(self):
        barcode = ('RU-430301-AAA0020659'.format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'SERIAL': 'AAA0020659',
            'TNWED_CODE': '4303',
            'INPUT_METHOD': '01',
            'COUNTRY_CODE': 'RU',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_photo(self):
        barcode = (
            '010460780959145421m9tNPzJTWzuc9exC5/M+{}91EE07{}92vdIdf340vdN01ot+7YRyUb0XRbSQEAe4C4wjaAysm4M='
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04607809591454',
            'SERIAL': 'm9tNPzJTWzuc9exC5/M+',
            'NHRN': 'EE07',
            'CHECK': 'vdIdf340vdN01ot+7YRyUb0XRbSQEAe4C4wjaAysm4M='
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_tires(self):
        barcode = (
            '0104607809591423215MGWI6OyoG3Jt{}91F010{}92xodkJv/PmhAHaiZBDNK8Kj83G4L4uPwDCoapvr28joY='
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04607809591423',
            'SERIAL': '5MGWI6OyoG3Jt',
            'NHRN': 'F010',
            'CHECK': 'xodkJv/PmhAHaiZBDNK8Kj83G4L4uPwDCoapvr28joY='
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_medicines(self):
        barcode = (
            '010460714356059821FGXEAGA5A1GAH{}91EE06{}92VW/n3g0hYP6kqx1WjVy/fnpKT+i7N3FT8QPUyzzKQT4='
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04607143560598',
            'SERIAL': 'FGXEAGA5A1GAH',
            'NHRN': 'EE06',
            'CHECK': 'VW/n3g0hYP6kqx1WjVy/fnpKT+i7N3FT8QPUyzzKQT4='
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_dairy_products(self):
        barcode = (
            '0103041094787443215Qbag!{}93Zjqw'
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '03041094787443',
            'SERIAL': '5Qbag!',
            'CHECK': 'Zjqw'
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_dairy_products_with_weight(self):
        barcode = (
            '0103041094787443215Qbag!{}93Zjqw{}3103000353'
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '03041094787443',
            'SERIAL': '5Qbag!',
            'CHECK': 'Zjqw',
            'WEIGHT': '000353'
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_packaged_water(self):
        barcode = (
            '010463633245536021561BtxPs9VbAP{}93dGVz'
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04636332455360',
            'SERIAL': '561BtxPs9VbAP',
            'CHECK': 'dGVz',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_bioadditives(self):
        barcode = (
            '0104260071832047215DKwJEavSWpj5{}93dGVzv'
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04260071832047',
            'SERIAL': '5DKwJEavSWpj5',
            'CHECK': 'dGVz',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_beer(self):
        barcode = (
            '0104636332455339215qa5?WHJssbI-{}93dGVz'
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04636332455339',
            'SERIAL': '5qa5?WHJssbI-',
            'CHECK': 'dGVz',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_antiseptics(self):
        barcode = (
            '0105015025322223215pE?s!Cbc0_MJ{}93dGVz'
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '05015025322223',
            'SERIAL': '5pE?s!Cbc0_MJ',
            'CHECK': 'dGVz',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_bicycles(self):
        barcode = (
            '0104640088090997215tjNZHkB"<jQY{}91FFD0{}92dGVzdGgUDZKISuwvUUiqzzWuUNnBVJhvRbOxG2W2Tg8='
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04640088090997',
            'NHRN':  'FFD0',
            'SERIAL': '5tjNZHkB"<jQY',
            'CHECK': 'dGVzdGgUDZKISuwvUUiqzzWuUNnBVJhvRbOxG2W2Tg8=',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_wheelchairs(self):
        barcode = (
            '0104640088091000215gMpn5CJG37mF{}91FFD0{}92dGVzdOvwCHl95aQdMlRHin6E0crdgMSvg18oBi/wagQ='
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04640088091000',
            'NHRN': 'FFD0',
            'SERIAL': '5gMpn5CJG37mF',
            'CHECK': 'dGVzdOvwCHl95aQdMlRHin6E0crdgMSvg18oBi/wagQ=',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)

    def test_canned_food(self):
        barcode = (
            '0104809011017511215abcde{}91A123{}92Test1234Test5678Test1234Test5678Test1234Test'
            .format(self.gs1, self.gs1))

        expect = {
            'BARCODE': barcode,
            'SCHEME': 'GS1',
            'GTIN': '04809011017511',
            'NHRN': 'A123',
            'SERIAL': '5abcde',
            'CHECK': 'Test1234Test5678Test1234Test5678Test1234Test',
        }

        actual = self.sut(barcode=barcode).parse()
        self.assertEqual(expect, actual)


class TestBarcodeWorker(unittest.TestCase):
    def setUp(self) -> None:
        rs_settings.put("path_to_databases", "./", True)
        self.barcode_data = {
            'id_good': 'baf54db7-7029-11e6-accf-0050568b35ac',
            'id_property': 'c3d2a493-7026-11e6-accf-0050568b35ac',
            'id_series': 'c3d2a493-7026-11e6-accf-0050568b35ac',
            'id_unit': 'c3d2a493-7026-11e6-accf-0050568b35ac',
            'ratio': 10,
            'approved': '0',
            'mark_id': '',
            'use_mark': False,
            'row_key': '',
            'use_series': '0',
            'qtty': 1,
            'd_qtty': 1,
            'qtty_plan': 5,
            'price': 0,
            'id_price': '',
        }

    def tearDown(self) -> None:
        pass

    def test_getting_error_empty_barcode_data(self):
        barcode = '2000000025988'
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        sut = BarcodeWorker(id_doc)
        sut._get_barcode_data = MagicMock(return_value={})

        result = sut.process_the_barcode(barcode)
        self.assertEqual(result.error, 'Not found')
    
    def test_getting_error_invalid_barcode(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000'

        sut = BarcodeWorker(id_doc)
        parser = BarcodeParser(barcode)
        barcode_info = parser.BarcodeInfo(error='error')
        BarcodeParser.parse = MagicMock(return_value=barcode_info)
        sut._get_barcode_data = MagicMock(return_value={})

        result = sut.process_the_barcode(barcode)

        self.assertTrue(type(result), BarcodeWorker.ProcessTheBarcodeResult)
        self.assertTrue(result.error, 'Invalid barcode')

    def test_getting_error_not_valid_barcode_if_use_mark_but_scan_ean13(self):
        """ not_valid_barcode """
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        self.barcode_data.update(use_mark=True)

        sut = BarcodeWorker(id_doc)
        rs_settings.put("use_mark", "true", True)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'Not valid barcode')
    
    def test_getting_error_zero_plan_error_if_have_zero_plan_and_control(self):
        """ zero_plan_error """
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        sut = BarcodeWorker(id_doc, have_zero_plan=True, control=True)
        rs_settings.put("use_mark", "false", False)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'Zero plan error')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)
    
    def test_can_add_qty_by_barcode(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        sut = BarcodeWorker(id_doc)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertFalse(result.error)
        self.assertTrue(sut.docs_table_update_data)
        self.assertEqual(sut.docs_table_update_data['d_qtty'], 11)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.mark_update_data)

    def test_can_add_qty_by_barcode_use_queue(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        sut = BarcodeWorker(id_doc, use_scanning_queue=True)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertFalse(result.error)
        self.assertTrue(sut.queue_update_data)
        self.assertEqual(sut.queue_update_data['d_qtty'], 10)
        self.assertTrue(sut.docs_table_update_data)
        self.assertFalse(sut.mark_update_data)
    
    def test_can_add_mark_in_document(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '00000046198488X?io+qCABm8wAYa'

        self.barcode_data.update(use_mark=True)

        sut = BarcodeWorker(id_doc)
        rs_settings.put("use_mark", "true", True)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertFalse(result.error)
        self.assertTrue(sut.mark_update_data)
        self.assertTrue(result.description, 'Марка добавлена в документ')
        self.assertFalse(sut.queue_update_data)
        self.assertTrue(sut.docs_table_update_data)
        self.assertEqual(sut.docs_table_update_data['d_qtty'], 11)
        self.assertEqual(sut.mark_update_data['approved'], '1')

    def test_can_set_approved_mark(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '00000046198488X?io+qCABm8wAYa'

        self.barcode_data.update(use_mark=True, mark_id='mark_id_value')

        sut = BarcodeWorker(id_doc)
        rs_settings.put("use_mark", "true", True)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)
        sut.update_document_barcode_data = MagicMock()

        result = sut.process_the_barcode(barcode)

        self.assertFalse(result.error)
        self.assertTrue(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertTrue(sut.docs_table_update_data)
        self.assertEqual(sut.docs_table_update_data['d_qtty'], 11)
        self.assertEqual(sut.mark_update_data['approved'], '1')
        sut.update_document_barcode_data.assert_called_once()
    
    def test_cant_add_already_mark(self):
        """ mark_already_scanned """
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '00000046198488X?io+qCABm8wAYa'

        self.barcode_data.update(use_mark=True, mark_id='mark_id_value', row_key='1', approved='1')

        sut = BarcodeWorker(id_doc)
        rs_settings.put("use_mark", "true", True)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)
        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'Already scanned')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)

    def test_cant_add_new_mark_if_have_mark_plan_and_control(self):
        """ mark_not_found """
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '00000046198488X?io+qCABm8wAYa'

        self.barcode_data.update(use_mark=True, row_key='1')

        sut = BarcodeWorker(id_doc, have_mark_plan=True, control=True)
        rs_settings.put("use_mark", "true", True)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'Not found')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)

    def test_cant_add_reached_plan_barcode(self):
        """ quantity_plan_reached """
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        self.barcode_data.update(use_mark=True, row_key=1)

        sut = BarcodeWorker(id_doc, have_qtty_plan=True, control=True)
        rs_settings.put("use_mark", "false", False)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'Quantity plan reached')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)

    def test_cant_use_process_barcode_if_use_series(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        self.barcode_data.update(use_mark=True, use_series='1')

        sut = BarcodeWorker(id_doc)

        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'use_series')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)

class TestAdrBarcodeWorker(unittest.TestCase):
    def setUp(self) -> None:
        rs_settings.put("path_to_databases", "./", True)
        self.barcode_data = {
            'id_good': 'baf54db7-7029-11e6-accf-0050568b35ac',
            'id_property': 'c3d2a493-7026-11e6-accf-0050568b35ac',
            'id_series': 'c3d2a493-7026-11e6-accf-0050568b35ac',
            'id_unit': 'c3d2a493-7026-11e6-accf-0050568b35ac',
            'ratio': 10,
            'approved': '0',
            'mark_id': '',
            'use_mark': False,
            'row_key': '',
            'use_series': '0',
            'qtty': 1,
            'd_qtty': 1,
            'qtty_plan': 5,
            'price': 0,
            'id_price': '',
        }

    def test_getting_error_zero_plan_error_if_have_zero_plan_and_control(self):
        """ zero_plan_error """
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        self.barcode_data.update(use_mark=True)

        sut = BarcodeAdrWorker(id_doc, have_zero_plan=True, control=True)
        rs_settings.put("use_mark", "false", False)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'Zero plan error')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)

    def test_can_add_qty_by_barcode(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        self.barcode_data['row_key'] = 1

        sut = BarcodeAdrWorker(id_doc)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertFalse(result.error)
        self.assertTrue(sut.docs_table_update_data)
        self.assertEqual(sut.docs_table_update_data['qtty'], 11)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.mark_update_data)

    def test_cant_add_reached_plan_barcode(self):
        """ quantity_plan_reached """
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        self.barcode_data.update(use_mark=True, row_key='1')

        sut = BarcodeAdrWorker(id_doc, have_qtty_plan=True, control=True)
        rs_settings.put("use_mark", "false", False)
        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'Quantity plan reached')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)

    def test_cant_use_process_barcode_if_use_series(self):
        id_doc = '96e94835-f8a0-11ed-a290-8babe363837e'
        barcode = '2000000025988'

        self.barcode_data.update(use_mark=True, use_series='1')

        sut = BarcodeAdrWorker(id_doc)

        sut._get_barcode_data = MagicMock(return_value=self.barcode_data)

        result = sut.process_the_barcode(barcode)

        self.assertTrue(result.error, 'use_series')
        self.assertFalse(sut.mark_update_data)
        self.assertFalse(sut.queue_update_data)
        self.assertFalse(sut.docs_table_update_data)
