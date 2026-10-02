from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Range
from Py4GWCoreLib import Agent, Party, Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills.ranger.Expertise import should_hold_tao_for_heroic_refrain
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Thrill_of_Victory_ID = Skill.GetID("Thrill_of_Victory")
Soldiers_Strike_ID = Skill.GetID("Soldiers_Strike")
Whirlwind_Attack_ID = Skill.GetID("Whirlwind_Attack")
Throw_Dirt_ID = Skill.GetID("Throw_Dirt")
Run_as_One_ID = Skill.GetID("Run_as_One")
Never_Rampage_Alone_ID = Skill.GetID("Never_Rampage_Alone")
Together_as_one_ID = Skill.GetID("Together_as_one")
Comfort_Animal_ID = Skill.GetID("Comfort_Animal")


class Together_as_One(BuildMgr):
    """R/W bar built around maintaining "Together as One!".

    Priority 1 is Comfort Animal: revive a dead pet or heal it below
    30% health, mirroring the R/A Tao dagger spammer. Without a living
    pet the shouts below lose their value, so this runs first. Priority
    2 is the elite shout: it is instant with no aftercast, so it fires
    with aftercast_delay=0 whenever it is not up. This deliberately
    bypasses the shared Expertise.Together_as_One helper, which waits
    250ms aftercast. The shout is held while Heroic Refrain outlasts it:
    letting TaO! lapse refreshes Refrain to full length, and TaO! is
    re-cast once it falls off. Priority 3 is Never Rampage Alone, re-cast on
    recharge while the pet is alive with aftercast_delay=0. Priority 4
    is Run as One, re-cast whenever its effect lapses. Priority 5 is
    the sword rotation
    (Thrill of Victory, Soldier's Strike, Whirlwind Attack, Throw Dirt),
    cast explicitly like the R/A Tao dagger spammer instead of riding
    the HeroAI fallback: the fallback gates Throw Dirt to martial-only
    targets and leaves the remaining attacks at the bottom of its
    generic priority order, so they effectively never fired.

    Carries OgEUURbeZcREFfa7goGrM8gj10GA (Thrill of Victory,
    Soldier's Strike, Whirlwind Attack, Throw Dirt, Run as One,
    Never Rampage Alone, "Together as One!", Comfort Animal).
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Together as One",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Warrior,
            template_code="OgEUURbeZcREFfa7goGrM8gj10GA",
            required_skills=[
                Together_as_one_ID,
                Never_Rampage_Alone_ID,
            ],
            optional_skills=[
                Thrill_of_Victory_ID,
                Soldiers_Strike_ID,
                Whirlwind_Attack_ID,
                Throw_Dirt_ID,
                Run_as_One_ID,
                Comfort_Animal_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)
        self.sword_target_type = "EnemyInjured"

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

    def _run_local_skill_logic(self):
        # NOTE: every block below chains with `and` so that a failed cast
        # attempt (e.g. skill still on recharge) falls through to the next
        # priority instead of aborting the whole chain with `return False`.
        if not Routines.Checks.Skills.CanCast():
            return False

        player_id = Player.GetAgentID()

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

        # Re-shout on recharge while a living ally is in earshot even
        # when the effect is already up on us: the shout also lands on
        # nearby party members, so holding a recharge wastes their buff.
        # Exception: while Heroic Refrain outlasts TaO!, hold the re-shout
        # (even for allies) so TaO! lapses and refreshes Refrain to full.
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

        if (
            self.IsSkillEquipped(Never_Rampage_Alone_ID)
            and self._pet_is_alive(player_id)
            and (
                yield from self.CastSkillID(
                    skill_id=Never_Rampage_Alone_ID,
                    log=False,
                    aftercast_delay=0,
                )
            )
        ):
            return True

        # Maintained in and out of combat: this block sits before the
        # aggro gate and re-casts whenever the stance lapses. No aftercast
        # hold so the refresh never delays the rest of the chain.
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

        if self.IsSkillEquipped(Thrill_of_Victory_ID) and (yield from self._cast_sword_attack(Thrill_of_Victory_ID)):
            return True
        if self.IsSkillEquipped(Soldiers_Strike_ID) and (yield from self._cast_sword_attack(Soldiers_Strike_ID)):
            return True
        if self.IsSkillEquipped(Whirlwind_Attack_ID) and (
            yield from self.skills.Warrior.NoAttribute.Whirlwind_Attack()
        ):
            return True
        if self.IsSkillEquipped(Throw_Dirt_ID) and (yield from self._cast_throw_dirt()):
            return True

        return False

    def _resolve_sword_target(self, skill_id: int, target_type: str) -> int:
        if not self.CanCastSkillID(skill_id):
            return 0
        target_acquired, _ = self._resolve_target(target_type)
        if not target_acquired:
            return 0
        return self.current_target_id

    def _cast_sword_attack(self, skill_id: int):
        target_agent_id = self._resolve_sword_target(skill_id, self.sword_target_type)
        if not target_agent_id:
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=skill_id,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_throw_dirt(self):
        target_agent_id = self._resolve_sword_target(Throw_Dirt_ID, "EnemyAttacking")
        if not target_agent_id:
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Throw_Dirt_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )
