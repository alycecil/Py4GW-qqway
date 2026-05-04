
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

# Import the new provider classes
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.intentional_stubs_provider import IntentionalStubsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.resurrection_skills_provider import ResurrectionSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.spirits_provider import SpiritsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.necromancer_skills_provider import NecromancerSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.monk_skills_provider import MonkSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.paragon_skills_provider import ParagonSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.mesmer_skills_provider import MesmerSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.warrior_skills_provider import WarriorSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.dervish_skills_provider import DervishSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.assassin_skills_provider import AssassinSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.elementalist_skills_provider import ElementalistSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.ranger_skills_provider import RangerSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.pve_skills_provider import PveSkillsProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.junundu_provider import JununduProvider
from Sources.oazix.CustomBehaviors.skills.generic.implementations.utility_skill_providers.dhuum_skele_provider import DhuumSkeleProvider

class GenericUtilitySkillsList:
    '''
    This class is a factory for generic utility skills.
    It is not meant to be used directly.
    Thoses skills are automatically added to the utility skillbar if the build is set to complete the build with generic skills.
    '''
    def __init__(self):
        pass

    @staticmethod
    def get_generic_utility_skills_list(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        skills: list[CustomSkillUtilityBase] = []

        skills.extend(IntentionalStubsProvider.get_skills(event_bus, in_game_build))

        skills.extend(ResurrectionSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(SpiritsProvider.get_skills(event_bus, in_game_build))

        skills.extend(NecromancerSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(MonkSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(ParagonSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(MesmerSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(WarriorSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(DervishSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(AssassinSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(ElementalistSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(RangerSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(PveSkillsProvider.get_skills(event_bus, in_game_build))

        skills.extend(JununduProvider.get_skills(event_bus, in_game_build))

        skills.extend(DhuumSkeleProvider.get_skills(event_bus, in_game_build))

        return skills
