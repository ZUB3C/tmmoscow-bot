from pydantic import BaseModel as PydanticBaseModel
from pydantic.alias_generators import to_camel


class BaseModel(PydanticBaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True
