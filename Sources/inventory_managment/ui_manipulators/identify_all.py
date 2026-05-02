from Py4GWCoreLib import UIManager
from Py4GWCoreLib.py4gwcorelib_src.Console import Console
from Sources.inventory_managment.ui_manipulators.generic_ui_frame_clicker import UIManagerHelpers

FRAME_ALIAS_FILE = ".\\Py4GWCoreLib\\frame_aliases.json"  # JSON file mapping human-readable frame labels
INVENTORY_WINDOW_HASH = 2874675009       # UIManager hash for fallback if the json dont load, probably can drop
INVENTORY_WINDOW_CHILD = 14


class IdentifyAllItems:

    def IsWindowOpen(self) -> bool:
        from Py4GWCoreLib.enums_src.UI_enums import WindowID
        return UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags)

    def OpenWindow(self) -> None:
        """Open the mini map window."""
        from Py4GWCoreLib.enums_src.UI_enums import WindowID
        if self.IsWindowOpen():
            return
        UIManager.SetWindowVisible(WindowID.WindowID_Inventory, True)

    def find_identify_all_frame_id(self):
        global INVENTORY_WINDOW_HASH, FRAME_ALIAS_FILE, INVENTORY_WINDOW_CHILD
        _frame_id = 0

        try:
            _frame_id = UIManager.GetFrameIDByCustomLabel(FRAME_ALIAS_FILE, "IdentifyAllItems")
        except Exception:
            _frame_id = 0

        if _frame_id > 0:
            return _frame_id

        try:
            _frame_id = UIManager.GetFrameIDByCustomLabel(FRAME_ALIAS_FILE, "Inventory Window")
        except Exception:
            _frame_id = 0

        if _frame_id == 0:
            _frame_id = UIManager.GetFrameIDByHash(INVENTORY_WINDOW_HASH)

        if _frame_id > 0 and UIManager.FrameExists(_frame_id):
            children = UIManagerHelpers().GetAllChildFrameIDs(_frame_id)
            for child_frame_id in children:
                from Py4GWCoreLib import PyUIManager
                child_frame = PyUIManager.UIFrame(child_frame_id)
                if child_frame is not None and child_frame.child_offset_id == INVENTORY_WINDOW_CHILD:
                    return child_frame_id

        return None

    def IdentifyAll(self):

        from Py4GWCoreLib import Routines

        if not self.IsWindowOpen():
            self.OpenWindow()
            yield from Routines.Yield.wait(150)
        else:
            Console.Log("IdentifyAll", f"Inventory already open", Console.MessageType.Info)

        yield from Routines.Yield.wait(350)
        if self.IsWindowOpen():
            yield from Routines.Yield.wait(150)

            frame_id = self.find_identify_all_frame_id()

            if frame_id is not None:
                Console.Log("IdentifyAll", f"Clicked on frame {frame_id} to IdentifyAll", Console.MessageType.Info)
                print ()
                UIManager.FrameClick(frame_id)
            else:
                Console.Log("IdentifyAll", f"{frame_id} - could not identify materials", Console.MessageType.Info)

        pass
