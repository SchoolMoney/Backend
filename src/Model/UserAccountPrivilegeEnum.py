from enum import IntEnum

from src.SQL.Enum import Privilege as Privileges

class UserAccountPrivilegeEnum(IntEnum):
    STANDARD_USER = Privileges.STANDARD_USER
    ADMIN_USER = Privileges.ADMIN_USER
