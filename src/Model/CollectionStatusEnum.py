from enum import IntEnum

from src.SQL.Enum import CollectionStatus as CSValues


class CollectionStatusEnum(IntEnum):
    OPEN = CSValues.OPEN
    FINISHED = CSValues.FINISHED
    NOT_PAID_BEFORE_DEADLINE = CSValues.NOT_PAID_BEFORE_DEADLINE
    CANCELLED = CSValues.CANCELLED
