#region AutoInventory
from typing import Optional, Callable
from .Console import ConsoleLog, Console
from .Timer import ThrottledTimer
from .ActionQueue import ActionQueueManager
from .Lootconfig_src import LootConfig

class AutoInventoryHandler():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoInventoryHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._LOOKUP_TIME:int = 15000
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)

        self.runtime_initialized = False
        self.status = "Idle"
        self.outpost_handled = False
        self.module_active:bool = False
        self.module_name:str = "AutoInventoryHandler"
        
        self.id_whites:bool = False
        self.id_blues:bool = False
        self.id_purples:bool = False
        self.id_golds:bool = False
        self.id_greens:bool = False
        self.id_model_blacklist:list[int] = []  # Items that should not be identified, even if they match the ID criteria
        
        self.salvage_whites:bool = False
        self.salvage_rare_materials:bool = False
        self.salvage_blues:bool = False
        self.salvage_purples:bool = False
        self.salvage_golds:bool = False
        self.salvage_dialog_auto_handle:bool = False
        self.salvage_dialog_auto_confirm_materials:bool = False
        self.salvage_dialog_debug:bool = False
        self.salvage_dialog_strategy:int = 0
        self.salvage_dialog_fallback_index:int = 1
        self.item_type_blacklist:list[int] = [] # Item types that should not be salvaged, even if they match the salvage criteria
        self.salvage_blacklist:list[int] = []  # Items that should not be salvaged, even if they match the salvage criteria
        self.blacklisted_model_id:int = 0
        self.model_id_search:str = ""
        self.item_type_search:str = ""
        self.model_id_search_mode:int = 0  # 0 = Contains, 1 = Starts With
        self.item_type_search_mode:int = 0  # 0 = Contains, 1 = Starts With
        self.show_dialog_popup:bool = False 
        self.show_item_type_dialog:bool = False
        
        self.deposit_trophies:bool = False
        self.deposit_materials:bool = False
        self.deposit_blues:bool = False
        self.deposit_purples:bool = False
        self.deposit_golds:bool = False
        self.deposit_greens:bool = False
        self.deposit_event_items:bool = False
        self.deposit_dyes:bool = False
        self.keep_gold:int = 5000
        self.deposit_trophies_blacklist:list[int] = []  # Model IDs of trophies that should not be deposited
        self.deposit_materials_blacklist:list[int] = []  # Model IDs of materials that should not be deposited
        self.deposit_event_items_blacklist:list[int] = []  # Model IDs of event items that should not
        self.deposit_dyes_blacklist:list[int] = []  # Model IDs of dyes that should not be deposited
        self.deposit_model_blacklist:list[int] = []  # Model IDs of items that should not be deposited

        self._initialized = True

    @property
    def initialized(self):
        # Backward-compatible alias for older callers.
        return self.runtime_initialized

    @initialized.setter
    def initialized(self, value):
        # Backward-compatible alias for older callers.
        self.runtime_initialized = value

                 
    def IdentifyItems(self,progress_callback: Optional[Callable[[float], None]] = None, log: bool = False):
        from ..ItemArray import ItemArray
        from ..enums import Bags
        from ..Inventory import Inventory
        import PyItem
        from ..Item import Item
        from ..Routines import Routines
        
        bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
        item_array = ItemArray.GetItemArray(bag_list)
        
        identified_items = 0
        identify_wait_step_ms = 50
        identify_wait_timeout_ms = 5000
             
        for item_id in item_array:
            first_id_kit = Inventory.GetFirstIDKit()
             
            if first_id_kit == 0:
                Console.Log("AutoIdentify", "No ID Kit found in inventory.", Console.MessageType.Warning)
                return   
                 
            item_instance = PyItem.PyItem(item_id)
            item_instance.GetContext()
            is_identified = item_instance.is_identified
            model_id = item_instance.model_id
                 
            if is_identified:
                continue
            if model_id in self.id_model_blacklist:
                continue
                 
            _,rarity = Item.Rarity.GetRarity(item_id)
            if ((rarity == "White" and self.id_whites) or
                (rarity == "Blue" and self.id_blues) or
                (rarity == "Green" and self.id_greens) or
                (rarity == "Purple" and self.id_purples) or
                (rarity == "Gold" and self.id_golds)):
                ActionQueueManager().AddAction("ACTION", Inventory.IdentifyItem,item_id, first_id_kit)
                identified_items += 1
                waited_ms = 0
                while True:
                    yield from Routines.Yield.wait(identify_wait_step_ms)
                    waited_ms += identify_wait_step_ms
                    item_instance.GetContext()
                    if item_instance.is_identified:
                        break
                    if waited_ms >= identify_wait_timeout_ms:
                        Console.Log("AutoIdentify", f"Timed out waiting for identification (item_id={item_id}).", Console.MessageType.Warning)
                        break
                    
        if identified_items > 0 and log:
            ConsoleLog(self.module_name, f"Identified {identified_items} items", Console.MessageType.Success)
            
    def SalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None, log: bool = False):
        from ..ItemArray import ItemArray
        from ..enums import Bags
        from ..Inventory import Inventory
        import PyItem
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines

        bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
        item_array = ItemArray.GetItemArray(bag_list)

        salvaged_items = 0
        salvage_wait_step_ms = 50
        salvage_wait_timeout_ms = 10000
        salvage_item_attempt_limit = 50
        salvage_confirm_timeout_ms = 1500
        salvage_dialog_auto_handle = bool(self.salvage_dialog_auto_handle)
        salvage_dialog_auto_confirm_materials = bool(self.salvage_dialog_auto_confirm_materials)
        salvage_dialog_debug = bool(self.salvage_dialog_debug)
        salvage_dialog_strategy = int(self.salvage_dialog_strategy)
        if salvage_dialog_strategy == 2:
            salvage_dialog_strategy = 1
        elif salvage_dialog_strategy not in (0, 1):
            salvage_dialog_strategy = 0

        for item_id in item_array:
            item_instance = PyItem.PyItem(item_id)
            item_instance.GetContext()
            quantity = item_instance.quantity
            if quantity == 0:
                continue

            is_customized = GLOBAL_CACHE.Item.Properties.IsCustomized(item_id)
            if is_customized:
                # Skip customized items
                continue
            _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            is_white = rarity == "White"
            is_blue = rarity == "Blue"
            is_green = rarity == "Green"
            is_purple = rarity == "Purple"
            is_gold = rarity == "Gold"

            is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
            is_material_salvageable = GLOBAL_CACHE.Item.Usage.IsMaterialSalvageable(item_id)
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
            is_salvageable = GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)
            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
            item_type,_ = GLOBAL_CACHE.Item.GetItemType(item_id)

            # Filtering logic
            if not ((is_white and is_salvageable) or (is_identified and is_salvageable)):
                continue
            if item_type in self.item_type_blacklist:
                continue
            if model_id in self.salvage_blacklist:
                continue
            if is_white and is_material and is_material_salvageable and not self.salvage_rare_materials:
                continue
            from Sources.oazix.CustomBehaviors.skills.inventory.inventory_utils import InventoryMode
            action_for_item = self.action_for_item(item_id)
            inventory_mode_salvage_ = [InventoryMode.SALVAGE]
            if Inventory.GetFreeSlotCount() < 5:
                inventory_mode_salvage_ = [InventoryMode.SALVAGE, InventoryMode.SELL_DONT_IDENTIFY, InventoryMode.SELL]

            if action_for_item in inventory_mode_salvage_:
                pass
            else:
                if is_white and not is_material and not self.salvage_whites:
                    continue
            if is_blue and not self.salvage_blues:
                continue
            # Greens are not salvageable in Guild Wars; skip explicitly.
            if is_green:
                continue
            if is_purple and not self.salvage_purples:
                continue
            if is_gold and not self.salvage_golds:
                continue

            require_materials_confirmation = is_purple or is_gold
            salvage_attempts = 0

            # Repeat until item no longer exists
            while True:
                salvage_attempts += 1
                if salvage_attempts > salvage_item_attempt_limit:
                    Console.Log("AutoSalvage", f"Giving up on item after too many salvage attempts (item_id={item_id}).", Console.MessageType.Warning)
                    break
                 
                bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
                item_array = ItemArray.GetItemArray(bag_list)
                if item_id not in item_array:
                    break  # Fully consumed / disappeared
    
                item_instance.GetContext()
                quantity = item_instance.quantity
                if quantity == 0:
                    break
                if not item_instance.is_salvageable:
                    salvaged_items += 1
                    Inventory._salvage_choice_debug_log(
                        salvage_dialog_debug,
                        "AutoSalvage",
                        f"complete item item_id={item_id} reason=no_longer_salvageable.",
                    )
                    break

                salvage_kit = Inventory.GetFirstSalvageKit(use_lesser=True)
                if salvage_kit == 0:
                    Console.Log("AutoSalvage", "No Salvage Kit found in inventory.", Console.MessageType.Warning)
                    return

                Inventory._salvage_choice_debug_log(
                    salvage_dialog_debug,
                    "AutoSalvage",
                    f"begin item item_id={item_id} attempt={salvage_attempts} rarity={rarity} qty={quantity} kit={salvage_kit} auto_handle={salvage_dialog_auto_handle} auto_confirm_warning={salvage_dialog_auto_confirm_materials}.",
                )
                ActionQueueManager().AddAction("ACTION", Inventory.SalvageItem, item_id, salvage_kit)
                if require_materials_confirmation:
                    yield from Routines.Yield.wait(150)
                    found_confirm_window = yield from Routines.Yield.Items._wait_for_salvage_materials_window(
                        timeout_ms=salvage_confirm_timeout_ms,
                        poll_ms=salvage_wait_step_ms,
                        initial_wait_ms=0
                    )
                    if not found_confirm_window:
                        Console.Log(
                            "AutoSalvage",
                            f"Timed out waiting for salvage confirmation window (item_id={item_id}).",
                            Console.MessageType.Warning
                        )
                        break
                    for i in range(3):
                        ActionQueueManager().AddAction("ACTION", Inventory.AcceptSalvageMaterialsWindow)
                        yield from Routines.Yield.wait(salvage_wait_step_ms)

                waited_ms = 0
                salvage_timed_out = False
                salvage_dialog_failed = False
                dialog_status = "not_visible"
                handled_salvage_dialog = False
                handled_dialog_settle_ms = 0
                handled_dialog_post_check_ms = max(250, salvage_wait_step_ms * 6)
                while True:
                    if salvage_dialog_auto_handle:
                        dialog_status = yield from Inventory.HandleSalvageChoiceDialog(
                            auto_handle=True,
                            strategy=salvage_dialog_strategy,
                            auto_confirm_materials_warning=salvage_dialog_auto_confirm_materials,
                            queue_name="ACTION",
                            log_module="AutoSalvage",
                            queue_wait_timeout_ms=max(1000, salvage_wait_timeout_ms // 2),
                            poll_ms=salvage_wait_step_ms,
                            close_timeout_ms=salvage_confirm_timeout_ms,
                            debug_enabled=salvage_dialog_debug,
                            item_id=item_id,
                        )
                        if dialog_status == "handled":
                            handled_salvage_dialog = True
                            handled_dialog_settle_ms = 0
                            waited_ms = 0
                            continue
                        if dialog_status not in {"not_visible", "disabled", "confirm_pending"}:
                            Inventory._salvage_choice_debug_log(
                                salvage_dialog_debug,
                                "AutoSalvage",
                                f"stop item item_id={item_id} status=popup_failed reason={dialog_status}.",
                            )
                            salvage_dialog_failed = True
                            break

                    yield from Routines.Yield.wait(salvage_wait_step_ms)
                    waited_ms += salvage_wait_step_ms
                    if handled_salvage_dialog:
                        handled_dialog_settle_ms += salvage_wait_step_ms

                    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
                    item_array = ItemArray.GetItemArray(bag_list)

                    if item_id not in item_array:
                        salvaged_items += 1
                        break  # Fully consumed

                    item_instance.GetContext()
                    if item_instance.quantity < quantity:
                        salvaged_items += 1
                        break  # Successfully salvaged one item
                    if handled_salvage_dialog and handled_dialog_settle_ms >= handled_dialog_post_check_ms:
                        retry_required = item_instance.is_salvageable
                        Inventory._salvage_choice_debug_log(
                            salvage_dialog_debug,
                            "AutoSalvage",
                            f"re-evaluate item item_id={item_id} after handled dialog settle={handled_dialog_settle_ms}ms status={'retry' if retry_required else 'processed'}.",
                        )
                        if not retry_required:
                            salvaged_items += 1
                        break
                    if waited_ms >= salvage_wait_timeout_ms:
                        Console.Log("AutoSalvage", f"Timed out waiting for salvage result (item_id={item_id}).", Console.MessageType.Warning)
                        salvage_timed_out = True
                        break

                if salvage_dialog_failed:
                    Console.Log(
                        "AutoSalvage",
                        f"Stopping auto-salvage because the salvage choice dialog could not be handled safely (item_id={item_id}, status={dialog_status}).",
                        Console.MessageType.Warning,
                    )
                    return

                if salvage_timed_out:
                    break

                yield from Routines.Yield.wait(salvage_wait_step_ms)

        if salvaged_items > 0 and log:
            ConsoleLog(self.module_name, f"Salvaged {salvaged_items} items", Console.MessageType.Success)

            
            
    def DepositItemsAuto(self):
        from ..enums import Bags, ModelID
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines

        event_items = set()
        selected_filters = {
            "Alcohol": None,          # include ALL subcategories
            "Sweets": None,           # include ALL subcategories
            "Party": None,            # include ALL subcategories
            "Death Penalty Removal": None,  # include ALL subcategories
            "Reward Trophies": {"Special Events"},
        }

        # Build once per deposit run instead of once per item.
        for category, subcats in LootConfig().LootGroups.items():
            if category not in selected_filters:
                continue

            allowed_subcats = selected_filters[category]
            for subcat, items in subcats.items():
                if allowed_subcats is not None and subcat not in allowed_subcats:
                    continue
                event_items.update(m.value for m in items)

        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                # Check if the item is a trophy or material
                is_trophy = GLOBAL_CACHE.Item.Type.IsTrophy(item_id)
                is_tome = GLOBAL_CACHE.Item.Type.IsTome(item_id)
                _, item_type = GLOBAL_CACHE.Item.GetItemType(item_id)
                is_usable = (item_type == "Usable")
                
                is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
                _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_white =  rarity == "White"
                is_blue = rarity == "Blue"
                is_green = rarity == "Green"
                is_purple = rarity == "Purple"
                is_gold = rarity == "Gold"
                
                model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
                
                is_dye = model_id == ModelID.Vial_Of_Dye.value
                
                if model_id in self.deposit_model_blacklist:
                    continue
                
                if is_material and model_id in self.deposit_materials_blacklist:
                    continue
                
                if is_trophy and model_id in self.deposit_trophies_blacklist:
                    continue
                
                is_dye = (model_id == ModelID.Vial_Of_Dye.value)
                dye1_to_match = None
                if is_dye:
                    dye_info = GLOBAL_CACHE.Item.Customization.GetDyeInfo(item_id)
                    dye1_to_match = dye_info.dye1.ToInt()
                    
                if is_dye and dye1_to_match in self.deposit_dyes_blacklist:
                    continue

                deposited = False
                if is_tome:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_trophy and self.deposit_trophies and is_white:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_material and self.deposit_materials:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_blue and self.deposit_blues:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_purple and self.deposit_purples:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_gold and self.deposit_golds and not is_usable and not is_trophy:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_green and self.deposit_greens:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                     
                if not deposited and model_id == ModelID.Vial_Of_Dye.value and self.deposit_dyes:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True

                from Sources.oazix.CustomBehaviors.skills.inventory.inventory_utils import InventoryMode
                if not deposited and self.action_for_item(item_id) in [InventoryMode.DEPOSIT]:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True

                if ((not deposited) and
                    (model_id in event_items) and 
                    self.deposit_event_items and
                    model_id not in self.deposit_event_items_blacklist):
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
            
            
    def IDAndSalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None):
        self.status = "Identifying"
        yield from self.IdentifyItems()
        if progress_callback:
            progress_callback(0.5)
        self.status = "Salvaging"
        yield from self.SalvageItems()
        self.status = "Idle"
        yield
        
    def IDSalvageDepositItems(self):
        from ..Routines import Routines

        #ConsoleLog("AutoInventoryHandler", "Starting ID, Salvage and Deposit routine", Console.MessageType.Info)
        self.status = "Identifying"
        yield from self.IdentifyItems()
        
        self.status = "Salvaging"
        yield from self.SalvageItems()
        
        self.status = "Depositing"
        yield from self.DepositItemsAuto()
        
        self.status = "Depositing Gold"
        
        yield from Routines.Yield.Items.DepositGold(self.keep_gold, log =False)
        
        self.status = "Idle"
        #ConsoleLog("AutoInventoryHandler", "ID, Salvage and Deposit routine completed", Console.MessageType.Success)

    def action_for_item(self, item_id):
        from Sources.oazix.CustomBehaviors.primitives.infrastructure.persistence_locator import PersistenceLocator
        from Sources.oazix.CustomBehaviors.skills.inventory.merchant_refill_if_needed_utility import string_to_dict
        from Sources.oazix.CustomBehaviors.skills.inventory.inventory_utils import InventoryMode, InventoryUtils, InventoryUtilsConfig
        data: str | None = PersistenceLocator().skills.read("my_inventory_utils_config", "inventory_utils_config")
        if data is not None:
            inventory_utils_config = string_to_dict(data)
        else:
            inventory_utils_config = InventoryUtilsConfig()

        inventory_utils = InventoryUtils()

        return inventory_utils.get_action_for_item(inventory_utils_config, item_id)

    def DepositMaterials(self):
        from Py4GWCoreLib import Map
        from Py4GWCoreLib import UIManager
        FRAME_ALIAS_FILE = ".\\Py4GWCoreLib\\frame_aliases.json"  # JSON file mapping human-readable frame labels
        XUNLAI_WINDOW_HASH = 2315448754       # UIManager hash for the Xunlai vault window

        def GetAllChildFrameIDs(root_frame_id: int):
            """
            Finds all frame IDs that match the given offset path from the parent hash.
            Unlike GetChildFrameID, this returns *all* frames that match the offset chain.

            :param root_frame_id: The root hash of the UI dialog
            :return: List of matching frame IDs
            """
            frame_array = UIManager.GetFrameArray()

            matching_ids = []

            for fid in frame_array:
                from Py4GWCoreLib import PyUIManager
                current = PyUIManager.UIFrame(fid)
                offsets = []
                trace = current

                if trace.frame_id == root_frame_id:
                    matching_ids.append(current.frame_id)

            return matching_ids

        def find_deposit_all_frame_id(FRAME_ALIAS_FILE, GetAllChildFrameIDs, XUNLAI_WINDOW_HASH):
            _frame_id = 0

            try:
                _frame_id = UIManager.GetFrameIDByCustomLabel(FRAME_ALIAS_FILE, "DepositAllMaterials")
            except Exception:
                _frame_id = 0

            if _frame_id > 0:
                return _frame_id

            try:
                _frame_id = UIManager.GetFrameIDByCustomLabel(FRAME_ALIAS_FILE, "Xunlai Window")
            except Exception:
                _frame_id = 0

            if _frame_id == 0:
                _frame_id = UIManager.GetFrameIDByHash(XUNLAI_WINDOW_HASH)

            if _frame_id > 0 and UIManager.FrameExists(_frame_id):
                children = GetAllChildFrameIDs(_frame_id)
                for child_frame_id in children:
                    from Py4GWCoreLib import PyUIManager
                    child_frame = PyUIManager.UIFrame(child_frame_id)
                    if child_frame is not None and child_frame.child_offset_id == 4:
                        return child_frame_id

            return None

        if Map.IsOutpost():
            from Py4GWCoreLib import Routines
            from Py4GWCoreLib import GLOBAL_CACHE

            if not GLOBAL_CACHE.Inventory.IsStorageOpen():
                GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
                yield from Routines.Yield.wait(150)
            else:
                Console.Log("DepositMaterials", f"Chest already open", Console.MessageType.Info)

            yield from Routines.Yield.wait(350)
            if GLOBAL_CACHE.Inventory.IsStorageOpen():
                yield from Routines.Yield.wait(150)

                frame_id = find_deposit_all_frame_id(FRAME_ALIAS_FILE, GetAllChildFrameIDs, XUNLAI_WINDOW_HASH)

                if frame_id is not None:
                    Console.Log("DepositMaterials", f"Clicked on frame {frame_id} to DepositAllMaterials", Console.MessageType.Info)
                    print ()
                    UIManager.FrameClick(frame_id)
                else:
                    Console.Log("DepositMaterials", f"{frame_id} - could not deposit materials", Console.MessageType.Info)
        else:
            Console.Log("DepositMaterials", f"Wrong location type", Console.MessageType.Info)
        pass

#endregion
