from Py4GWCoreLib import Map
from Py4GWCoreLib import UIManager
from Py4GWCoreLib.py4gwcorelib_src.Console import Console
from Sources.inventory_managment.ui_manipulators.generic_ui_frame_clicker import UIManagerHelpers

FRAME_ALIAS_FILE = ".\\Py4GWCoreLib\\frame_aliases.json"  # JSON file mapping human-readable frame labels
XUNLAI_WINDOW_HASH = 2315448754       # UIManager hash for the Xunlai vault window
XUNLAI_WINDOW_CHILD = 5

class DepositMaterials:

    def find_deposit_all_frame_id(self):
        global XUNLAI_WINDOW_HASH, FRAME_ALIAS_FILE, XUNLAI_WINDOW_CHILD
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
            children = UIManagerHelpers().GetAllChildFrameIDs(_frame_id)
            for child_frame_id in children:
                from Py4GWCoreLib import PyUIManager
                child_frame = PyUIManager.UIFrame(child_frame_id)
                if child_frame is not None and child_frame.child_offset_id == XUNLAI_WINDOW_CHILD:
                    return child_frame_id

        return None

    def DepositMaterials(self):
        global XUNLAI_WINDOW_HASH, FRAME_ALIAS_FILE

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

                frame_id = self.find_deposit_all_frame_id()

                if frame_id is not None:
                    Console.Log("DepositMaterials", f"Clicked on frame {frame_id} to DepositAllMaterials", Console.MessageType.Info)
                    print ()
                    UIManager.FrameClick(frame_id)
                else:
                    Console.Log("DepositMaterials", f"{frame_id} - could not deposit materials", Console.MessageType.Info)
        else:
            Console.Log("DepositMaterials", f"Wrong location type", Console.MessageType.Info)
        pass
