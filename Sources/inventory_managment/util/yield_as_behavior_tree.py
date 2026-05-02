from typing import Generator


from Py4GWCoreLib import traceback, IconsFontAwesome5, Console, ConsoleLog
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
                #     Console.Log(f"YieldAsBehaviorTree {self.name}", f"Tick: {string}", Console.MessageType.Info)

                return BehaviorTree.NodeState.RUNNING
            else:
                return BehaviorTree.NodeState.SUCCESS
        except StopIteration:
            self.ticker = None
            Console.Log(f"YieldAsBehaviorTree {self.name}", f"Ticker done", Console.MessageType.Info)
            return BehaviorTree.NodeState.SUCCESS
        except Exception as e:
            self.ticker = None
            # Catch-all for any other unexpected exceptions
            Console.Log(f"YieldAsBehaviorTree {self.name}", f"Unexpected error encountered: {str(e)}", Console.MessageType.Error)
            Console.Log(f"YieldAsBehaviorTree {self.name}", f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)
            return BehaviorTree.NodeState.FAILURE
