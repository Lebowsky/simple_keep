from typing import Optional
from pydantic import BaseModel, Field, root_validator

class SeriesItemModel(BaseModel):
    id: Optional[str]
    id_doc: str
    item_id: str = Field(alias='id_good')
    property_id: Optional[str] = Field(alias='id_properties')
    warehouse_id: Optional[str] = Field(alias='id_warehouse')
    cell_id: Optional[str] = Field(alias='cell')
    name: str
    number: str
    best_before: Optional[str]
    production_date: Optional[str]
    qtty: int

    @root_validator(pre=True)
    def fill_type_pre(cls, values):
        if not values.get('name'):
            values['name'] = values.get('number')
        return values

    class Config:
        allow_population_by_field_name = True

