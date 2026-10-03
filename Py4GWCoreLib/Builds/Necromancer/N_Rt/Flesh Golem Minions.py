from Py4GWCoreLib import Agent, AgentArray, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate
from Py4GWCoreLib.enums_src.GameData_enums import Attribute


Animate_Flesh_Golem_ID = Skill.GetID("Animate_Flesh_Golem")
Animate_Bone_Minions_ID = Skill.GetID("Animate_Bone_Minions")
Death_Nova_ID = Skill.GetID("Death_Nova")
Barbs_ID = Skill.GetID("Barbs")
Weaken_Armor_ID = Skill.GetID("Weaken_Armor")
Necrosis_ID = Skill.GetID("Necrosis")
Foul_Feast_ID = Skill.GetID("Foul_Feast")
Signet_of_Lost_Souls_ID = Skill.GetID("Signet_of_Lost_Souls")

FLESH_GOLEM_MODEL_ID = 2795


def minion_cap_for_death_magic(death_magic_rank: int) -> int:
    """PvE controlled-minion cap for a Death Magic rank."""
    return 2 + max(0, int(death_magic_rank)) // 2


class Flesh_Golem_Minions(BuildMgr):
    """N/Rt minion army: golem first, minions to cap, nova the wounded.

    Carries OAhDUstnRANVBoBfClB3gJgVVA (Animate Flesh Golem, Animate Bone
    Minions, Death Nova, Barbs, Weaken Armor, Necrosis, Foul Feast, Signet
    of Lost Souls). Death Magic 12 / Soul Reaping 11 / Curses 6.

    Summon order follows the Minion Master controller pattern (PR #118):
    the one Flesh Golem first (it leaves its own corpse when it dies),
    then Bone Minions pairs until the Death-rank cap is filled
    (2 + rank // 2 = 8 at rank 12). Raising runs in and out of combat so
    the army is already standing when the fight starts.

    Behind the army: Death Nova on hurt minions (AoE + poison when they
    fall), Barbs so every minion hit lands harder, Weaken Armor cracked
    armor over clusters, Foul Feast support, Necrosis spike on afflicted
    foes, and Signet of Lost Souls for energy off sub-50% targets.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Flesh Golem Minions",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Ritualist,
            template_code="OAhDUstnRANVBoBfClB3gJgVVA",
            required_skills=[
                Animate_Flesh_Golem_ID,
                Animate_Bone_Minions_ID,
                Death_Nova_ID,
            ],
            optional_skills=[
                Barbs_ID,
                Weaken_Armor_ID,
                Necrosis_ID,
                Foul_Feast_ID,
                Signet_of_Lost_Souls_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills(
            [
                Animate_Flesh_Golem_ID,
                Animate_Bone_Minions_ID,
                Death_Nova_ID,
                Barbs_ID,
                Weaken_Armor_ID,
                Necrosis_ID,
                Foul_Feast_ID,
                Signet_of_Lost_Souls_ID,
            ]
        )
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _death_magic_rank(self) -> int:
        attributes = Agent.GetAttributes(Player.GetAgentID()) or []
        death_magic = next(
            (
                attribute
                for attribute in attributes
                if int(getattr(attribute, "attribute_id", -1)) == int(Attribute.DeathMagic)
            ),
            None,
        )
        return int(getattr(death_magic, "level", 0) or 0)

    def _controlled_minion_count(self) -> int:
        player_agent_id = Player.GetAgentID()
        counts = [
            max(0, int(minion_count))
            for agent_id, minion_count in (Player.GetControlledMinions() or [])
            if int(agent_id) == int(player_agent_id)
        ]
        return max(counts, default=0)

    def _has_owned_flesh_golem(self) -> bool:
        player_agent_id = Player.GetAgentID()
        for minion_agent_id in AgentArray.GetMinionArray() or []:
            if not Agent.IsAlive(minion_agent_id):
                continue
            if Agent.GetOwnerID(minion_agent_id) != player_agent_id:
                continue
            if Agent.GetPlayerNumber(minion_agent_id) == FLESH_GOLEM_MODEL_ID:
                return True
        return False

    def _cast_barbs(self):
        """Physical-taken hex so minion hits land harder. Skips targets
        already carrying it."""
        if not self.IsSkillEquipped(Barbs_ID):
            return False

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Nearby.value,
            preferred_condition=lambda agent_id: not Routines.Checks.Agents.HasEffect(agent_id, Barbs_ID),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False
        if Routines.Checks.Agents.HasEffect(target_agent_id, Barbs_ID):
            return False

        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Barbs_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_necrosis(self):
        """Bonus damage only against a hexed or conditioned foe — lowest HP
        first so the spike finishes something."""
        if not self.IsSkillEquipped(Necrosis_ID):
            return False
        if not self.CanCastSkillID(Necrosis_ID):
            return False

        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
        )
        if not enemy_array:
            return False
        target_agent_id = min(enemy_array, key=lambda agent_id: Agent.GetHealth(agent_id))

        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Necrosis_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        minion_count = self._controlled_minion_count()
        desired_cap = minion_cap_for_death_magic(self._death_magic_rank())
        has_corpse = bool(Routines.Agents.GetExploitableCorpses(Range.Spellcast.value))

        # 1. The one golem first — it leaves its own corpse behind.
        if (
            self.IsSkillEquipped(Animate_Flesh_Golem_ID)
            and not self._has_owned_flesh_golem()
            and has_corpse
            and (yield from self.skills.Necromancer.DeathMagic.Animate_Flesh_Golem())
        ):
            return True

        # 2. Minion pairs until the Death-rank cap is filled.
        if (
            self.IsSkillEquipped(Animate_Bone_Minions_ID)
            and has_corpse
            and minion_count < desired_cap
            and (yield from self.skills.Necromancer.DeathMagic.Animate_Bone_Minions())
        ):
            return True

        # 3. Nova hurt minions (detonates AoE + poison when they fall).
        if self.IsSkillEquipped(Death_Nova_ID) and (
            yield from self.skills.Necromancer.DeathMagic.Death_Nova()
        ):
            return True

        if not self.IsInAggro():
            return False

        # 4. Hexes: minion-damage amp, then cracked armor, then support.
        if (yield from self._cast_barbs()):
            return True

        if self.IsSkillEquipped(Weaken_Armor_ID) and (
            yield from self.skills.Necromancer.Curses.Weaken_Armor()
        ):
            return True

        if self.IsSkillEquipped(Foul_Feast_ID) and (
            yield from self.skills.Necromancer.SoulReaping.Foul_Feast()
        ):
            return True

        # 5. Spike and energy off afflicted / sub-50% foes.
        if (yield from self._cast_necrosis()):
            return True

        if self.IsSkillEquipped(Signet_of_Lost_Souls_ID) and (
            yield from self.skills.Necromancer.SoulReaping.Signet_of_Lost_Souls()
        ):
            return True

        return False
