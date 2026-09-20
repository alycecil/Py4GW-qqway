from __future__ import annotations

from Py4GWCoreLib import AgentArray, BuildMgr, Profession, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills import SkillsTemplate
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


MASOCHISM_ID = Skill.GetID("Masochism")
SOUL_TAKER_ID = Skill.GetID("Soul_Taker")
TWIN_MOON_SWEEP_ID = Skill.GetID("Twin_Moon_Sweep")
EREMITES_ATTACK_ID = Skill.GetID("Eremites_Attack")
STAGGERING_FORCE_ID = Skill.GetID("Staggering_Force")
DUST_CLOAK_ID = Skill.GetID("Dust_Cloak")
AURA_OF_THORNS_ID = Skill.GetID("Aura_of_Thorns")
DRUNKEN_MASTER_ID = Skill.GetID("Drunken_Master")
I_AM_UNSTOPPABLE_ID = Skill.GetID("I_Am_Unstoppable")
LIGHTBRINGER_SIGNET_ID = Skill.GetID("Lightbringer_Signet")
SIGNET_OF_CORRUPTION_ID = Skill.GetID("Signet_of_Corruption")
SIGNET_OF_CORRUPTION_KURZICK_ID = Skill.GetID("Signet_of_Corruption_kurzick")
SIGNET_OF_CORRUPTION_LUXON_ID = Skill.GetID("Signet_of_Corruption_luxon")

# Flash-enchant flex slots. Any equipped subset feeds the scythe attacks;
# the bar no longer requires a specific pair.
FLASH_ENCHANT_IDS = (DUST_CLOAK_ID, STAGGERING_FORCE_ID, AURA_OF_THORNS_ID)

# Faction variants share one flex slot: the bar carries at most one of them.
SIGNET_OF_CORRUPTION_IDS = (
    SIGNET_OF_CORRUPTION_ID,
    SIGNET_OF_CORRUPTION_KURZICK_ID,
    SIGNET_OF_CORRUPTION_LUXON_ID,
)


