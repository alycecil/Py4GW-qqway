from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Range
from Py4GWCoreLib import Agent, Party, Player, Utils
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills.ranger.Expertise import should_hold_tao_for_heroic_refrain
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Run_as_One_ID = Skill.GetID("Run_as_One")
Whirlwind_Attack_ID = Skill.GetID("Whirlwind_Attack")
Distracting_Blow_ID = Skill.GetID("Distracting_Blow")
Soldiers_Strike_ID = Skill.GetID("Soldiers_Strike")
Apply_Poison_ID = Skill.GetID("Apply_Poison")
Together_as_one_ID = Skill.GetID("Together_as_one")
Save_Yourselves_ID = Skill.GetID("Save_Yourselves")
Comfort_Animal_ID = Skill.GetID("Comfort_Animal")


class Poison_Shout_Support(BuildMgr):
    """R/W pet-and-shout support: poison prep, party shouts, melee spikes.

    Carries OgEUULbeZMSrM7gFFfazGj1ie0GA (Run as One, Whirlwind Attack,
    Distracting Blow, Soldier's Strike, Apply Poison, "Together as One!",
    "Save Yourselves!", Comfort Animal). Tactics 5 / Beast Mastery 9 /
    Expertise 12 / Wilderness Survival 8.

    Shape mirrors the "Together as One" sibling in this folder: pet first
    (a dead pet guts the shouts' value), elite shout upkeep with the
    Heroic Refrain hold, stance upkeep in and out of combat, then melee
    spikes in aggro. New here: Apply Poison prep upkeep (poison on every
    physical hit feeds the whole bar) and "Save Yourselves!" spam on
    recharge while fighting. Soldier's Strike goes unblockable under our
    own shouts, so shout upkeep doubles as spike enabler.

    Melee attacks fire only in adjacent contact — no recharge wasted on
    out-of-range whiffs.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Poison Shout Support",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Warrior,
            template_code="OgEUULbeZMSrM7gFFfazGj1ie0GA",
            required_skills=[
                Together_as_one_ID,
                Save_Yourselves_ID,
                Apply_Poison_ID,
            ],
            optional_skills=[
                Run_as_One_ID,
                Whirlwind_Attack_ID,
                Distracting_Blow_ID,
                Soldiers_Strike_ID,
                Comfort_Animal_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _pet_is_alive(self, player_id: int) -> bool:
        pet_id = Party.Pets.GetPetID(player_id)
        return bool(pet_id) and bool(Agent.IsAlive(pet_id))

    def _ally_in_shout_range(self, player_id: int) -> bool:
        try:
            player_x, player_y = Player.GetXY()
            ally_array = Routines.Agents.GetFilteredAllyArray(
                player_x,
                player_y,
                Range.Earshot.value,
                other_ally=True,
            )
        except Exception:
            return False
        for ally_id in ally_array or []:
            ally_id = int(ally_id)
            if ally_id == 0 or ally_id == player_id:
                continue
            if Agent.IsPet(ally_id):
                continue
            if not Agent.IsAlive(ally_id):
                continue
            return True
        return False

    def _should_cast_comfort_animal(self, player_id: int) -> bool:
        pet_id = Party.Pets.GetPetID(player_id)
        if not pet_id:
            return False
        if not Agent.IsAlive(pet_id):
            return True
        return Agent.GetHealth(pet_id) < 0.30

    def _is_in_melee_contact(self, target_agent_id: int) -> bool:
        if not target_agent_id or not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return False
        return Utils.Distance(Player.GetXY(), Agent.GetXY(target_agent_id)) <= Range.Adjacent.value

    def _resolve_melee_target(self, skill_id: int, target_type: str) -> int:
        if not self.CanCastSkillID(skill_id):
            return 0
        target_acquired, _ = self._resolve_target(target_type)
        if not target_acquired:
            return 0
        target_agent_id = int(self.current_target_id or 0)
        if not self._is_in_melee_contact(target_agent_id):
            return 0
        return target_agent_id

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        player_id = Player.GetAgentID()
        close_to_aggro = self.IsInAggro() or self.IsCloseToAggro()

        # Pet first, in and out of combat — everything else loses value
        # with the pet dead.
        if (
            self.IsSkillEquipped(Comfort_Animal_ID)
            and self._should_cast_comfort_animal(player_id)
            and (
                yield from self.CastSkillID(
                    skill_id=Comfort_Animal_ID,
                    extra_condition=lambda: self._should_cast_comfort_animal(Player.GetAgentID()),
                    log=False,
                    aftercast_delay=250,
                )
            )
        ):
            return True

        # Elite shout: instant, no aftercast. Re-shout on recharge while an
        # ally is in earshot even when already up on us — the shout lands on
        # them too. Held while Heroic Refrain outlasts it so TaO! lapses and
        # refreshes Refrain to full length.
        if (
            self.IsSkillEquipped(Together_as_one_ID)
            and not should_hold_tao_for_heroic_refrain(player_id)
            and (
                not Routines.Checks.Agents.HasEffect(player_id, Together_as_one_ID)
                or self._ally_in_shout_range(player_id)
            )
            and (
                yield from self.CastSkillID(
                    skill_id=Together_as_one_ID,
                    log=False,
                    aftercast_delay=0,
                )
            )
        ):
            return True

        # Party armor on recharge while fighting. Party-wide effect, so no
        # ally-range check — but never OOC spam on a 4-6s duration.
        if (
            self.IsSkillEquipped(Save_Yourselves_ID)
            and close_to_aggro
            and (
                yield from self.CastSkillID(
                    skill_id=Save_Yourselves_ID,
                    log=False,
                    aftercast_delay=0,
                )
            )
        ):
            return True

        # Prep before the fight and refresh inside it.
        if (
            self.IsSkillEquipped(Apply_Poison_ID)
            and close_to_aggro
            and not Routines.Checks.Agents.HasEffect(player_id, Apply_Poison_ID)
            and (
                yield from self.CastSkillID(
                    skill_id=Apply_Poison_ID,
                    log=False,
                    aftercast_delay=250,
                )
            )
        ):
            return True

        # Stance upkeep in and out of combat, no aftercast hold.
        if (
            self.IsSkillEquipped(Run_as_One_ID)
            and not Routines.Checks.Agents.HasEffect(player_id, Run_as_One_ID)
            and (
                yield from self.CastSkillID(
                    skill_id=Run_as_One_ID,
                    log=False,
                    aftercast_delay=0,
                )
            )
        ):
            return True

        if not self.IsInAggro():
            return False

        # Unblockable under our own shouts — single-target spike.
        if self.IsSkillEquipped(Soldiers_Strike_ID):
            target_agent_id = self._resolve_melee_target(Soldiers_Strike_ID, "EnemyInjured")
            if target_agent_id and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Soldiers_Strike_ID,
                    target_agent_id=target_agent_id,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        # Interrupt on a casting foe in contact.
        if self.IsSkillEquipped(Distracting_Blow_ID):
            target_agent_id = self._resolve_melee_target(Distracting_Blow_ID, "EnemyClustered")
            if target_agent_id and Agent.IsCasting(target_agent_id) and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Distracting_Blow_ID,
                    target_agent_id=target_agent_id,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        if self.IsSkillEquipped(Whirlwind_Attack_ID) and (
            yield from self.skills.Warrior.NoAttribute.Whirlwind_Attack()
        ):
            return True

        return False
