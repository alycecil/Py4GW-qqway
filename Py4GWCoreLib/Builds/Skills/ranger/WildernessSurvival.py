from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["WildernessSurvival"]


class WildernessSurvival:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region W
    def Winter(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, SpiritModelID

        winter_id: int = Skill.GetID("Winter")

        if not self.build.IsSkillEquipped(winter_id):
            return False

        # No aggro gate: Winter is always-up upkeep so it is already in
        # place before aggro. Skip only while an owned Winter spirit exists.
        self_agent_id = self.build._resolve_self_agent_id()
        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Spirit.value)
        if any(
            Agent.IsAlive(spirit_id)
            and Agent.IsSpawned(spirit_id)
            and Agent.GetOwnerID(spirit_id) == self_agent_id
            and Agent.GetPlayerNumber(spirit_id) == SpiritModelID.WINTER.value
            for spirit_id in spirits
        ):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=winter_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

