
from Py4GWCoreLib import UIManager


class UIManagerHelpers:

    def GetAllChildFrameIDs(self, root_frame_id: int):
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
