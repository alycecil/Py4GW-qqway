from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


# Primary template: OASjUohK5Sl1xTSTTO+gVBeeXMA
# Variant:          OASjUohK5Sl1aiSTTOjTVBeeXMA
# Rt/N — Death Magic 10 / Restoration Magic 10 / Spawning Power 11
# Common core: Weapons of Three Forges (elite), Mend Body and Soul,
#   Spirit Light, Animate Bone Minions, Signet of Corruption, Flesh of My Flesh
# Variant slots: Wielder's Boon <-> Mending Grip, Vampirism <-> Life
# Both variants match this one build via required + optional skills.
Weapons_of_Three_Forges_ID = Skill.GetID("Weapons_of_Three_Forges")
Mend_Body_and_Soul_ID = Skill.GetID("Mend_Body_and_Soul")
Spirit_Light_ID = Skill.GetID("Spirit_Light")
Animate_Bone_Minions_ID = Skill.GetID("Animate_Bone_Minions")
Signet_of_Corruption_ID = Skill.GetID("Signet_of_Corruption")
Flesh_of_My_Flesh_ID = Skill.GetID("Flesh_of_My_Flesh")
Wielders_Boon_ID = Skill.GetID("Wielders_Boon")
Mending_Grip_ID = Skill.GetID("Mending_Grip")
Vampirism_ID = Skill.GetID("Vampirism")
Life_ID = Skill.GetID("Life")


class Three_Forges_Minion_Healer(BuildMgr):
    """
    HeroAI Rt/N support: elite weapon-spell aura, minion engine, heals, rez.

    Priority chain (first hit wins the tick):
    1. Rez — Flesh of My Flesh on a dead ally in spellcast range.
    2. Emergency heals — Spirit Light / Mend Body and Soul at low thresholds.
    3. Elite upkeep — Weapons of Three Forges once the party nears combat,
       then on recharge while fighting. Targets a non-weapon-spelled ally;
       the aura covers non-spirit allies in earshot, minions included.
    4. Minion engine — Animate Bone Minions whenever a corpse is available
       (corpse reservation lives in the shared helper). Raised in or out of
       combat so the army is already standing when the fight starts.
    5. Weapon-spell synergy heals — Wielder's Boon / Mending Grip, whichever
       variant is equipped.
    6. Routine heals — Mend Body and Soul, Spirit Light, spirit upkeep
       (Life / Vampirism, whichever variant is equipped).
    7. Damage — Signet of Corruption on a hexed/conditioned cluster, free
       AoE plus energy per afflicted foe hit.

    Everything after the rez is guarded by IsSkillEquipped, so both template
    variants run on this one handler.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Three Forges Minion Healer",
            required_primary=Profession.Ritualist,
            required_secondary=Profession.Necromancer,
            template_code="OASjUohK5Sl1xTSTTO+gVBeeXMA",
            required_skills=[
                Weapons_of_Three_Forges_ID,
                Mend_Body_and_Soul_ID,
                Spirit_Light_ID,
                Animate_Bone_Minions_ID,
                Signet_of_Corruption_ID,
                Flesh_of_My_Flesh_ID,
            ],
            optional_skills=[
                Wielders_Boon_ID,
                Mending_Grip_ID,
                Vampirism_ID,
                Life_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _weapons_of_three_forges(self):
        # Elite upkeep: prebuff as the party nears combat, refresh on recharge
        # while fighting. CloseToAggro covers both the approach and the fight,
        # so one gate handles the user's "nears combat, then on recharge" rule.
        # Targeting mirrors Xinraes_Weapon: a non-weapon-spelled ally in
        # spellcast range, preferring whoever is about to take damage.
        from Py4GWCoreLib.HeroAI.targeting import TargetAllyWeaponSpell

        if not self.IsSkillEquipped(Weapons_of_Three_Forges_ID):
            return False
        if not (self.IsInAggro() or self.IsCloseToAggro()):
            return False

        target_agent_id = TargetAllyWeaponSpell(Weapons_of_Three_Forges_ID, Range.Spellcast.value)
        if not target_agent_id:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            Weapons_of_Three_Forges_ID,
            target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _flesh_of_my_flesh(self):
        # Rez outweighs everything else. Costs half our HP; the heal rotation
        # below tops us back up. No aggro gate — wipes get rezzed OOC too.
        if not self.IsSkillEquipped(Flesh_of_My_Flesh_ID):
            return False

        dead_ally_id = Routines.Agents.GetDeadAlly(Range.Spellcast.value) or 0
        if not dead_ally_id:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Flesh_of_My_Flesh_ID,
            target_agent_id=dead_ally_id,
            log=False,
            aftercast_delay=250,
        ))

    def _signet_of_corruption(self):
        # Free AoE + energy per hexed/conditioned foe hit. Anchor the biggest
        # cluster around an afflicted foe; hold on clean fields.
        if not self.IsSkillEquipped(Signet_of_Corruption_ID):
            return False
        if not self.IsInAggro():
            return False

        from Py4GWCoreLib.Agent import Agent

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

        # 1. Rez first.
        if (yield from self._flesh_of_my_flesh()):
            return True

        # 2. Emergency heals preempt buffs.
        if (yield from self.skills.Ritualist.RestorationMagic.Spirit_Light(health_threshold=0.30)):
            return True

        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(health_threshold=0.40)):
            return True

        # 3. Elite upkeep — before minions so the aura is up when they rise.
        if (yield from self._weapons_of_three_forges()):
            return True

        # 4. Minion engine — any available corpse, in or out of combat.
        if self.IsSkillEquipped(Animate_Bone_Minions_ID) and (
            yield from self.skills.Necromancer.DeathMagic.Animate_Bone_Minions()
        ):
            return True

        # 5. Weapon-spell synergy heals (one per variant).
        if self.IsSkillEquipped(Wielders_Boon_ID) and (
            yield from self.skills.Ritualist.RestorationMagic.Wielders_Boon()
        ):
            return True

        if self.IsSkillEquipped(Mending_Grip_ID) and (
            yield from self.skills.Ritualist.RestorationMagic.Mending_Grip()
        ):
            return True

        # 6. Spirit upkeep (one per variant; aggro/existence gates inside).
        if self.IsSkillEquipped(Life_ID) and (
            yield from self.skills.Ritualist.RestorationMagic.Life()
        ):
            return True

        if self.IsSkillEquipped(Vampirism_ID) and (
            yield from self.skills.Any.PvE.Vampirism()
        ):
            return True

        # Damaged tier before combat-only damage.
        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(health_threshold=0.75)):
            return True

        if (yield from self.skills.Ritualist.RestorationMagic.Spirit_Light()):
            return True

        # 7. Free damage once the party is healthy.
        if (yield from self._signet_of_corruption()):
            return True

        # Preventive tier, last.
        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(health_threshold=0.85)):
            return True

        return False
