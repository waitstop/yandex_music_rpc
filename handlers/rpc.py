from tkinter import StringVar

from pypresence import Presence
from pypresence.exceptions import PyPresenceException


def update_rpc(data: dict | Exception, rpc: Presence, status: StringVar) -> Exception | None:
    try:
        if type(data) == Exception:
            status.set(str(data))
            return data
        rpc.update(**data)
    except PyPresenceException:
        status.set("Ошибка обновления RPC")
        return Exception("Ошибка обновления RPC")
