import os

from Py4GWCoreLib import GLOBAL_CACHE, Item
from Sources.marks_sources.mods_parser import ParsedModifierResult, parse_modifiers, MatchedWeaponModInfo, \
    MatchedRuneInfo, ModDatabase


class GetMods:

    def __init__(
            self,
    ):
        project_root = Py4GW.Console.get_projects_path()
        self.MOD_DB = ModDatabase.load(os.path.join(project_root, "Sources/marks_sources/mods_data"))

    def get_mods_from_item(self, item_id) -> tuple[str | None, str | None, str | None, ParsedModifierResult]:
        modifiers = []
        item = Item.item_instance(item_id)
        for mod in item.modifiers:
            modifiers.append(
                [
                    mod.GetIdentifier(),
                    mod.GetArg1(),
                    mod.GetArg2(),
                ]
            )
        # 2. Parse any item's raw modifiers
        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        result: ParsedModifierResult = parse_modifiers(
            modifiers=modifiers,
            item_type=item_type_to_int,
            model_id=GLOBAL_CACHE.Item.GetModelID(item_id),
            db=self.MOD_DB,
        )

        prefix = None
        suffix = None
        inherent = None

        if result.prefix and isinstance(result.prefix, MatchedWeaponModInfo):
            prefix = result.prefix.weapon_mod.name
        elif result.prefix and isinstance(result.prefix, MatchedRuneInfo):
            prefix = result.prefix.rune.name

        if result.inherent and isinstance(result.inherent, MatchedWeaponModInfo):
            inherent = result.inherent.weapon_mod.name

        if result.suffix and isinstance(result.suffix, MatchedWeaponModInfo):
            suffix = result.suffix.weapon_mod.name
        elif result.prefix and isinstance(result.suffix, MatchedRuneInfo):
            suffix = result.suffix.rune.name

        return prefix, suffix, inherent, result
