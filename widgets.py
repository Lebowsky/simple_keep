from abc import ABC, abstractmethod, abstractproperty
from typing import Union, List
import json


class Widget(ABC):
    @abstractmethod
    def __init__(self, **kwargs):
        self.type: str
        self.Value: str
        self.Variable: str = ''
        self.width = "wrap_content"
        self.height = "wrap_content"
        self.weight = '0'
        self.NoRefresh = False
        self.show_by_condition = ''
        # self.document_type = ''
        self.mask = ''

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


class CustomCards:
    def __init__(self, layout: LinearLayout, options: dict, cardsdata: List[dict]):
        self.customcards = {
            'layout': layout,
            'cardsdata': cardsdata,
            'options': options
        }

    def to_json(self):
        return json.dumps(self, default=lambda x: vars(x), indent=4, ensure_ascii=False).encode('utf8').decode()


class CustomTable:
    def __init__(self, layout: LinearLayout, tabledata: List[dict]):
        self.customtable = {
            'layout': layout,
            'tabledata': tabledata
        }

    def to_json(self):
        return json.dumps(self, default=lambda x: vars(x), indent=4, ensure_ascii=False).encode('utf8').decode()
