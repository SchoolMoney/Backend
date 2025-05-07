from enum import IntEnum

from src.SQL.Enum import AccountStatus as CSValues


class UserAccountStatusEnum(IntEnum):
    DISABLED = CSValues.DISABLED
    LOCKED = CSValues.LOCKED
    ENABLED = CSValues.ENABLED
