import sm_adr_docs
from java import jclass
from printing_factory import PrintService
from ru.travelfood.simple_ui import SimpleUtilites as suClass

from ui_utils import HashMap
import ui_models
from ui_models import create_screen

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


# =============== Main events =================


@HashMap()
def app_on_start(hash_map: HashMap):
    """ Обработчик при старте приложения """

    model = ui_models.MainEvents(hash_map)
    model.app_on_start()


@HashMap()
def timer_update(hash_map: HashMap):
    """ Обработчик для фонового обмена """

    timer = ui_models.Timer(hash_map)
    timer.timer_on_start()


@HashMap()
def event_service(hash_map):
    """ Обработчик для работы МП в режиме сервера.
     В ws_body по умолчанию лежит текст конфигурации """

    ui_models.WebServiceSyncCommand(hash_map).on_service_request()



@HashMap()
def on_sql_error(hash_map):
    model = ui_models.MainEvents(hash_map)
    model.on_sql_error()


@HashMap()
def on_close_app(hash_map):
    # Попытка очистки кэша при выходе с приложения
    suClass.deleteCache()


# ^^^^^^^^^^^^^^^^^ Main events ^^^^^^^^^^^^^^^^^


# =============== Documents =================
@HashMap()
def flow_docs_on_start(hash_map: HashMap):
    """Отдельные обработчики плиток для определения процесса hash_map'ом"""
    screen = ui_models.FlowDocScreen(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def flow_docs_on_select(hash_map: HashMap):
    """Отдельные обработчики плиток для определения процесса hash_map'ом"""
    screen = ui_models.FlowDocScreen(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def flow_tiles_on_start(hash_map: HashMap):
    """Отдельные обработчики плиток для определения процесса hash_map'ом"""
    screen = ui_models.FlowTilesScreen(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def flow_tiles_on_select(hash_map: HashMap):
    """Отдельные обработчики плиток для определения процесса hash_map'ом"""
    screen = ui_models.FlowTilesScreen(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def barcode_flow_on_start(hash_map: HashMap):
    """Процесс: Сбор ШК. Экран: ПотокШтрихкодовДокумента"""
    screen = ui_models.FlowDocDetailsScreen(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def barcode_flow_listener(hash_map: HashMap):
    """Процесс: Сбор ШК. Экран: ПотокШтрихкодовДокумента"""
    screen = ui_models.FlowDocDetailsScreen(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def article_cv_on_object_detected(hash_map: HashMap):
    """Процесс: Распознавание артикулов. Шаг: Новый шаг ActiveCV."""
    screen = ui_models.ActiveCVArticleRecognition(hash_map, rs_settings)
    screen.on_object_detected()


@HashMap()
def article_cv_on_input(hash_map: HashMap):
    """Процесс: Распознавание артикулов. Шаг: Новый шаг ActiveCV."""
    screen = ui_models.ActiveCVArticleRecognition(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def article_cv_on_start(hash_map: HashMap):
    """Процесс: Распознавание артикулов. Шаг: Новый шаг ActiveCV."""
    screen = ui_models.ActiveCVArticleRecognition(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def serial_number_ocr_settings_on_start(hash_map: HashMap):
    """Процесс: OcrTextRecognition. Экран: SerialNumberOCRSettings."""
    screen = ui_models.SerialNumberOCRSettings(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def serial_number_ocr_settings_on_input(hash_map: HashMap):
    """Процесс: OcrTextRecognition. Экран: SerialNumberOCRSettings."""
    screen = ui_models.SerialNumberOCRSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def serial_key_recognition_ocr(hash_map: HashMap):
    """Процесс: OcrTextRecognition. Экран: SerialNumberOCRSettings."""
    ui_models.SerialNumberOCRSettings.serial_key_recognition_ocr(hash_map)


@HashMap()
def docs_tiles_on_start(hash_map: HashMap):
    """Отдельные обработчики плиток для определения процесса hash_map'ом"""
    screen: ui_models.DocumentsTiles = ui_models.DocumentsTiles(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def gs_tiles_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.GroupScanTiles)
    screen.on_start()


@HashMap()
def tiles_on_input(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def docs_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.DocumentsDocsListScreen)
    screen.on_start()


@HashMap()
def docs_on_select(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.DocumentsDocsListScreen)
    screen.on_input()


@HashMap()
def group_docs_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.GroupScanDocsListScreen)
    screen.on_start()


@HashMap()
def group_docs_on_select(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.GroupScanDocsListScreen)
    screen.on_input()


@HashMap()
def doc_details_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.DocumentsDocDetailScreen)
    screen.on_start()


@HashMap()
def doc_details_listener(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.DocumentsDocDetailScreen)
    screen.on_input()

@HashMap()
def group_doc_details_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.GroupScanDocDetailsScreen )
    screen.on_start()

@HashMap()
def group_doc_details_listener(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.GroupScanDocDetailsScreen)
    screen.on_input()


@HashMap()
def highlight_scanned_item(hash_map: HashMap):
    """ Обработчик для отмены раскраски отсканированного товара """
    screen = ui_models.DocDetailsScreen(hash_map, rs_settings)
    screen.disable_highlight()


@HashMap()
def send_post_lines_data(hash_map: HashMap):
    """ Отправка на 1С выбранных в nosql строк post-запросом """
    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.send_unsent_lines_run()


@HashMap()
def send_all_scan_lines(hash_map: HashMap):
    """ Отправка на 1С всех nosql строк товара post-запросом """
    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.send_all_scan_lines_run()


@HashMap()
def after_send_post_lines_data(hash_map: HashMap):
    """ После отправки-обработки post-запроса """
    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.after_send_data()


@HashMap()
def adr_docs_on_start(hash_map: HashMap):
    screen = create_screen(
        hash_map=hash_map,
        screen_class=sm_adr_docs.AdrDocsListScreen
    )
    screen.init_screen()
    screen.on_start()


@HashMap()
def adr_doc_on_select(hash_map: HashMap):
    screen = create_screen(
        hash_map=hash_map,
        screen_class=sm_adr_docs.AdrDocsListScreen
    )
    screen.on_input()


@HashMap()
def adr_doc_details_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, sm_adr_docs.AdrDocDetailsScreen)
    screen.on_start()


@HashMap()
def adr_doc_details_on_input(hash_map: HashMap):
    screen = create_screen(hash_map, sm_adr_docs.AdrDocDetailsScreen)
    screen.on_input()


@HashMap()
def docs_offline_on_start(hash_map: HashMap):
    screen = ui_models.DocsOfflineListScreen(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def elem_viev_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.GoodsSelectScreen)
    screen.on_start()


@HashMap()
def elem_viev_on_click(hash_map):
    screen = create_screen(hash_map, ui_models.GoodsSelectScreen)
    screen.on_input()


@HashMap()
def adr_elem_view_on_start(hash_map):
    screen = create_screen(hash_map, sm_adr_docs.AdrGoodsSelectScreen)
    screen.on_start()


@HashMap()
def adr_elem_view_on_click(hash_map):
    screen = create_screen(hash_map, sm_adr_docs.AdrGoodsSelectScreen)
    screen.on_input()

@HashMap()
def barcode_register_doc_on_click(hash_map):
    screen = create_screen(hash_map, ui_models.BarcodeRegistrationScreen)
    screen.on_input()

@HashMap()
def barcode_register_doc_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.BarcodeRegistrationScreen)
    screen.on_start()

@HashMap()
def group_elem_view_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.GroupScanItemScreen)
    screen.on_start()


@HashMap()
def group_elem_view_on_click(hash_map):
    screen = create_screen(hash_map, ui_models.GroupScanItemScreen)
    screen.on_input()


@HashMap()
def group_elem_view_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.GroupScanItemScreen)
    screen.on_start()


@HashMap()
def group_elem_view_on_click(hash_map):
    screen = create_screen(hash_map, ui_models.GroupScanItemScreen)
    screen.on_input()


@HashMap()
def barcode_error_screen_listener(hash_map: HashMap):
    if hash_map['listener'] in ['ON_BACK_PRESSED', 'btn_continue_scan']:
        hash_map.show_screen("Документ товары")


# ^^^^^^^^^^^^^^^^^ Documents ^^^^^^^^^^^^^^^^^

@HashMap()
def select_item_on_start(hash_map: HashMap):
    create_screen(hash_map, ui_models.SelectItemScreen).on_start()

@HashMap()
def select_item_on_input(hash_map: HashMap):
    create_screen(hash_map, ui_models.SelectItemScreen).on_input()


@HashMap()
def select_item_result(hash_map: HashMap):
    hash_map.toast('select_item_result')

@HashMap()
def show_items_screen_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.ShowItemsScreen)
    screen.on_start()

@HashMap()
def show_items_screen_on_input(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.ShowItemsScreen)
    screen.on_input()

@HashMap()
def show_marks_screen_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.ShowMarksScreen)
    screen.on_start()