class Soul_Taker_Scythe(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Soul Taker Scythe",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Dervish,
            template_code="OApjYwpzKTbhf1PXNXaXZXqi0kA",
            required_skills=[
                MASOCHISM_ID,
                SOUL_TAKER_ID,
                TWIN_MOON_SWEEP_ID,
                EREMITES_ATTACK_ID,
                DRUNKEN_MASTER_ID,
            ],
            # Flex slots: the bar matches without any of these. Any equipped
            # flash enchant feeds the scythe attacks, and any equipped signet
            # is used for energy management.
            optional_skills=[
                STAGGERING_FORCE_ID,
                DUST_CLOAK_ID,
                AURA_OF_THORNS_ID,
                I_AM_UNSTOPPABLE_ID,
                LIGHTBRINGER_SIGNET_ID,
                SIGNET_OF_CORRUPTION_ID,
                SIGNET_OF_CORRUPTION_KURZICK_ID,
                SIGNET_OF_CORRUPTION_LUXON_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skillbook: SkillsTemplate = SkillsTemplate(self)

    def _get_player_contact_count(self) -> int:
        player_x, player_y = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Adjacent.value)
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsValid(agent_id) and not Agent.IsDead(agent_id),
        )
        return len(enemy_array or [])

    def _is_in_melee_contact(self, target_agent_id: int) -> bool:
        if not target_agent_id or not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return False
        return Utils.Distance(Player.GetXY(), Agent.GetXY(target_agent_id)) <= Range.Adjacent.value

    def _auto_attack_cluster(self):
        return (yield from self.AutoAttack(target_type="EnemyClustered"))

    def _get_equipped_flash_enchant_ids(self) -> tuple[int, ...]:
        return tuple(skill_id for skill_id in FLASH_ENCHANT_IDS if self.IsSkillEquipped(skill_id))

    def _signet_of_corruption(self, max_self_energy_pct: float = 0.70):
        # Free AoE + energy per hexed/conditioned foe hit. The flash enchants
        # and scythe attacks spread conditions, so this pays out once the
        # spike is rolling. Energy-gated: only fires when the bar needs fuel.
        signet_id = next(
            (skill_id for skill_id in SIGNET_OF_CORRUPTION_IDS if self.IsSkillEquipped(skill_id)),
            0,
        )
        if not signet_id:
            return False
        if not self.IsInAggro():
            return False
        if float(Agent.GetEnergy(Player.GetAgentID()) or 0.0) >= max_self_energy_pct:
            return False

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Nearby.value,
            preferred_condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=signet_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _lightbringer_signet(self, max_self_energy_pct: float = 0.85):
        # Free energy, but only inside the area of a demonic servant of
        # Abaddon. Energy-gated so a fizzle outside demon areas costs at most
        # one cast per recharge cycle.
        if not self.IsSkillEquipped(LIGHTBRINGER_SIGNET_ID):
            return False
        if not self.IsInAggro():
            return False
        if float(Agent.GetEnergy(Player.GetAgentID()) or 0.0) >= max_self_energy_pct:
            return False

        return (yield from self.CastSkillID(
            skill_id=LIGHTBRINGER_SIGNET_ID,
            log=False,
            aftercast_delay=250,
        ))

    def _run_local_skill_logic(self):
        if not (self.IsInAggro() or self.IsCloseToAggro()):
            return False

        contact_count = self._get_player_contact_count()

        if self.IsSkillEquipped(I_AM_UNSTOPPABLE_ID) and (
            yield from self.skillbook.Any.NoAttribute.I_Am_Unstoppable(
                contact_count=contact_count,
                min_adjacent_enemies=2,
                refresh_window_ms=1000,
                aftercast_delay=150,
            )
        ):
            return True

        if self.IsSkillEquipped(MASOCHISM_ID) and (
            yield from self.skillbook.Necromancer.SoulReaping.Masochism()
        ):
            return True

        if (yield from self.skillbook.Necromancer.SoulReaping.Soul_Taker(refresh_window_ms=2000)):
            return True

        if (yield from self.skillbook.Any.PvE.Drunken_Master(refresh_window_ms=2000)):
            return True

        target_agent_id = self.current_target_id
        if not self._is_in_melee_contact(target_agent_id):
            if (yield from self._auto_attack_cluster()):
                return True
            target_agent_id = self.current_target_id

        target_cluster_size = 0
        if target_agent_id and Agent.IsValid(target_agent_id) and not Agent.IsDead(target_agent_id):
            target_cluster_size = 1 + Routines.Targeting.CountNearbyEnemies(
                target_agent_id,
                Range.Adjacent.value,
            )

        cluster_size = max(target_cluster_size, contact_count)

        # Compress damage by reapplying flash enchants during the spike window
        # when energy is comfortable, otherwise just keep them maintained.
        # Any equipped subset of the flex slots is maintained here.
        flash_chain_floor = 0.35 if cluster_size >= 2 else 0.15

        for flash_enchant_id, flash_cast in (
            (DUST_CLOAK_ID, self.skillbook.Dervish.EarthPrayers.Dust_Cloak),
            (STAGGERING_FORCE_ID, self.skillbook.Dervish.EarthPrayers.Staggering_Force),
            (AURA_OF_THORNS_ID, self.skillbook.Dervish.EarthPrayers.Aura_of_Thorns),
        ):
            if self.IsSkillEquipped(flash_enchant_id) and (
                yield from flash_cast(
                    refresh_window_ms=1200,
                    min_self_energy_pct=flash_chain_floor,
                )
            ):
                return True

        if (yield from self._signet_of_corruption()):
            return True

        if (yield from self._lightbringer_signet()):
            return True

        if not self._is_in_melee_contact(target_agent_id):
            if (yield from self._auto_attack_cluster()):
                return True
            return False

        active_flash_enchants = self.skillbook.Dervish.ScytheMastery.Count_Active_Dervish_Enchantments(
            self._get_equipped_flash_enchant_ids()
        )

        # Both scythe attacks consume a Dervish enchantment for their premium
        # effect. Preserve that removal logic explicitly:
        # - with 2 enchants up, fire Twin first then Eremite so both consume one
        # - with only 1 enchant up, spend it on Eremite for blob AoE when the
        #   player is already in the middle of a pack; otherwise Twin still gets
        #   the better single-target compression.
        twin_ready = self.CanCastSkillID(TWIN_MOON_SWEEP_ID)
        prefer_eremites_first = (
            not twin_ready
            or (active_flash_enchants == 1 and cluster_size >= 3)
        )
        attack_order = (
            (EREMITES_ATTACK_ID, TWIN_MOON_SWEEP_ID)
            if prefer_eremites_first
            else (TWIN_MOON_SWEEP_ID, EREMITES_ATTACK_ID)
        )

        for attack_skill_id in attack_order:
            if not self.IsSkillEquipped(attack_skill_id):
                continue

            if attack_skill_id == EREMITES_ATTACK_ID:
                if active_flash_enchants <= 0 and cluster_size < 2:
                    continue
                min_energy_pct = 0.10 if cluster_size < 2 else 0.0
                cast_skill = self.skillbook.Dervish.ScytheMastery.Eremites_Attack
            else:
                min_energy_pct = 0.0
                if active_flash_enchants <= 0:
                    min_energy_pct = max(min_energy_pct, 0.20)
                if cluster_size < 2:
                    min_energy_pct = max(min_energy_pct, 0.15)
                cast_skill = self.skillbook.Dervish.ScytheMastery.Twin_Moon_Sweep

            if (
                yield from cast_skill(
                    target_agent_id,
                    cluster_size=cluster_size,
                    min_self_energy_pct=min_energy_pct,
                )
            ):
                return True

            active_flash_enchants = self.skillbook.Dervish.ScytheMastery.Count_Active_Dervish_Enchantments(
                self._get_equipped_flash_enchant_ids()
            )

        if (yield from self._auto_attack_cluster()):
            return True

        return False
