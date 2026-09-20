from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Range
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Aura_of_Restoration_ID = Skill.GetID("Aura_of_Restoration")
Ether_Renewal_ID = Skill.GetID("Ether_Renewal")
Balthazars_Spirit_ID = Skill.GetID("Balthazars_Spirit")
Life_Attunement_ID = Skill.GetID("Life_Attunement")
Burning_Speed_ID = Skill.GetID("Burning_Speed")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Infuse_Health_ID = Skill.GetID("Infuse_Health")


class Ether_Renewal_Speedrun(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Ether Renewal Speedrun",
            required_primary=Profession.Elementalist,
            required_secondary=Profession.Monk,
            template_code="OgNDwcPPTkE3Mwl1C0CyDxD0DA",
            required_skills=[
                Aura_of_Restoration_ID,
                Ether_Renewal_ID,
                Balthazars_Spirit_ID,
                Burning_Speed_ID,
            ],
            # NOTE: Life Bond is deliberately NOT listed here. Supported
            # skills are masked from the HeroAI fallback, and Life Bond has
            # no local logic — listing it would orphan it. Unlisted, the
            # fallback keeps maintaining it on allies out of combat as today.
            optional_skills=[
                Infuse_Health_ID,
                Life_Attunement_ID,
                Air_of_Superiority_ID,
            ],
        )

        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _life_attunement_self_upkeep(self):
        # The one enchantment that is always maintained on self, in and out
        # of combat, and never cancelled by the zero-energy failsafe.
        not_has_life_attunement = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), Life_Attunement_ID)

        if not self.IsSkillEquipped(Life_Attunement_ID):
            return False
        if not not_has_life_attunement():
            return False

        return (yield from self.CastSkillID(
            skill_id=Life_Attunement_ID,
            extra_condition=not_has_life_attunement,
            log=False,
            aftercast_delay=250,
            target_agent_id=Player.GetAgentID(),
        ))

    def _balthazars_spirit_upkeep(self):
        # Core energy engine: Balthazar's Spirit on self pays energy whenever
        # an ally takes damage; frontliners get it too since they are the
        # ones constantly taking hits. Maintain in and out of combat.
        #
        # NOTE: the generic custom data tags this skill AllyMartialMelee, so
        # BuildMgr._validate_target_for_skill_cast vetoes a self-cast from a
        # caster monk and CastSkillID silently returns False. The game itself
        # allows casting ally enchantments on self (manually verified), so
        # the self-cast goes through the skill bar directly with
        # CanCastSkillID as the gate. Melee allies pass validation, so they
        # use the standard path.
        if not self.IsSkillEquipped(Balthazars_Spirit_ID):
            return False

        player_id = Player.GetAgentID()
        not_has_balthazars_self = lambda: not Routines.Checks.Effects.HasBuff(player_id, Balthazars_Spirit_ID)

        # Tier 1: self, via direct bar cast (see NOTE above). The attempt is
        # verified (buff must read back afterwards) and backed off for 10s:
        # an unverified cast must never retry every tick and starve the rest
        # of the bar.
        import time

        last_self_attempt = float(getattr(self, "_balthazars_self_last_attempt", 0.0) or 0.0)
        if not_has_balthazars_self() and time.monotonic() - last_self_attempt >= 10.0:
            if self.CanCastSkillID(Balthazars_Spirit_ID, extra_condition=not_has_balthazars_self):
                slot = self.GetEquippedSkillSlot(Balthazars_Spirit_ID)
                if 1 <= slot <= 8:
                    GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=player_id, aftercast_delay=250)
                    self._mark_local_cast_pending(250)
                    yield from Routines.Yield.wait(750)
                    self._balthazars_self_last_attempt = time.monotonic()
                    if Routines.Checks.Effects.HasBuff(player_id, Balthazars_Spirit_ID):
                        self.SetTickSuccess()
                        return True
                    # Unverified: fall through to the frontline tier instead
                    # of claiming the tick, so Infuse/Burning Speed still fire.

        # Tier 2: nearest melee ally in spellcast range missing it, covered
        # BEFORE the fight only. Mid-combat casts on moving frontliners
        # insta-cancel (range churn between scan and cast, plus interrupts
        # on the long activation), so prebuff while stacked instead of
        # chasing melee through the fight. Nearest-first so the target is
        # still in range when the cast resolves.
        if self.IsInAggro():
            return False
        ally_array = Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id) and agent_id != player_id,
        )
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsMelee(agent_id),
        )
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: not Routines.Checks.Effects.HasBuff(agent_id, Balthazars_Spirit_ID),
        )
        if not ally_array:
            return False
        player_x, player_y = Player.GetXY()
        target_agent_id = min(
            ally_array,
            key=lambda agent_id: (Agent.GetXY(agent_id)[0] - player_x) ** 2 + (Agent.GetXY(agent_id)[1] - player_y) ** 2,
        )

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Balthazars_Spirit_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _burning_speed_energy_spam(self):
        # Energy printer: each enchant cast on self while Ether Renewal is up
        # refunds energy, so spam the cheap Burning Speed to stay fueled.
        # Deliberately NOT gated on the burning condition or enemy proximity
        # (unlike the shared FireMagic helper, which serves Contagion): a
        # refresh cast still triggers Ether Renewal's refund. Never fires
        # without Ether Renewal up, in or out of combat.
        if not self.IsSkillEquipped(Burning_Speed_ID):
            return False
        has_ether_renewal = lambda: Routines.Checks.Effects.HasBuff(Player.GetAgentID(), Ether_Renewal_ID)
        if not has_ether_renewal():
            return False

        return (yield from self.CastSkillID(
            skill_id=Burning_Speed_ID,
            extra_condition=has_ether_renewal,
            log=False,
            aftercast_delay=250,
        ))

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        if (yield from self.skills.Elementalist.EnergyStorage.Aura_of_Restoration()):
            return True

        if self.IsSkillEquipped(Life_Attunement_ID) and (yield from self._life_attunement_self_upkeep()):
            return True

        if self.IsSkillEquipped(Balthazars_Spirit_ID) and (yield from self._balthazars_spirit_upkeep()):
            return True

        if (
            self.IsSkillEquipped(Air_of_Superiority_ID)
            and (self.IsInAggro() or self.IsCloseToAggro())
            and (yield from self.skills.Any.PvE.Air_of_Superiority())
        ):
            return True

        # Engine pre-load: maintain Ether Renewal out of combat too, so the
        # refund is already up at pull. Burning Speed spam stays gated behind
        # aggro below, so nothing burns energy out of combat.
        if (yield from self.skills.Elementalist.EnergyStorage.Ether_Renewal()):
            return True

        if not self.IsInAggro():
            return False

        self.UpdatePartyHealthMonitor(sample_interval_ms=150)

        if self.IsSkillEquipped(Infuse_Health_ID) and (yield from self.skills.Monk.HealingPrayers.Infuse_Health()):
            return True

        if self.IsSkillEquipped(Burning_Speed_ID) and (yield from self._burning_speed_energy_spam()):
            return True

        return False
