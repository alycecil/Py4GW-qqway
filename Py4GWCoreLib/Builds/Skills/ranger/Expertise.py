from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib import Routines

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Expertise", "should_hold_tao_for_heroic_refrain"]


def should_hold_tao_for_heroic_refrain(player_id: int) -> bool:
    """True while re-shouting TaO! would starve a Heroic Refrain refresh.

    Heroic Refrain refreshes to full length whenever a shout ends on you.
    When both are up and Refrain outlasts TaO!, holding the re-shout lets
    TaO! lapse, which refreshes Refrain, and TaO! is re-cast afterwards.
    Returns False when either effect is missing so normal upkeep applies.
    """
    from Py4GWCoreLib import GLOBAL_CACHE

    together_as_one_id: int = Skill.GetID("Together_as_one")
    heroic_refrain_id: int = Skill.GetID("Heroic_Refrain")

    tao_remaining = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, together_as_one_id) or 0)
    if tao_remaining <= 0:
        return False
    hr_remaining = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, heroic_refrain_id) or 0)
    return hr_remaining > tao_remaining


class Expertise:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region T
    def Together_as_One(self) -> BuildCoroutine:
        together_as_one_id: int = Skill.GetID("Together_as_one")

        if not self.build.IsSkillEquipped(together_as_one_id):
            return False

        if should_hold_tao_for_heroic_refrain(Player.GetAgentID()):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=together_as_one_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
