from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Blood_Bond_ID = Skill.GetID("Blood_Bond")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Finish_Him_ID = Skill.GetID("Finish_Him")
Weaken_Armor_ID = Skill.GetID("Weaken_Armor")
Enfeebling_Blood_ID = Skill.GetID("Enfeebling_Blood")
Ebon_Escape_ID = Skill.GetID("Ebon_Escape")
Blood_is_Power_ID = Skill.GetID("Blood_is_Power")
Flesh_of_My_Flesh_ID = Skill.GetID("Flesh_of_My_Flesh")


class Blood_Power_Support(BuildMgr):
    """N/Rt battery with support hexes, execute, and rez.

    Carries OAhDQqxHSDN7ixkfC2B0l3BXMA (Blood Bond, Ebon Vanguard Assassin
    Support, "Finish Him!", Weaken Armor, Enfeebling Blood, Ebon Escape,
    Blood is Power, Flesh of My Flesh). Blood Magic 10 / Soul Reaping 12 /
    Curses 8.

    Priority: rez a dead ally first, then feed energy with Blood is Power
    (the bar's actual job — safety floors and throttle live in the shared
    helper), then layer support hexes (Blood Bond lifesteal, Weaken Armor
    cracked armor, Enfeebling Blood weakness), then execute sub-50% foes
    with "Finish Him!", then assassin support damage. Ebon Escape is owned
    locally (OOC catch-up plus in-combat rescue to the safest ally) and
    blocked from the fallback so a rescue step never fires outside this
    priority chain.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Blood Power Support",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Ritualist,
            template_code="OAhDQqxHSDN7ixkfC2B0l3BXMA",
            required_skills=[
                Blood_is_Power_ID,
                Blood_Bond_ID,
                Finish_Him_ID,
            ],
            optional_skills=[
                Ebon_Vanguard_Assassin_Support_ID,
                Weaken_Armor_ID,
                Enfeebling_Blood_ID,
                Ebon_Escape_ID,
                Flesh_of_My_Flesh_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills(
            [
                Blood_Bond_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Finish_Him_ID,
                Weaken_Armor_ID,
                Enfeebling_Blood_ID,
                Ebon_Escape_ID,
                Blood_is_Power_ID,
                Flesh_of_My_Flesh_ID,
            ]
        )
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _flesh_of_my_flesh(self):
        # Rez outweighs everything, including the battery. No aggro gate —
        # wipes get rezzed OOC too.
        if not self.IsSkillEquipped(Flesh_of_My_Flesh_ID):
            return False

        dead_ally_id = Routines.Agents.GetDeadAlly(Range.Spellcast.value) or 0
        if not dead_ally_id:
            return False

        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Flesh_of_My_Flesh_ID,
                target_agent_id=dead_ally_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _ebon_escape_rescue(self):
        """In-combat shadow step to the safest ally when pressured. Kept
        local so the fallback cannot fire it outside this priority chain."""
        if not self.IsSkillEquipped(Ebon_Escape_ID):
            return False
        if not self.IsInAggro():
            return False

        player_id = Player.GetAgentID()
        player_x, player_y = Player.GetXY()
        adjacent_foes = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Adjacent.value) or []
        if Agent.GetHealth(player_id) >= 0.50 and len(adjacent_foes) < 3:
            return False

        allies = Routines.Agents.GetFilteredAllyArray(player_x, player_y, Range.Spellcast.value, other_ally=True) or []
        candidates = [aid for aid in allies if Agent.IsValid(aid) and Routines.Checks.Agents.IsAlive(aid)]
        if not candidates:
            return False

        def _enemies_near(agent_id: int) -> int:
            ally_x, ally_y = Agent.GetXY(agent_id)
            nearby = Routines.Agents.GetFilteredEnemyArray(ally_x, ally_y, Range.Earshot.value) or []
            return len(nearby)

        candidates.sort(key=lambda aid: (_enemies_near(aid), -Agent.GetHealth(aid)))
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Ebon_Escape_ID,
                target_agent_id=candidates[0],
                log=False,
                aftercast_delay=250,
            )
        )

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # 1. Rez first.
        if (yield from self._flesh_of_my_flesh()):
            return True

        # 2. OOC travel: step toward the party when lagging behind.
        if self.IsSkillEquipped(Ebon_Escape_ID) and (
            yield from self.skills.Any.PvE.Ebon_Escape_CatchUp()
        ):
            return True

        # 3. Battery — the bar's job. HP-safety floors and per-target
        # throttle live inside the shared helper.
        if (yield from self.skills.Necromancer.BloodMagic.Blood_is_Power()):
            return True

        # 4. Support hexes, most party-wide value first.
        if self.IsSkillEquipped(Blood_Bond_ID) and (
            yield from self.skills.Necromancer.BloodMagic.Blood_Bond()
        ):
            return True

        if self.IsSkillEquipped(Weaken_Armor_ID) and (
            yield from self.skills.Necromancer.Curses.Weaken_Armor()
        ):
            return True

        if self.IsSkillEquipped(Enfeebling_Blood_ID) and (
            yield from self.skills.Necromancer.Curses.Enfeebling_Blood()
        ):
            return True

        if not self.IsInAggro():
            return False

        # 5. Survival before kills.
        if (yield from self._ebon_escape_rescue()):
            return True

        # 6. Execute, then assassin damage.
        if self.IsSkillEquipped(Finish_Him_ID) and (
            yield from self.skills.Any.NoAttribute.Finish_Him()
        ):
            return True

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (
            yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()
        ):
            return True

        return False
