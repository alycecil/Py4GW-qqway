"""
Party Feasts widget.

Party-wide buttons for the two combo consumables: Hero's Trifecta
(model 38619: Essence + Grail + Armor) and Empowering Feast
(model 38618: Cupcake + Apple + Egg + Corn + Pie).

Each button broadcasts a PCon shared message. Feast goes to every real
account in the local party (self included) since food effects are
per-character; Trifecta goes to exactly one account - the party member
holding the most - since its effect is party-wide. The Messaging widget's
UsePcon handler on each client checks its own inventory before using
anything, so accounts without the item simply no-op. Effect skill IDs are
intentionally 0 (same as the Candy Cane / Honeycomb precedent): the combos
grant several effects at once, so skipping on any single known effect
would be wrong.
"""

import PyImGui
import PySystem

from Py4GWCoreLib import ImGui, ModelID, Player, Routines, SharedCommandType, Utils
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Settings import Settings

MODULE_NAME = "Party Feasts"
MODULE_ICON = "Assets/Textures/Module_Icons/Pycons.png"
WIDGET_KEY = "Widgets/Guild Wars/Party Feasts"

INI_PATH = "Widgets/PartyFeasts"
INI_FILENAME = "PartyFeasts.ini"

_POST_THROTTLE_MS = 100

initialized = False
INI_KEY = ""
_enabled = False
_last_post_tick_ms = 0
_last_result = "idle"


def _cfg() -> Settings:
    return Settings(f"{INI_PATH}/{INI_FILENAME}", "account")


def _set_enabled(value: bool) -> None:
    global _enabled
    _enabled = value
    _cfg().set("Main", "enabled", value)


def _party_recipient_emails() -> list[str]:
    """Real-player accounts in the local party, self included."""
    local_email = str(Player.GetAccountEmail() or "").strip()
    if not local_email:
        return []
    try:
        local_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(local_email)
    except Exception:
        local_account = None
    try:
        accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData(sort_results=False) or [])
    except TypeError:
        accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData() or [])
    except Exception:
        accounts = []

    local_party_id = 0
    if local_account is not None:
        local_party_id = int(getattr(getattr(local_account, "AgentPartyData", None), "PartyID", 0) or 0)

    result: list[str] = []
    seen: set[str] = set()
    for account in accounts:
        email = str(getattr(account, "AccountEmail", "") or "").strip()
        if not email or email in seen:
            continue
        if bool(getattr(account, "IsHero", False)) or bool(getattr(account, "IsNPC", False)):
            continue
        if local_party_id > 0:
            account_party_id = int(getattr(getattr(account, "AgentPartyData", None), "PartyID", 0) or 0)
            if account_party_id != local_party_id:
                continue
        seen.add(email)
        result.append(email)
    if local_email not in seen:
        result.append(local_email)
    return result


def _throttled() -> bool:
    return int(Utils.GetBaseTimestamp()) - _last_post_tick_ms < _POST_THROTTLE_MS


def _carrier_model_count(email: str, model_id: int, local_email: str) -> int:
    # Own inventory is authoritative locally; remote counts come from shared
    # memory and can lag a snapshot behind.
    if email == local_email:
        return _model_count(model_id)
    try:
        return int(GLOBAL_CACHE.ShMem.GetAccountInventoryModelCount(email, int(model_id)) or 0)
    except Exception:
        return 0


def _richest_carrier(model_id: int, recipients: list[str]) -> str | None:
    local_email = str(Player.GetAccountEmail() or "").strip()
    best_email: str | None = None
    best_count = 0
    for email in sorted(recipients):
        count = _carrier_model_count(email, model_id, local_email)
        if count > best_count:
            best_count = count
            best_email = email
    return best_email


def _pop_model(model_id: int, label: str, single_carrier: bool = False) -> None:
    global _last_post_tick_ms, _last_result
    if not Routines.Checks.Map.MapValid():
        _last_result = "not in a valid map"
        return
    if _throttled():
        return
    sender_email = str(Player.GetAccountEmail() or "").strip()
    if not sender_email:
        _last_result = "unknown account email"
        return
    recipients = _party_recipient_emails()
    if not recipients:
        _last_result = "no party recipients found"
        return
    if single_carrier:
        carrier = _richest_carrier(model_id, recipients)
        if carrier is None:
            _last_result = f"no party member holds a {label}"
            return
        recipients = [carrier]
        label = f"{label} via {carrier}"
    sent = 0
    for receiver_email in recipients:
        try:
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                receiver_email,
                SharedCommandType.PCon,
                (int(model_id), 0, 0, 0),
            )
            sent += 1
        except Exception as exc:
            ConsoleLog(MODULE_NAME, f"Failed to message {receiver_email}: {exc}", Console.MessageType.Warning)
    _last_post_tick_ms = int(Utils.GetBaseTimestamp())
    _last_result = f"{label} requested on {sent} account(s)"
    ConsoleLog(MODULE_NAME, _last_result, Console.MessageType.Info)


def _model_count(model_id: int) -> int:
    try:
        return int(GLOBAL_CACHE.Inventory.GetModelCount(int(model_id)) or 0)
    except Exception:
        return 0


def main():
    global initialized, INI_KEY, _enabled

    if not Routines.Checks.Map.MapValid():
        return

    if not INI_KEY:
        INI_KEY = _cfg().name
        if not INI_KEY:
            return
        initialized = True
        _enabled = _cfg().get_bool("Main", "enabled", False)


def draw_widget():
    global INI_KEY, _enabled

    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        new_enabled = PyImGui.checkbox("Enabled##feasts", _enabled)
        if new_enabled != _enabled:
            _set_enabled(new_enabled)
            ConsoleLog(
                MODULE_NAME,
                "Party Feasts enabled." if new_enabled else "Party Feasts disabled.",
                Console.MessageType.Info,
            )

        if not _enabled:
            ImGui.End(INI_KEY)
            return

        PyImGui.separator()

        trifecta_count = _model_count(int(ModelID.Heros_Trifecta.value))
        if PyImGui.button(f"Pop Trifecta (party)##feasts_trifecta"):
            _pop_model(int(ModelID.Heros_Trifecta.value), "Hero's Trifecta", single_carrier=True)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Hero's Trifecta: one pop covers the party, so only the richest carrier uses one.")
        PyImGui.same_line(0, -1)
        PyImGui.text(f"own stock: {trifecta_count}")

        feast_count = _model_count(int(ModelID.Empowering_Feast.value))
        if PyImGui.button(f"Pop Feast (party)##feasts_feast"):
            _pop_model(int(ModelID.Empowering_Feast.value), "Empowering Feast")
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Empowering Feast: Cupcake + Apple + Egg + Corn + Pie on every party member.")
        PyImGui.same_line(0, -1)
        PyImGui.text(f"own stock: {feast_count}")

        PyImGui.separator()
        PyImGui.text(f"Status: {_last_result}")
        PyImGui.text_wrapped(
            "Each client uses the item from its own inventory; accounts without "
            "one do nothing. Heroes are never messaged."
        )

    ImGui.End(INI_KEY)


def draw():
    global initialized
    if initialized:
        draw_widget()


if __name__ == "__main__":
    main()
