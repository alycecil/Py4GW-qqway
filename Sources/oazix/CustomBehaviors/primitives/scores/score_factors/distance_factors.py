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
    def __init__(
            self,
            touch_short_range: float = 50,
            touch_long_range: float = 2.2,
            adjacent_short_range: float = 35,
            adjacent_long_range: float = 2,
            nearby_short_range: float = 20,
            nearby_long_range: float = 1.5,
            area_short_range: float = 10,
            area_long_range: float = 1.1,
            twice_area_short_range: float = 5,
            twice_area_long_range: float = 0.5,
            earshot_short_range: float = 1,
            earshot_long_range: float = 0.1,
    ):
        self.touch_short_range = touch_short_range
        self.touch_long_range = touch_long_range
        self.adjacent_short_range = adjacent_short_range
        self.adjacent_long_range = adjacent_long_range
        self.nearby_short_range = nearby_short_range
        self.nearby_long_range = nearby_long_range
        self.area_short_range = area_short_range
        self.area_long_range = area_long_range
        self.twice_area_short_range = twice_area_short_range
        self.twice_area_long_range = twice_area_long_range
        self.earshot_short_range = earshot_short_range
        self.earshot_long_range = earshot_long_range

    def distance_factor(
            self,
            score_max, score_min, score_offset,
            distance, short_range
    ):
        # Distance factor
        if distance < Range.Touch.value:
            score_offset += self.touch_short_range if short_range else self.touch_long_range
        elif distance < Range.Adjacent.value:
            score_offset += self.adjacent_short_range if short_range else self.adjacent_long_range
        elif distance < Range.Nearby.value:
            score_offset += self.nearby_short_range if short_range else self.nearby_long_range
        elif distance < Range.Area.value:
            score_offset += self.area_short_range if short_range else self.area_long_range
        elif distance < Range.Area.value * 2:
            score_offset += self.twice_area_short_range if short_range else self.twice_area_long_range
        elif distance < Range.Earshot.value:
            score_offset += self.earshot_short_range if short_range else self.earshot_long_range
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
