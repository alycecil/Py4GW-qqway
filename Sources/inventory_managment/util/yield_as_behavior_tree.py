from typing import Generator

import Py4GW

from Py4GWCoreLib import traceback, IconsFontAwesome5
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.py4gwcorelib_src.Color import ColorPalette
from Sources.inventory_managment import constants


# Allow the user to override the dialog id manually if they so choose as well as display current dialog id and button to send
def as_behavior_tree(name: str, p_ticker: Generator | None = None):
    if p_ticker is None:
        return None
    return BehaviorTree(YieldAsBehaviorTree(name, p_ticker))


class YieldAsBehaviorTree(BehaviorTree.Node):

    def __init__(
            self,
            name: str,
            ticker: Generator | None
    ):
        super().__init__(name=name,
                         node_type="ActionNode",
                         node_category="leaf",
                         icon=IconsFontAwesome5.ICON_PLAY,
                         color=ColorPalette.GetColor("dark_orange"))
        self.ticker = ticker

    def _tick_impl(self) -> BehaviorTree.NodeState:
        try:
            if self.ticker is not None:
                string = next(self.ticker)

                # if constants.DEBUG:
                #     Py4GW.Console.Log(f"YieldAsBehaviorTree {self.name}", f"Tick: {string}", Py4GW.Console.MessageType.Info)

                return BehaviorTree.NodeState.RUNNING
            else:
                return BehaviorTree.NodeState.SUCCESS
        except StopIteration:
            self.ticker = None
            Py4GW.Console.Log(f"YieldAsBehaviorTree {self.name}", f"Ticker done", Py4GW.Console.MessageType.Info)
            return BehaviorTree.NodeState.SUCCESS
        except Exception as e:
            self.ticker = None
            # Catch-all for any other unexpected exceptions
            Py4GW.Console.Log(f"YieldAsBehaviorTree {self.name}", f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log(f"YieldAsBehaviorTree {self.name}", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
            return BehaviorTree.NodeState.FAILURE
