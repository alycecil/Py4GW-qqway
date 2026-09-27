from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Range
from Py4GWCoreLib import Agent, Party, Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build


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
    250ms aftercast. Priority 3 is Never Rampage Alone, maintained the
    same way but only while the pet is alive. Priority 4 is Run as One,
    re-cast whenever its effect lapses. Everything else rides the
    HeroAI fallback.

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
        if not Routines.Checks.Skills.CanCast():
            return False

        player_id = Player.GetAgentID()

        if self.IsSkillEquipped(Comfort_Animal_ID) and self._should_cast_comfort_animal(player_id):
            return (
                yield from self.CastSkillID(
                    skill_id=Comfort_Animal_ID,
                    extra_condition=lambda: self._should_cast_comfort_animal(Player.GetAgentID()),
                    log=False,
                    aftercast_delay=250,
                )
            )

        if self.IsSkillEquipped(Together_as_one_ID):
            # Re-shout on recharge while a living ally is in earshot even
            # when the effect is already up on us: the shout also lands on
            # nearby party members, so holding a recharge wastes their buff.
            if not Routines.Checks.Agents.HasEffect(player_id, Together_as_one_ID) or self._ally_in_shout_range(
                player_id
            ):
                return (
                    yield from self.CastSkillID(
                        skill_id=Together_as_one_ID,
                        log=False,
                        aftercast_delay=0,
                    )
                )

        if self.IsSkillEquipped(Never_Rampage_Alone_ID):
            if self._pet_is_alive(player_id) and not Routines.Checks.Agents.HasEffect(
                player_id, Never_Rampage_Alone_ID
            ):
                return (
                    yield from self.CastSkillID(
                        skill_id=Never_Rampage_Alone_ID,
                        log=False,
                        aftercast_delay=250,
                    )
                )

        if self.IsSkillEquipped(Run_as_One_ID):
            if not Routines.Checks.Agents.HasEffect(player_id, Run_as_One_ID):
                return (
                    yield from self.CastSkillID(
                        skill_id=Run_as_One_ID,
                        log=False,
                        aftercast_delay=250,
                    )
                )

        return False