@HashMap()
def show_marks_screen_on_input(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.ShowMarksScreen)
    screen.on_input()


# =============== Goods =================


@HashMap()
def goods_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.GoodsListScreen)
    screen.init_screen().on_start()


@HashMap()
def goods_on_input(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.GoodsListScreen)
    screen.on_input()


@HashMap()
def select_type_goods_on_start(hash_map):
    screen = ui_models.SelectGoodsType(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def select_type_goods_on_input(hash_map):
    screen = ui_models.SelectGoodsType(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def good_card_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.ItemCard)
    screen.on_start()


@HashMap()
def good_card_post_start(hash_map):
    screen = create_screen(hash_map, ui_models.ItemCard)
    screen.on_post_start()


@HashMap()
def good_card_on_input(hash_map):
    screen = create_screen(hash_map, ui_models.ItemCard)
    screen.on_input()


@HashMap()
def offline_good_card_on_input(hash_map):
    screen = ui_models.ItemCardOfflineScreen(hash_map, rs_settings)
    screen.on_input()


# ^^^^^^^^^^^^^^^^^ Goods ^^^^^^^^^^^^^^^^^

# ==================== GoodsBalances =============================

@HashMap()
def balances_on_start(hash_map):
    screen: ui_models.GoodsBalancesItemCard = create_screen(hash_map)
    screen.on_start()


@HashMap()
def balances_on_input(hash_map):
    screen = ui_models.GoodsBalancesItemCard(hash_map, rs_settings)
    screen.on_input()


# ^^^^^^^^^^^^^^^^^^^^^ GoodsBalances ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== GoodsPrices =============================

@HashMap()
def prices_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.GoodsPricesItemCard)
    screen.on_start()


