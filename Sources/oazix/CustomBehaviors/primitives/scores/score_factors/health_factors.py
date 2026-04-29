from typing import override

from Py4GWCoreLib import Agent
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class Health_Factors(ScoreDefinition):
    def health_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        # Health factor
        health = Agent.GetHealth(target_agent_id)
        score_max, score_min, score_offset = self._health_factors(health, score_max, score_min, score_offset)

        return score_max, score_min, score_offset

    def _health_factors(self, health, score_max, score_min, score_offset):
        if health <= .15:
            score_max += 7.5
            score_min += 15.0
            score_offset += 6
        elif health <= .5:
            score_max += 10.0
            score_min += 17.0
            score_offset += 5
        elif health <= .75:
            score_max += 5.0
            score_min += 15.0
            score_offset += 3
        elif health <= .9:
            score_max += 1.0
            score_min += 1.0
            score_offset += 1
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        string = "Health => (max, min, score)"

        for _range in [0,0.20,0.40,0.50,0.60,0.80,1]:
            nearby = self._health_factors(_range, 0, 0, 0)
            string += f"""
    {round(_range*100)}% => {nearby} """

        return string
