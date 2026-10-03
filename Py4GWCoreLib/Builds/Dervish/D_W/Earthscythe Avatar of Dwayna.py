from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


# Template: OgGjkqrLrSmXvXZXaX7gPXNXRXA
# D/W — Scythe 10 / Earth Prayers 11 / Mysticism 10
# Bar: Sand Shards, Avatar of Dwayna (elite), Dust Cloak, Staggering Force,
#      Whirlwind Attack, Twin Moon Sweep, Eremite's Attack, Irresistible Sweep
Sand_Shards_ID = Skill.GetID("Sand_Shards")
Avatar_of_Dwayna_ID = Skill.GetID("Avatar_of_Dwayna")
Dust_Cloak_ID = Skill.GetID("Dust_Cloak")
Staggering_Force_ID = Skill.GetID("Staggering_Force")
Whirlwind_Attack_ID = Skill.GetID("Whirlwind_Attack")
Twin_Moon_Sweep_ID = Skill.GetID("Twin_Moon_Sweep")
Eremites_Attack_ID = Skill.GetID("Eremites_Attack")
Irresistible_Sweep_ID = Skill.GetID("Irresistible_Sweep")


class Earthscythe_Avatar_of_Dwayna(BuildMgr):
    """
    HeroAI melee earthscythe: maintain Avatar + three flash enchantments,
    then spend enchantments on scythe attacks in contact.

    Enchant engine: Sand Shards (adjacent splash on scythe hits), Dust Cloak
    (earth damage + Blind on end), Staggering Force (earth damage + Cracked
    Armor on end). Avatar of Dwayna (elite Form) converts damage to holy and
    heals allies in earshot whenever a Dervish enchantment is lost.

    Attack spending (all strip one Dervish enchantment for premium effect):
    - Irresistible Sweep: unblockable + stance removal + bonus damage
    - Eremites Attack: bonus damage + hits all adjacent foes
    - Twin Moon Sweep: heal + unblockable double-hit
    - Whirlwind Attack (Warrior, no enchant cost): target + adjacent AoE filler
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Earthscythe Avatar of Dwayna",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Warrior,
            template_code="OgGjkqrLrSmXvXZXaX7gPXNXRXA",
            required_skills=[
                Sand_Shards_ID,
                Avatar_of_Dwayna_ID,
                Dust_Cloak_ID,
                Staggering_Force_ID,
                Whirlwind_Attack_ID,
                Twin_Moon_Sweep_ID,
                Eremites_Attack_ID,
                Irresistible_Sweep_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _resolve_melee_target(self) -> int:
        target = int(self.current_target_id or Player.GetTargetID() or 0)
        if target and Agent.IsValid(target) and not Agent.IsDead(target):
            return target
        acquired, _ = self._resolve_target("EnemyClustered")
        if acquired:
            return int(self.current_target_id or 0)
        return 0

    def _is_in_melee_contact(self, target_agent_id: int) -> bool:
        if not target_agent_id or not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return False
        return Utils.Distance(Player.GetXY(), Agent.GetXY(target_agent_id)) <= Range.Adjacent.value

    def _cast_avatar_of_dwayna(self):
        # Elite Form: holy damage + party heal on each lost Dervish enchantment.
        # Has a 45s disable after it ends, so only refresh when actually missing.
        if not self.IsSkillEquipped(Avatar_of_Dwayna_ID):
            return False
        if not (self.IsInAggro() or self.IsCloseToAggro()):
            return False
        if Routines.Checks.Agents.HasEffect(Player.GetAgentID(), Avatar_of_Dwayna_ID):
            return False
        if (yield from self.CastSkillID(Avatar_of_Dwayna_ID, aftercast_delay=250)):
            return True
        return False

    def _cast_sand_shards(self):
        # Flash enchantment splash engine. Ends after 1-5 scythe hits, so the
        # buff check is the refresh signal — no shared helper covers it yet.
        if not self.IsSkillEquipped(Sand_Shards_ID):
            return False
        if not (self.IsInAggro() or self.IsCloseToAggro()):
            return False
        if Routines.Checks.Agents.HasEffect(Player.GetAgentID(), Sand_Shards_ID):
            return False
        if (yield from self.CastSkillID(Sand_Shards_ID, aftercast_delay=250)):
            return True
        return False

    def _cast_irresistible_sweep(self, target_agent_id: int):
        # No shared ScytheMastery helper covers this skill yet, so keep the
        # melee-contact + enchant-stock gating local. Strips one enchantment:
        # unblockable, removes a stance, bonus damage.
        if not self.IsSkillEquipped(Irresistible_Sweep_ID):
            return False
        if not self._is_in_melee_contact(target_agent_id):
            return False
        if self.skills.Dervish.ScytheMastery.Count_Active_Dervish_Enchantments() <= 0:
            return False
        if (yield from self.CastSkillIDAndRestoreTarget(
            Irresistible_Sweep_ID,
            target_agent_id,
            aftercast_delay=250,
        )):
            return True
        return False

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # 1. Elite Form upkeep — first so every later enchant-strip heals.
        if (yield from self._cast_avatar_of_dwayna()):
            return True

        # 2. Splash engine upkeep.
        if (yield from self._cast_sand_shards()):
            return True

        # 3-4. Shared flash-enchantment upkeep (aggro/close gating + refresh
        # window live inside the helpers).
        if self.IsSkillEquipped(Dust_Cloak_ID) and (
            yield from self.skills.Dervish.EarthPrayers.Dust_Cloak()
        ):
            return True

        if self.IsSkillEquipped(Staggering_Force_ID) and (
            yield from self.skills.Dervish.EarthPrayers.Staggering_Force()
        ):
            return True

        # Attacks need a live melee target.
        if not self.IsInAggro():
            return False

        target_agent_id = self._resolve_melee_target()
        if not target_agent_id:
            return False

        enchant_stock = self.skills.Dervish.ScytheMastery.Count_Active_Dervish_Enchantments()

        # Unblockable + stance strip while we have fuel. Gating lives inside.
        if enchant_stock > 0 and (
            yield from self._cast_irresistible_sweep(target_agent_id)
        ):
            return True

        # AoE compression: spends one enchantment to hit all adjacent foes.
        # Shared helper enforces melee contact; require fuel so the base hit
        # without the splash does not eat the bar's engine.
        if self.IsSkillEquipped(Eremites_Attack_ID) and (
            yield from self.skills.Dervish.ScytheMastery.Eremites_Attack(
                target_agent_id,
                require_dervish_enchantment=True,
            )
        ):
            return True

        # Sustain: heal + unblockable double-hit, also enchant-fueled.
        if self.IsSkillEquipped(Twin_Moon_Sweep_ID) and (
            yield from self.skills.Dervish.ScytheMastery.Twin_Moon_Sweep(
                target_agent_id,
                require_dervish_enchantment=True,
            )
        ):
            return True

        # Filler: no enchantment cost, target + adjacent AoE.
        if self.IsSkillEquipped(Whirlwind_Attack_ID) and (
            yield from self.skills.Warrior.NoAttribute.Whirlwind_Attack()
        ):
            return True

        return False
