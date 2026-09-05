"""
Unyielding Aura widget.

Feature 1 (drop): while the character maintains Unyielding Aura, watch for
dead party members (pets are excluded) inside spellcasting range minus a
configurable margin. When one is found, drop the aura so its end-effect
resurrects, and suppress recasting for 3 seconds.

Feature 2 (recast): when Unyielding Aura sits on the skill bar and is ready
to cast (slot found, charged, enough energy, nothing else casting) and no
drop happened in the last 3 seconds, cast it on self.
"""

from typing import Any, Generator

import PyImGui
import PySystem

from Py4GWCoreLib import Agent, ImGui, Map, Player, Range, Routines, ThrottledTimer
from Py4GWCoreLib.Effect import Effects
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Skillbar import SkillBar
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Settings import Settings

MODULE_NAME = "Unyielding Aura"
MODULE_ICON = "Assets/Textures/Skill_Icons/[268] - Unyielding Aura.jpg"
WIDGET_KEY = "Widgets/Guild Wars/Unyielding Aura"

INI_PATH = "Widgets/UnyieldingAura"
INI_FILENAME = "UnyieldingAura.ini"

_DROP_SUPPRESS_MS = 3000
_SCAN_MS = 250
_CAST_ROUTINE_TIMEOUT_MS = 8000
_TICK_ERROR_LOG_MS = 10000
_DEFAULT_MARGIN_PCT = 5
_MAX_MARGIN_PCT = 25

initialized = False
INI_KEY = ""
_enabled = False
_ua_skill_id = 0
_last_drop_tick_ms = 0
_cast_routine: Generator[None, Any, Any] | None = None
_cast_started_tick_ms = 0
_last_dead_count = 0
_maintaining = False
_ua_slot = 0
_stage = "idle"
_tick_error_last_log_ms = 0
_tick_error_last_msg = ""
_scan_timer = ThrottledTimer(_SCAN_MS)


def _cfg() -> Settings:
    return Settings(f"{INI_PATH}/{INI_FILENAME}", "account")


def _set_enabled(value: bool) -> None:
    global _enabled
    _enabled = value
    _cfg().set("Main", "enabled", value)


def _resolve_skill_id() -> int:
    global _ua_skill_id
    if _ua_skill_id != 0:
        return _ua_skill_id
    try:
        _ua_skill_id = int(Skill.GetID("Unyielding_Aura") or 0)
    except Exception:
        _ua_skill_id = 0
    return _ua_skill_id


def _drop_threshold() -> float:
    margin = _cfg().get_int("Drop", "margin_pct", _DEFAULT_MARGIN_PCT)
    margin = max(0, min(_MAX_MARGIN_PCT, margin))
    return float(Range.Spellcast.value) * (1.0 - margin / 100.0)


def _dead_party_members(threshold: float) -> list[int]:
    found: list[int] = []
    allies = Routines.Agents.GetDeadAllyArray(threshold) or []
    for ally_id in allies:
        ally_id = int(ally_id)
        if ally_id == 0:
            continue
        if not Agent.IsValid(ally_id):
            continue
        if not Agent.IsDead(ally_id):
            continue
        if Agent.IsPet(ally_id):
            continue
        found.append(ally_id)
    return found


def _drop_ua(reason: str) -> bool:
    global _last_drop_tick_ms, _stage
    ua_id = _resolve_skill_id()
    if ua_id == 0:
        return False
    player_id = Player.GetAgentID()
    if not Routines.Checks.Agents.HasEffect(player_id, ua_id):
        return False
    buff_id = int(Effects.GetBuffID(ua_id) or 0)
    if buff_id:
        Effects.DropBuff(buff_id)
        ConsoleLog(MODULE_NAME, reason, Console.MessageType.Info)
    else:
        ConsoleLog(
            MODULE_NAME,
            "Unyielding Aura active but no droppable buff found.",
            Console.MessageType.Warning,
        )
    _last_drop_tick_ms = int(PySystem.get_tick_count64())
    _stage = "dropped UA"
    return True


def _recast_suppressed() -> bool:
    if _last_drop_tick_ms == 0:
        return False
    return int(PySystem.get_tick_count64()) - _last_drop_tick_ms < _DROP_SUPPRESS_MS


def _log_tick_error(message: str) -> None:
    global _tick_error_last_log_ms, _tick_error_last_msg
    now_ms = int(PySystem.get_tick_count64())
    if message != _tick_error_last_msg or now_ms - _tick_error_last_log_ms >= _TICK_ERROR_LOG_MS:
        _tick_error_last_msg = message
        _tick_error_last_log_ms = now_ms
        ConsoleLog(MODULE_NAME, message, Console.MessageType.Error)


