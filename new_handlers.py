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
def put_notification(hash_map: HashMap):
    """ Обработчик для работы МП в режиме сервера. Уведомления о входящих документах """

    model = ui_models.MainEvents(hash_map, rs_settings)
    model.put_notification()


@HashMap()
def on_close_app(hash_map):
    # Попытка очистки кэша при выходе с приложения
    suClass.deleteCache()


# ^^^^^^^^^^^^^^^^^ Main events ^^^^^^^^^^^^^^^^^


# =============== Documents =================

@HashMap()
def docs_tiles_on_start(hash_map: HashMap):
    """Отдельные обработчики плиток для определения процесса hash_map'ом"""
    screen = ui_models.DocumentsTiles(hash_map, rs_settings)
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


# ^^^^^^^^^^^^^^^^^ Documents ^^^^^^^^^^^^^^^^^


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

# ^^^^^^^^^^^^^^^^^ Settings ^^^^^^^^^^^^^^^^^

