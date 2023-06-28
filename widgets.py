from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
import json

wrap_content = "wrap_content"
match_parent = 'match_parent'


class Widget(ABC):
    @abstractmethod
    def __init__(self, **kwargs):
        self.type: str
        self.Value: str
        self.width = wrap_content
        self.height = wrap_content
        self.weight = 0

        if kwargs:
            for key, value in kwargs.items():
                self.__dict__[key] = value

    def to_json(self):
        return json.dumps(self, default=lambda x: vars(x), indent=4)


class Picture(Widget):
    def __init__(self, **kwargs):
        self.Value = '@pic'
        super().__init__(**kwargs)
        self.type = "Picture"


class TextView(Widget):
    def __init__(self, **kwargs):
        self.Value = '@value'
        super().__init__(**kwargs)
        self.type = "TextView"


class CheckBox(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = 'CheckBox'


class PopupMenuButton(Widget):
    def __init__(self, **kwargs):
        self.Value = '@value'
        super().__init__(**kwargs)
        self.type = "PopupMenuButton"
        self.show_by_condition = ''
        self.NoRefresh = False
        self.document_type = ''
        self.mask = ''


class LinearLayout(Widget):
    def __init__(self, *args, **kwargs):
        self.type = 'LinearLayout'
        self.orientation = "vertical"

        super().__init__(**kwargs)
        self.Elements = list(args) or []

    def append(self, *widgets):
        for widget in widgets:
            self.Elements.append(widget)


class Options:
    def __init__(self, search_enabled=True, save_position=True):
        self.options = {
            'search_enabled': search_enabled,
            'save_position': save_position
        }


class CustomCards:
    def __init__(self, layout: LinearLayout, options: Options, cardsdata: List[dict] = []):
        self.customcards = {
            'options': options or Options(),
            'layout': layout,
            'cardsdata': cardsdata
        }

    def to_json(self):
        return json.dumps(self, default=lambda x: vars(x), indent=4, ensure_ascii=False).encode('utf8').decode()


class CustomTable:
    def __init__(self, layout: LinearLayout, options: Options, tabledata: List[dict]):
        self.customtable = {
            'options': options or Options(),
            'layout': layout,
            'tabledata': tabledata
        }

    def to_json(self):
        return json.dumps(self, default=lambda x: vars(x), indent=4, ensure_ascii=False).encode('utf8').decode()


@dataclass
class ModernField:
    hint: str = ''
    default_text: str = ''
    counter: bool = False
    counter_max: int = 0
    input_type: int = 0
    password: bool = False
    events: bool = False

    """
    TYPE_NULL: 0
    
    TYPE_CLASS_NUMBER: 2
    TYPE_NUMBER_FLAG_DECIMAL: 8192 
    TYPE_NUMBER_FLAG_SIGNED: 4096 
    TYPE_NUMBER_VARIATION_NORMAL: 0
    TYPE_NUMBER_VARIATION_PASSWORD: 16
    
    TYPE_CLASS_DATETIME : 4
    TYPE_DATETIME_VARIATION_DATE: 16
    TYPE_DATETIME_VARIATION_NORMAL: 0
    TYPE_DATETIME_VARIATION_TIME: 32
    
    TYPE_CLASS_PHONE: 3
    
    TYPE_MASK_CLASS: 15
    TYPE_MASK_FLAGS: 16773120 
    TYPE_MASK_VARIATION: 4080 

    TYPE_CLASS_TEXT: 1
    TYPE_TEXT_FLAG_AUTO_COMPLETE: 65536 
    TYPE_TEXT_FLAG_AUTO_CORRECT: 32768 
    TYPE_TEXT_FLAG_CAP_CHARACTERS: 4096 
    TYPE_TEXT_FLAG_CAP_SENTENCES: 16384 
    TYPE_TEXT_FLAG_CAP_WORDS: 8192  
    TYPE_TEXT_FLAG_ENABLE_TEXT_CONVERSION_SUGGESTIONS: 1048576 
    TYPE_TEXT_FLAG_IME_MULTI_LINE: 262144 
    TYPE_TEXT_FLAG_MULTI_LINE: 131072 
    TYPE_TEXT_FLAG_NO_SUGGESTIONS: 524288 
    TYPE_TEXT_VARIATION_EMAIL_ADDRESS: 32
    TYPE_TEXT_VARIATION_EMAIL_SUBJECT: 48
    TYPE_TEXT_VARIATION_FILTER: 176 
    TYPE_TEXT_VARIATION_LONG_MESSAGE: 80
    TYPE_TEXT_VARIATION_NORMAL: 0
    TYPE_TEXT_VARIATION_PASSWORD: 128 
    TYPE_TEXT_VARIATION_PERSON_NAME:  96
    TYPE_TEXT_VARIATION_PHONETIC: 192 
    TYPE_TEXT_VARIATION_POSTAL_ADDRESS: 112 
    TYPE_TEXT_VARIATION_SHORT_MESSAGE: 64 
    TYPE_TEXT_VARIATION_URI: 16 
    TYPE_TEXT_VARIATION_VISIBLE_PASSWORD: 144 
    TYPE_TEXT_VARIATION_WEB_EDIT_TEXT: 160
    TYPE_TEXT_VARIATION_WEB_EMAIL_ADDRESS: 208 
    TYPE_TEXT_VARIATION_WEB_PASSWORD: 224 
    """

    def to_json(self):
        return json.dumps(
            self,
            default=lambda x: {k: v for k, v in vars(x).items() if v},
            indent=4, ensure_ascii=False
        ).encode('utf8').decode()
