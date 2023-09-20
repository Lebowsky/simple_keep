from java import jclass
from ru.travelfood.simple_ui import SimpleUtilites as suClass

from ui_utils import HashMap
import ui_models

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")
current_screen = None


def create_screen(hash_map: HashMap):
    """
    Метод для получения модели соответствующей текущему процессу и экрану.
    Если модель не реализована возвращает заглушку
    Реализован синглтон через глобальную переменную current_screen, для сохренения состояния текущего экрана
    """
    global current_screen

    screen_params = {
        'hash_map': hash_map,
        'rs_settings': rs_settings
    }
    screen_class = ui_models.ScreensFactory.get_screen_class(**screen_params)

    if not screen_class:
        current_screen = ui_models.MockScreen(**screen_params)
    elif not isinstance(current_screen, screen_class):
        current_screen = screen_class(**screen_params)
    else:
        current_screen.hash_map = hash_map
        current_screen.listener = hash_map['listener']
        current_screen.event = hash_map['event']

    return current_screen




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
    screen: ui_models.ActiveCVArticleRecognition = ui_models.ActiveCVArticleRecognition(hash_map, rs_settings)
    screen.on_object_detected()


@HashMap()
def select_good_article_on_input(hash_map: HashMap):
    """Процесс: Документы. Экран: ВыборТовараАртикул."""
    screen: ui_models.GoodsSelectArticle = ui_models.GoodsSelectArticle(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def select_good_article_on_start(hash_map: HashMap):
    """Процесс: Документы. Экран: ВыборТовараАртикул."""
    screen: ui_models.GoodsSelectArticle = ui_models.GoodsSelectArticle(hash_map, rs_settings)
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


@HashMap()
def doc_details_on_start(hash_map: HashMap):
    screen: ui_models.GroupScanDocDetailsScreen = create_screen(hash_map)
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
def adr_docs_on_start(hash_map: HashMap):
    screen: ui_models.AdrDocsListScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def adr_doc_on_select(hash_map: HashMap):
    screen: ui_models.AdrDocsListScreen = create_screen(hash_map)
    screen.on_input()

@HashMap()
def adr_doc_details_on_start(hash_map: HashMap):
    screen: ui_models.AdrDocDetailsScreen = create_screen(hash_map)
    screen.on_start()

@HashMap()
def adr_doc_details_on_input(hash_map: HashMap):
    screen: ui_models.AdrDocDetailsScreen = create_screen(hash_map)
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
def offline_elem_view_on_click(hash_map):
    screen = ui_models.GoodsSelectOfflineScreen(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def adr_elem_viev_on_start(hash_map):
    screen = ui_models.AdrGoodsSelectScreen(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def adr_elem_viev_on_click(hash_map):
    screen = ui_models.AdrGoodsSelectScreen(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def barcode_register_doc_on_click(hash_map):
    screen = ui_models.GoodBarcodeRegister(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def barcode_register_doc_on_start(hash_map):
    screen = ui_models.GoodBarcodeRegister(hash_map, rs_settings)
    screen.on_start()

@HashMap()
def doc_properties_on_start(hash_map):
    screen: ui_models.DocGoodSelectProperties = create_screen(hash_map)
    screen.on_start()

@HashMap()
def doc_properties_on_input(hash_map):
    screen = ui_models.DocGoodSelectProperties(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def doc_units_on_start(hash_map):
    screen = ui_models.DocGoodSelectUnit(hash_map, rs_settings)
    screen.on_start()

@HashMap()
def doc_units_on_input(hash_map):
    screen = ui_models.DocGoodSelectUnit(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def barcode_error_screen_listener(hash_map: HashMap):
    if hash_map['listener'] in ['ON_BACK_PRESSED', 'btn_continue_scan']:
        hash_map.show_screen("Документ товары")


# ^^^^^^^^^^^^^^^^^ Documents ^^^^^^^^^^^^^^^^^

# =============== Goods =================

@HashMap()
def goods_on_start(hash_map):
    screen: ui_models.GoodsListScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def goods_on_input(hash_map: HashMap):
    screen: ui_models.GoodsListScreen = ui_models.GoodsListScreen(hash_map, rs_settings)
    # screen: ui_models.GoodsListScreen = create_screen(hash_map)
    screen.on_input()
    # hash_map.toast(f'{hash_map.get_current_screen()} {hash_map.get_current_process()}')


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

@HashMap()
def barcode_register_item_on_input(hash_map):
    screen = ui_models.GoodItemBarcodeRegister(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def barcode_register_item_on_start(hash_map):
    screen: ui_models.GoodItemBarcodeRegister = create_screen(hash_map)
    screen.on_start()

@HashMap()
def item_properties_on_start(hash_map):
    screen: ui_models.ItemGoodSelectProperties = create_screen(hash_map)
    screen.on_start()

@HashMap()
def item_properties_on_input(hash_map):
    screen = ui_models.ItemGoodSelectProperties(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def item_units_on_start(hash_map):
    screen: ui_models.ItemGoodSelectUnit = create_screen(hash_map)
    screen.on_start()

@HashMap()
def item_units_on_input(hash_map):
    screen = ui_models.ItemGoodSelectUnit(hash_map, rs_settings)
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


@HashMap()
def wh_select_on_start(hash_map):
    screen: ui_models.SelectWH = create_screen(hash_map)
    screen.on_start()

@HashMap()
def wh_select_on_input(hash_map):
    screen = ui_models.SelectWH(hash_map, rs_settings)
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


@HashMap()
def price_types_on_start(hash_map):
    screen: ui_models.SelectPriceType = create_screen(hash_map)
    screen.on_start()

@HashMap()
def price_types_on_input(hash_map):
    screen = ui_models.SelectPriceType(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def properties_on_start(hash_map):
    screen: ui_models.SelectProperties = create_screen(hash_map)
    screen.on_start()

@HashMap()
def properties_on_input(hash_map):
    screen = ui_models.SelectProperties(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def units_on_start(hash_map):
    screen: ui_models.SelectUnit = create_screen(hash_map)
    screen.on_start()

@HashMap()
def units_on_input(hash_map):
    screen = ui_models.SelectUnit(hash_map, rs_settings)
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