@HashMap()
def prices_on_input(hash_map):
    screen = create_screen(hash_map, ui_models.GoodsPricesItemCard)
    screen.on_input()


# ^^^^^^^^^^^^^^^^^^^^^ GoodsPrices ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
@HashMap()
def series_list_on_start(hash_map):
    screen: ui_models.SeriesSelectScreen = create_screen(hash_map, ui_models.SeriesSelectScreen)
    screen.on_start()


@HashMap()
def series_list_on_input(hash_map):
    screen: ui_models.SeriesSelectScreen = create_screen(hash_map, ui_models.SeriesSelectScreen)
    screen.on_input()


@HashMap()
def series_item_on_start(hash_map):
    screen: ui_models.SeriesItem =  create_screen(hash_map, ui_models.SeriesItem)
    screen.on_start()


@HashMap()
def series_item_on_input(hash_map):
    screen: ui_models.SeriesItem =  create_screen(hash_map, ui_models.SeriesItem)
    screen.on_input()


# ^^^^^^^^^^^^^^^^^^^^^ GoodsPrices ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# =============== Settings =================

@HashMap()
def settings_on_start(hash_map: HashMap):
    screen: ui_models.SettingsScreen = create_screen(hash_map, ui_models.SettingsScreen)
    screen.on_start()


@HashMap()
def settings_on_click(hash_map: HashMap):
    screen: ui_models.SettingsScreen = create_screen(hash_map, ui_models.SettingsScreen)
    screen.on_input()


@HashMap()
def font_sizes_on_start(hash_map: HashMap):
    screen: ui_models.FontSizeSettingsScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def font_size_settings_listener(hash_map: HashMap):
    screen: ui_models.FontSizeSettingsScreen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def test_barcode_listener(hash_map: HashMap):
    screen: ui_models.BarcodeTestScreen = create_screen(hash_map)
    screen.on_input()

@HashMap()
def test_barcode_on_start(hash_map: HashMap):
    screen: ui_models.BarcodeTestScreen = create_screen(hash_map)
    screen.on_start()  


