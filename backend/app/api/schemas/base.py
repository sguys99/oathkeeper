from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    """Base for schemas that read from ORM objects."""

    model_config = ConfigDict(from_attributes=True)