def _tick() -> None:
    global _last_dead_count, _maintaining, _ua_slot, _stage, _cast_routine, _cast_started_tick_ms

    cfg = _cfg()
    drop_on = cfg.get_bool("Drop", "enabled", True)
    recast_on = cfg.get_bool("Recast", "enabled", True)
    ua_id = _resolve_skill_id()
    if ua_id == 0:
        return

    player_id = Player.GetAgentID()
    _maintaining = bool(Routines.Checks.Agents.HasEffect(player_id, ua_id))
    _ua_slot = int(SkillBar.GetSlotBySkillID(ua_id) or 0)

    _last_dead_count = 0
    if drop_on and _maintaining:
        dead = _dead_party_members(_drop_threshold())
        _last_dead_count = len(dead)
        if dead:
            _cast_routine = None
            _drop_ua(f"Dropped Unyielding Aura - {len(dead)} dead party member in range.")
            return

    if not recast_on:
        return
    if _maintaining:
        return
    if _cast_routine is not None:
        return
    if _recast_suppressed():
        return
    if not Routines.Checks.Skills.CanCast():
        return
    if not 1 <= _ua_slot <= 8:
        return
    if not Routines.Checks.Skills.HasEnoughEnergy(player_id, ua_id):
        return
    if not Routines.Checks.Skills.IsSkillIDReady(ua_id):
        return
    _stage = "casting UA"
    ConsoleLog(MODULE_NAME, f"Casting Unyielding Aura (slot {_ua_slot}).", Console.MessageType.Info)
    _cast_started_tick_ms = int(PySystem.get_tick_count64())
    _cast_routine = Routines.Yield.Skills.CastSkillID(
        ua_id, target_agent_id=player_id, aftercast_delay=250, log=True
    )


def main():
    global initialized, INI_KEY, _enabled, _cast_routine, _stage

    if not Routines.Checks.Map.MapValid():
        _cast_routine = None
        return

    if not INI_KEY:
        INI_KEY = _cfg().name
        if not INI_KEY:
            return
        initialized = True
        _enabled = _cfg().get_bool("Main", "enabled", False)

    if not _enabled:
        _cast_routine = None
        _stage = "idle"
        return

    _resolve_skill_id()

    if _scan_timer.IsExpired():
        _scan_timer.Reset()
        try:
            _tick()
        except Exception as exc:
            _log_tick_error(f"scan failed: {exc}")

    if _cast_routine is not None:
        if int(PySystem.get_tick_count64()) - _cast_started_tick_ms > _CAST_ROUTINE_TIMEOUT_MS:
            ConsoleLog(MODULE_NAME, "Cast routine timed out - abandoning.", Console.MessageType.Warning)
            _cast_routine = None
            _stage = "idle"
        else:
            try:
                next(_cast_routine)
            except StopIteration:
                _cast_routine = None
                _stage = "idle"


def draw_widget():
    global INI_KEY, _enabled
    cfg = _cfg()

    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        new_enabled = PyImGui.checkbox("Enabled##ua", _enabled)
        if new_enabled != _enabled:
            _set_enabled(new_enabled)
            ConsoleLog(
                MODULE_NAME,
                "Unyielding Aura enabled." if new_enabled else "Unyielding Aura disabled.",
                Console.MessageType.Info,
            )

        PyImGui.separator()

        drop_on = cfg.get_bool("Drop", "enabled", True)
        new_drop = PyImGui.checkbox("Drop UA on dead party member", drop_on)
        if new_drop != drop_on:
            cfg.set("Drop", "enabled", new_drop)

        margin = cfg.get_int("Drop", "margin_pct", _DEFAULT_MARGIN_PCT)
        margin = max(0, min(_MAX_MARGIN_PCT, margin))
        new_margin = PyImGui.slider_int("Range margin %", margin, 0, _MAX_MARGIN_PCT)
        if new_margin != margin:
            cfg.set("Drop", "margin_pct", new_margin)

        recast_on = cfg.get_bool("Recast", "enabled", True)
        new_recast = PyImGui.checkbox("Recast UA when ready", recast_on)
        if new_recast != recast_on:
            cfg.set("Recast", "enabled", new_recast)

        PyImGui.separator()

        PyImGui.text(f"State: {_stage}")
        PyImGui.text(f"Maintaining UA: {'yes' if _maintaining else 'no'}")
        PyImGui.text(f"UA slot: {_ua_slot if 1 <= _ua_slot <= 8 else '--'}")
        PyImGui.text(f"Dead party members in range: {_last_dead_count}")
        PyImGui.text(f"Recast: {'suppressed' if _recast_suppressed() else 'ready'}")

        PyImGui.separator()

        if PyImGui.button("Drop UA now"):
            _drop_ua("Dropped Unyielding Aura manually.")

        PyImGui.separator()

        PyImGui.text_wrapped(
            "Drop: while maintaining Unyielding Aura, drops it when a dead "
            "party member (pets excluded) is inside spellcast range minus the "
            "margin, then blocks recasting for 3 seconds. Recast: casts UA on "
            "self when it is on the bar, charged, and affordable."
        )

    ImGui.End(INI_KEY)


def draw():
    global initialized
    if initialized:
        draw_widget()


if __name__ == "__main__":
    main()