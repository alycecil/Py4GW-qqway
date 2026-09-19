from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Range
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Icy_Veins_ID = Skill.GetID("Icy_Veins")
Necrosis_ID = Skill.GetID("Necrosis")
Foul_Feast_ID = Skill.GetID("Foul_Feast")
Signet_of_Lost_Souls_ID = Skill.GetID("Signet_of_Lost_Souls")
Technobabble_ID = Skill.GetID("Technobabble")
Signet_of_Corruption_ID = Skill.GetID("Signet_of_Corruption")
Putrid_Explosion_ID = Skill.GetID("Putrid_Explosion")
Putrid_Bile_ID = Skill.GetID("Putrid_Bile")


class Icy_Veins_Necrosis(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Icy Veins Necrosis",
            required_primary=Profession.Necromancer,
            required_secondary=Profession(0),  # Any
            template_code="OABCUsxUbpn3NYC4XgCYNTVF",
            required_skills=[
                Icy_Veins_ID,
                Necrosis_ID,
                Foul_Feast_ID,
                Signet_of_Lost_Souls_ID,
            ],
            optional_skills=[
                Technobabble_ID,
                Signet_of_Corruption_ID,
                Putrid_Explosion_ID,
                Putrid_Bile_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)
        # agent_id -> monotonic timestamp of our last Icy Veins cast.
        self._icy_veins_cast_cache: dict[int, float] = {}
        # agent_id -> monotonic timestamp of our last Putrid Bile cast.
        self._putrid_bile_cast_cache: dict[int, float] = {}

    def _icy_veins(self):
        # Elite: single-target nuke that detonates an AoE if the target dies
        # while hexed. Anchor the lowest-HP enemy in spellcast range so the
        # detonation actually goes off. Recently-hexed foes are tracked in a
        # local 35s ledger (the hex's max duration) instead of an effect
        # check, so a refresh lands as the old hex expires rather than
        # stacking or stalling on stale reads.
        import time

        if not self.IsSkillEquipped(Icy_Veins_ID):
            return False
        if not self.IsInAggro():
            return False

        now = time.monotonic()
        self._icy_veins_cast_cache = {
            agent_id: cast_ts
            for agent_id, cast_ts in self._icy_veins_cast_cache.items()
            if now - cast_ts < 35.0
        }

        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: agent_id not in self._icy_veins_cast_cache,
        )
        if not enemy_array:
            return False
        target_agent_id = min(enemy_array, key=lambda agent_id: Agent.GetHealth(agent_id))

        cast_result = yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Icy_Veins_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        )
        if cast_result:
            self._icy_veins_cast_cache[target_agent_id] = time.monotonic()
            return True
        return False

    def _putrid_bile(self):
        # Setup hex: the foe detonates an AoE on death while hexed. Same
        # ledger logic as Icy Veins — lowest-HP uncached enemy in spellcast
        # range — but a 20s window (Bile's max duration) and a lower rotation
        # slot than the elite, so it never steals the opening nuke's target.
        import time

        if not self.IsSkillEquipped(Putrid_Bile_ID):
            return False
        if not self.IsInAggro():
            return False

        now = time.monotonic()
        self._putrid_bile_cast_cache = {
            agent_id: cast_ts
            for agent_id, cast_ts in self._putrid_bile_cast_cache.items()
            if now - cast_ts < 20.0
        }

        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: agent_id not in self._putrid_bile_cast_cache,
        )
        if not enemy_array:
            return False
        target_agent_id = min(enemy_array, key=lambda agent_id: Agent.GetHealth(agent_id))

        cast_result = yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Putrid_Bile_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        )
        if cast_result:
            self._putrid_bile_cast_cache[target_agent_id] = time.monotonic()
            return True
        return False

    def _necrosis(self):
        # Bonus damage only against a hexed or conditioned foe. Prefer the
        # lowest-HP such enemy in spellcast range; without hexes/conditions
        # on the field this holds (no point firing it clean).
        if not self.IsSkillEquipped(Necrosis_ID):
            return False
        if not self.IsInAggro():
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

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Necrosis_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _signet_of_corruption(self):
        # Free AoE + energy per hexed/conditioned foe hit. Anchor the biggest
        # cluster around a hexed or conditioned foe; hold on clean fields.
        if not self.IsSkillEquipped(Signet_of_Corruption_ID):
            return False
        if not self.IsInAggro():
            return False

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Nearby.value,
            preferred_condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Signet_of_Corruption_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # Support first: move conditions off allies (shared helper resolves
        # the conditioned ally via the skill's own targeting data).
        if self.IsSkillEquipped(Foul_Feast_ID) and (yield from self.skills.Necromancer.SoulReaping.Foul_Feast()):
            return True

        if not self.IsInAggro():
            return False

        # Elite nuke on the most killable target so the detonation pays off.
        if self.IsSkillEquipped(Icy_Veins_ID) and (yield from self._icy_veins()):
            return True

        # Corpse engine: seed Bile on the dying, detonate corpses into packs.
        if self.IsSkillEquipped(Putrid_Bile_ID) and (yield from self._putrid_bile()):
            return True

        if self.IsSkillEquipped(Putrid_Explosion_ID) and (yield from self.skills.Necromancer.DeathMagic.Putrid_Explosion()):
            return True

        # Condition/hex payoffs, cheapest last.
        if self.IsSkillEquipped(Necrosis_ID) and (yield from self._necrosis()):
            return True

        if self.IsSkillEquipped(Signet_of_Corruption_ID) and (yield from self._signet_of_corruption()):
            return True

        if self.IsSkillEquipped(Technobabble_ID) and (yield from self.skills.Any.PvE.Technobabble()):
            return True

        # Idle energy/HP top-off: free whenever a sub-50% foe exists and
        # nothing above wants the tick.
        if self.IsSkillEquipped(Signet_of_Lost_Souls_ID) and (yield from self.skills.Necromancer.SoulReaping.Signet_of_Lost_Souls()):
            return True

        return False
