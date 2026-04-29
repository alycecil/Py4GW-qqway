from typing import override

from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class DistanceFactors(ScoreDefinition):

    def distance_factor(
            self,
            score_max, score_min, score_offset,
            distance, short_range
    ):
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return "distance is not a factor"


class DistanceFactors_Simple(DistanceFactors):
    def distance_factor(
            self,
            score_max, score_min, score_offset,
            distance, short_range
    ):
        # Distance factor
        if distance < Range.Touch.value:
            score_offset += 50 if short_range else 2.2
        elif distance < Range.Adjacent.value:
            score_offset += 35 if short_range else 2
        elif distance < Range.Nearby.value:
            score_offset += 20 if short_range else 1.5
        elif distance < Range.Area.value:
            score_offset += 10 if short_range else 1.1
        elif distance < Range.Area.value * 2:
            score_offset += 5 if short_range else 0.5
        elif distance < Range.Earshot.value:
            score_offset += 1 if short_range else 0.1
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        string = "distance => (max, min, score) (not short range)"

        for _range in [Range.Touch, Range.Adjacent, Range.Nearby, Range.Area, Range.Earshot]:
            nearby = self.distance_factor(0, 0, 0, _range.value - 1, True)
            longer = self.distance_factor(0, 0, 0, _range.value - 1, False)
            string += f"""
    {_range.name} => {nearby} ({longer})"""

        return string


class DistanceFactors_Short(DistanceFactors):
    def __init__(self,
                 touch=12,
                 adjacent=7,
                 nearby=5,
                 area=3,
                 twice_area=2,
                 earshot=1,
                 ) -> None:
        self.touch = touch
        self.adjacent = adjacent
        self.nearby = nearby
        self.area = area
        self.twice_area = twice_area
        self.earshot = earshot

    # todo constructor
    def distance_factor(
            self,
            score_max, score_min, score_offset,
            distance, short_range
    ):
        # Distance factor
        if distance < Range.Touch.value:
            score_offset += self.touch
        elif distance < Range.Adjacent.value:
            score_offset += self.adjacent
        elif distance < Range.Nearby.value:
            score_offset += self.nearby
        elif distance < Range.Area.value:
            score_offset += self.area
        elif distance < Range.Area.value * 2:
            score_offset += self.twice_area
        elif distance < Range.Earshot.value:
            score_offset += self.earshot
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        string = "distance => (max, min, score)"

        for _range in [Range.Touch, Range.Adjacent, Range.Nearby, Range.Area, Range.Earshot]:
            nearby = self.distance_factor(0, 0, 0, _range.value - 1, True)
            string += f"""
    {_range.name} => {nearby}"""

        return string