@HashMap()
def settings_errors_on_start(hash_map: HashMap):
    screen: ui_models.ErrorLogScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def settings_errors_on_click(hash_map: HashMap):
    screen: ui_models.ErrorLogScreen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def http_settings_on_start(hash_map):
    screen: ui_models.HttpSettingsScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def http_settings_on_click(hash_map):
    screen: ui_models.HttpSettingsScreen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def sound_settings_on_start(hash_map):
    screen = ui_models.SoundSettings(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def sound_settings_listener(hash_map):
    screen = ui_models.SoundSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def documents_settings_on_input(hash_map):
    """Процесс: Параметры. Экран: Настройки документов"""
    screen = ui_models.DocumentsSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def documents_settings_on_start(hash_map):
    """Процесс: Параметры. Экран: Настройки документов"""
    screen = ui_models.DocumentsSettings(hash_map, rs_settings)
    screen.on_start()


# ^^^^^^^^^^^^^^^^^ Settings ^^^^^^^^^^^^^^^^^

# =============== Print =================

@HashMap()
def print_settings_on_input(hash_map):
    """Процесс: Печать. Экран: Настройки печати"""
    screen = ui_models.PrintSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def print_settings_on_start(hash_map):
    """Процесс: Печать. Экран: Настройки печати"""
    screen = ui_models.PrintSettings(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def template_list_on_start(hash_map):
    """Процесс: Печать. Экран: Список шаблонов"""
    screen: ui_models.TemplatesList = ui_models.TemplatesList(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def template_list_on_input(hash_map):
    """Процесс: Печать. Экран: Список шаблонов"""
    screen: ui_models.TemplatesList = ui_models.TemplatesList(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def html_view_on_start(hash_map):
    """Процесс: Печать. Экран: Результат"""
    screen = ui_models.HtmlView(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def html_view_on_input(hash_map):
    """Процесс: Печать. Экран: Результат"""
    screen = ui_models.HtmlView(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def print_bluetooth_settings_on_input(hash_map):
    """Процесс: Печать. Экран: Настройки печати Bluetooth"""
    screen = ui_models.PrintBluetoothSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def print_bluetooth_settings_on_start(hash_map):
    """Процесс: Печать. Экран: Настройки печати Bluetooth"""
    screen = ui_models.PrintBluetoothSettings(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def bluetooth_error(hash_map):
    """Общий обработчик ошибки при печати через Bluetooth"""
    PrintService.bluetooth_error(hash_map)


@HashMap()
def print_wifi_settings_on_input(hash_map):
    """Процесс: Печать. Экран: Настройки печати WiFi"""
    screen = ui_models.PrintWiFiSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def print_wifi_settings_on_start(hash_map):
    """Процесс: Печать. Экран: Настройки печати WiFi"""
    screen = ui_models.PrintWiFiSettings(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def print_wifi(hash_map):
    """Обработчик для печати через WiFi. Должен быть вызван асинхронно"""
    PrintService.print_wifi(hash_map)


@HashMap()
def wifi_error(hash_map):
    """Общий обработчик ошибки при печати через WiFi"""
    PrintService.wifi_error(hash_map)


@HashMap()
def print_label_templates_on_start(hash_map):
    """Процесс: Печать. Экран: Настройки печати Шаблоны"""
    screen = ui_models.PrintLabelTemplatesSettings(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def print_label_templates_on_input(hash_map):
    """Процесс: Печать. Экран: Настройки печати Шаблоны"""
    screen = ui_models.PrintLabelTemplatesSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def print_label_template_size_on_input(hash_map):
    """Процесс: Печать. Экран: Настройки печати Размеры"""
    screen = ui_models.PrintTemplateSizeSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def print_label_template_size_on_start(hash_map):
    """Процесс: Печать. Экран: Настройки печати Размеры"""
    screen = ui_models.PrintTemplateSizeSettings(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def print_post_execute(hash_map):
    """Срабатывает после вызова PrintService.print и печатает ценник"""
    PrintService.print_post_execute(hash_map)

# ^^^^^^^^^^^^^^^^^ Print ^^^^^^^^^^^^^^^^^


@HashMap()
def file_browser_on_start(hash_map):
    screen = ui_models.SimpleFileBrowser(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def file_browser_on_input(hash_map):
    screen = ui_models.SimpleFileBrowser(hash_map, rs_settings)
    screen.on_input()


# =============== Debug =================

@HashMap()
def debug_on_start(hash_map: HashMap):
    screen: ui_models.DebugSettingsScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def debug_listener(hash_map, _files=None, _data=None):
    screen: ui_models.DebugSettingsScreen = create_screen(hash_map)
    screen.on_input()

# ^^^^^^^^^^^^^^^^^ Debug ^^^^^^^^^^^^^^^^^


