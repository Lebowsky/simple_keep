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

    model = ui_models.MainEvents(hash_map, rs_settings)
    model.app_on_start()


@HashMap()
def timer_update(hash_map: HashMap):
    """ Обработчик для фонового обмена """

    timer = ui_models.Timer(hash_map, rs_settings)
    timer.timer_on_start()


@HashMap()
def event_service(hash_map):
    """ Обработчик для работы МП в режиме сервера. В ws_body по умолчанию лежит текст конфигурации """

    hash_map['ws_body'] = hash_map['ANDROID_ID']


@HashMap()
def on_sql_error(hash_map):
    model = ui_models.MainEvents(hash_map, rs_settings)
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
def barcode_flow_listener(hash_map:HashMap):
    """Процесс: Сбор ШК. Экран: ПотокШтрихкодовДокумента"""
    screen = ui_models.FlowDocDetailsScreen(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def serial_key_recognition_ocr(hash_map:HashMap):
    """Процесс: Сбор ШК. Экран: ПотокШтрихкодовДокумента.
       Шаблон Распознавания: Серийный номер"""
    ui_models.FlowDocDetailsScreen.serial_key_recognition_ocr(hash_map, rs_settings)


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
def select_good_article_on_input(hash_map: HashMap):
    """Процесс: Документы. Экран: ВыборТовараАртикул."""
    screen = ui_models.GoodsSelectArticle(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def select_good_article_on_start(hash_map: HashMap):
    """Процесс: Документы. Экран: ВыборТовараАртикул."""
    screen = ui_models.GoodsSelectArticle(hash_map, rs_settings)
    screen.on_start()

@HashMap()
def docs_tiles_on_start(hash_map: HashMap):
    """Отдельные обработчики плиток для определения процесса hash_map'ом"""
    screen: ui_models.DocumentsTiles = ui_models.DocumentsTiles(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def gs_tiles_on_start(hash_map: HashMap):
    screen = ui_models.GroupScanTiles(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def tiles_on_input(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def docs_on_start(hash_map: HashMap):
    screen: ui_models.DocsListScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def docs_on_select(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()



# @HashMap()
# def doc_details_on_start(hash_map: HashMap):
#     screen: ui_models.GroupScanDocDetailsScreen = create_screen(hash_map)
#     screen.on_start()

@HashMap()
def doc_details_on_start(hash_map: HashMap):
    screen: ui_models.GroupScanDocDetailsScreenNew = create_screen(hash_map)
    screen.on_start()


@HashMap()
def doc_details_listener(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def doc_details_before_process_barcode(hash_map):
    """ Обработчик для синхронного запроса и обновления данных после сканирования и перед обработкой ШК"""

    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.before_process_barcode()


@HashMap()
def doc_run_post_barcode_scanned(hash_map):
    """ Отправка данных после обработки ШК"""

    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.hash_map.remove('toast')
    screen.post_barcode_scanned()


@HashMap()
def doc_scan_error_sound(hash_map):
    """ Звуковые сигналы ошибок сканирования"""

    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.scan_error_sound()


@HashMap()
def highlight_scanned_item(hash_map: HashMap):
    """ Обработчик для отмены раскраски отсканированного товара """
    screen = ui_models.DocDetailsScreen(hash_map, rs_settings)
    screen.disable_highlight()


@HashMap()
def send_post_lines_data(hash_map: HashMap):
    """ Отправка на 1С выбранных в nosql строк post-запросом """
    screen = ui_models.GroupScanDocDetailsScreenNew(hash_map, rs_settings)
    screen.send_unsent_lines_run()


@HashMap()
def send_all_scan_lines(hash_map: HashMap):
    """ Отправка на 1С всех nosql строк товара post-запросом """
    screen = ui_models.GroupScanDocDetailsScreenNew(hash_map, rs_settings)
    screen.send_all_scan_lines_run()


@HashMap()
def after_send_post_lines_data(hash_map: HashMap):
    """ После отправки-обработки post-запроса """
    screen = ui_models.GroupScanDocDetailsScreenNew(hash_map, rs_settings)
    screen.after_send_data()


@HashMap()
def adr_docs_on_start(hash_map: HashMap):
    screen = create_screen(
        hash_map=hash_map,
        screen_class=ui_models.AdrDocsListScreen
    )
    screen.on_start()

@HashMap()
def adr_doc_on_select(hash_map: HashMap):
    screen = create_screen(
        hash_map=hash_map,
        screen_class=ui_models.AdrDocsListScreen
    )
    screen.on_input()


@HashMap()
def adr_doc_details_on_start(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.AdrDocDetailsScreen)
    screen.on_start()

@HashMap()
def adr_doc_details_on_input(hash_map: HashMap):
    screen = create_screen(hash_map, ui_models.AdrDocDetailsScreen)
    screen.on_input()

@HashMap()
def docs_offline_on_start(hash_map: HashMap):
    screen = ui_models.DocsOfflineListScreen(hash_map, rs_settings)
    screen.on_start()

@HashMap()
def elem_viev_on_start(hash_map):
    screen = ui_models.GoodsSelectScreen(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def elem_viev_on_click(hash_map):
    screen = ui_models.GoodsSelectScreen(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def adr_elem_view_on_start(hash_map):
    screen = create_screen(hash_map, ui_models.AdrGoodsSelectScreen)
    screen.on_start()


@HashMap()
def adr_elem_view_on_click(hash_map):
    screen = create_screen(hash_map, ui_models.AdrGoodsSelectScreen)
    screen.on_input()


@HashMap()
def barcode_error_screen_listener(hash_map: HashMap):
    if hash_map['listener'] in ['ON_BACK_PRESSED', 'btn_continue_scan']:
        hash_map.show_screen("Документ товары")


# ^^^^^^^^^^^^^^^^^ Documents ^^^^^^^^^^^^^^^^^

@HashMap()
def select_item_on_start(hash_map: HashMap):
    ui_models.SelectItemScreen(hash_map, rs_settings).on_start()

@HashMap()
def select_item_on_input(hash_map: HashMap):
    ui_models.SelectItemScreen(hash_map, rs_settings).on_input()

@HashMap()
def select_item_result(hash_map: HashMap):
    hash_map.toast('select_item_result')

# =============== Goods =================

@HashMap()
def goods_on_start(hash_map):
    screen = ui_models.GoodsListScreen(hash_map, rs_settings)
    screen.init_screen().on_start()


@HashMap()
def goods_on_input(hash_map: HashMap):
    screen = ui_models.GoodsListScreen(hash_map, rs_settings)
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
    screen: ui_models.ItemCard = create_screen(hash_map)
    screen.on_start()


@HashMap()
def good_card_post_start(hash_map):
    screen: ui_models.ItemCard = create_screen(hash_map)
    screen.on_post_start()


@HashMap()
def good_card_on_input(hash_map):
    screen: ui_models.ItemCard = create_screen(hash_map)
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
    screen: ui_models.GoodsPricesItemCard = create_screen(hash_map)
    screen.on_start()

@HashMap()
def prices_on_input(hash_map):
    screen = ui_models.GoodsPricesItemCard(hash_map, rs_settings)
    screen.on_input()


# ^^^^^^^^^^^^^^^^^^^^^ GoodsPrices ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

@HashMap()
def series_list_on_start(hash_map):
    screen: ui_models.SeriesList = ui_models.SeriesList(hash_map, rs_settings)
    screen.on_start()

@HashMap()
def series_list_on_input(hash_map):
    screen = ui_models.SeriesList(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def series_item_on_start(hash_map):
    screen: ui_models.SeriesItem = ui_models.SeriesItem(hash_map, rs_settings)
    screen.on_start()

@HashMap()
def series_item_on_input(hash_map):
    screen: ui_models.SeriesItem = ui_models.SeriesItem(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def adr_series_list_on_start(hash_map):
    screen: ui_models.SeriesAdrList = ui_models.SeriesAdrList(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def adr_series_list_on_input(hash_map):
    screen: ui_models.SeriesAdrList = ui_models.SeriesAdrList(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def adr_series_item_on_start(hash_map):
    screen: ui_models.SeriesAdrItem = ui_models.SeriesAdrItem(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def adr_series_item_on_input(hash_map):
    screen: ui_models.SeriesAdrItem = ui_models.SeriesAdrItem(hash_map, rs_settings)
    screen.on_input()


# ^^^^^^^^^^^^^^^^^^^^^ GoodsPrices ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# =============== Settings =================

@HashMap()
def settings_on_start(hash_map: HashMap):
    screen: ui_models.SettingsScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def settings_on_click(hash_map: HashMap):
    screen: ui_models.SettingsScreen = create_screen(hash_map)
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

    # screen = ui_models.SelectGoodsType(hash_map, rs_settings)
    # screen.on_input()


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
    PrintService.bluetooth_error(hash_map)


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
    PrintService.wifi_error(hash_map)


@HashMap()
def print_label_templates_on_input(hash_map):
    """Процесс: Печать. Экран: Настройки печати Шаблоны"""
    screen = ui_models.PrintLabelTemplatesSettings(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def print_label_templates_on_start(hash_map):
    """Процесс: Печать. Экран: Настройки печати Шаблоны"""
    screen = ui_models.PrintLabelTemplatesSettings(hash_map, rs_settings)
    screen.on_start()

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
def print_postExecute(hash_map):
    """Срабатывает после вызова PrintService.print и печатает ценник"""
    PrintService.print_postExecute(hash_map)
# ^^^^^^^^^^^^^^^^^ Settings ^^^^^^^^^^^^^^^^^

# =============== Html =================

@HashMap()
def html_view_on_start(hash_map):
    screen = ui_models.HtmlView(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def html_view_on_input(hash_map):
    screen = ui_models.HtmlView(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def template_list_on_start(hash_map):
    screen: ui_models.TemplatesList = ui_models.TemplatesList(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def template_list_on_input(hash_map):
    screen: ui_models.TemplatesList = ui_models.TemplatesList(hash_map, rs_settings)
    screen.on_input()

# ^^^^^^^^^^^^^^^^^ Html ^^^^^^^^^^^^^^^^^

@HashMap()
def file_browser_on_start(hash_map):
    screen: ui_models.SimpleFileBrowser = ui_models.SimpleFileBrowser(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def file_browser_on_input(hash_map):
    screen: ui_models.SimpleFileBrowser = ui_models.SimpleFileBrowser(hash_map, rs_settings)
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
