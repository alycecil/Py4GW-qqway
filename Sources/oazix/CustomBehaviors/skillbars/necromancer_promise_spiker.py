from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import (
    ScorePerAgentQuantityDefinition,
)
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import (
    CustomBehaviorBaseUtility,
)
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import (
    CustomSkillUtilityBase,
)
from Sources.oazix.CustomBehaviors.skills.assassin.assassins_promise_utility import (
    AssassinsPromiseUtility,
)
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import (
    EbonVanguardAssassinSupportUtility,
)
from Sources.oazix.CustomBehaviors.skills.common.finish_him_utility import FinishHimUtility
from Sources.oazix.CustomBehaviors.skills.dervich.eremites_attack_utility import EremitesAttack_Utility
from Sources.oazix.CustomBehaviors.skills.dervich.twin_moon_sweep_utility import TwinMoonSweep_Utility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import (
    KeepSelfEffectUpUtility,
)
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_attack_utility import (
    RawSimpleAttackUtility,
)
from Sources.oazix.CustomBehaviors.skills.necromancer.putrid_explosion_utility import (
    PutridExplosionUtility,
)
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_lost_souls_utility import (
    SignetOfLostSoulsUtility,
)


class NecromancerPromiseSpiker_UtilitySkillBar(CustomBehaviorBaseUtility):
    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core
        self.masochism_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Masochism"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(92),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        )
        self.assassins_promise_utility: CustomSkillUtilityBase = AssassinsPromiseUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(95),
        )
        self.putrid_bile_utility: CustomSkillUtilityBase = RawSimpleAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Putrid_Bile"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
            mana_required_to_cast=10,
        )
        self.putrid_explosion_utility: CustomSkillUtilityBase = PutridExplosionUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 80 if enemy_qte >= 2 else 50
            ),
            mana_required_to_cast=5,
        )


        # scythe attacks
        self.twin_moon_sweep_utility: CustomSkillUtilityBase = TwinMoonSweep_Utility(event_bus=self.event_bus, current_build=in_game_build)
        self.eremites_attack_utility: CustomSkillUtilityBase = EremitesAttack_Utility(event_bus=self.event_bus, current_build=in_game_build)
        #sin attacks
        self.jagged_strike_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.fox_fangs_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.death_blossom_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)


        # pve spike helpers
        self.finish_him_utility: CustomSkillUtilityBase = FinishHimUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(87),
        )
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = (
            EbonVanguardAssassinSupportUtility(
                event_bus=self.event_bus,
                current_build=in_game_build,
                score_definition=ScoreStaticDefinition(89),
                mana_required_to_cast=15,
            )
        )
        self.pain_inverter_utility: CustomSkillUtilityBase = RawSimpleAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Pain_Inverter"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
            mana_required_to_cast=5,
        )
        self.angorodons_gaze_utility: CustomSkillUtilityBase = RawSimpleAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Angorodons_Gaze"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(69),
            mana_required_to_cast=5,
        )
        self.signet_of_lost_souls_utility: CustomSkillUtilityBase = SignetOfLostSoulsUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.masochism_utility,
            self.assassins_promise_utility,
            self.ebon_vanguard_assassin_support,
            self.putrid_bile_utility,
            self.finish_him_utility,
            self.putrid_explosion_utility,
            self.pain_inverter_utility,
            self.angorodons_gaze_utility,
            self.signet_of_lost_souls_utility,

            self.twin_moon_sweep_utility,
            self.eremites_attack_utility,

            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.assassins_promise_utility.custom_skill
        ]
