import PyInventory
import PyImGui
import random
import time
import os
import re
import shutil
import copy

from Py4GWCoreLib import *
import os

import Py4GW
import PyImGui

from Py4GWCoreLib import Item
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Item_enums import Rarity
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

Utils.ClearSubModules("ItemHandling")
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Mods.ItemMod import ItemMod
from Sources.frenkeyLib.ItemHandling.BTNodes import STORAGE_BAGS, BTNodes
from Sources.frenkeyLib.ItemHandling.Rules.types import SalvageMode

MODULE_NAME = "Xunlai Sort"        # Display name shown in the overlay window
MODULE_ICON = "Textures/Module_Icons/XunlaiSort.png"  # Relative path to the toggle-button icon
CHEST_FRAME_ID = 752                  # Fallback frame ID for the Xunlai chest window
XUNLAI_WINDOW_HASH = 2315448754       # UIManager hash for the Xunlai vault window
FRAME_ALIAS_FILE = ".\\Py4GWCoreLib\\frame_aliases.json"  # JSON file mapping human-readable frame labels
INVENTORY_FRAME_HASH = 291586130      # Fallback: player inventory panel frame hash
ANCHOR_OFFSET_X = 6                   # Horizontal gap (px) between the vault window and our overlay
ANCHOR_OFFSET_Y = 40                   # Vertical offset from the top of the vault window
COMPACT_WINDOW_MIN_WIDTH = 200        # Minimum width of the compact settings panel
project_root = Py4GW.Console.get_projects_path()  # Absolute root path of the Py4GW installation
SORTER_STATE : bool = False
_tree : BehaviorTree | None = None

def _get_storage_anchor_position(anchor_window_width=None):
	"""Calculate the screen position where our overlay window should be anchored.

	Looks up the Xunlai vault frame by alias, then by hash, then falls back to the
	inventory panel. Returns (x, y) or None when no suitable frame is visible.
	"""
	if anchor_window_width is None:
		anchor_window_width = max(float(_last_window_width), float(COMPACT_WINDOW_MIN_WIDTH))
	else:
		anchor_window_width = max(float(anchor_window_width), 1.0)
	frame_id = 0

	try:
		frame_id = UIManager.GetFrameIDByCustomLabel(FRAME_ALIAS_FILE, "Xunlai Window")
	except Exception:
		frame_id = 0

	if frame_id == 0:
		frame_id = UIManager.GetFrameIDByHash(XUNLAI_WINDOW_HASH)

	if frame_id == 0:
		frame_id = CHEST_FRAME_ID

	if frame_id > 0 and UIManager.FrameExists(frame_id):
		left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
		x1 = min(left, right)
		y1 = min(top, bottom)
		y2 = max(top, bottom)

		anchor_x = float(x1 - ANCHOR_OFFSET_X - anchor_window_width)

		if y2 > y1:
			anchor_y = float(y1 + ANCHOR_OFFSET_Y)
		else:
			anchor_y = float(top + ANCHOR_OFFSET_Y)

		return anchor_x, anchor_y

	fallback_frame_id = UIManager.GetFrameIDByHash(INVENTORY_FRAME_HASH)
	if fallback_frame_id == 0 or not UIManager.FrameExists(fallback_frame_id):
		return None

	left, top, right, _ = UIManager.GetFrameCoords(fallback_frame_id)
	if right <= left:
		return None

	return float(left - ANCHOR_OFFSET_X - anchor_window_width), float(top + ANCHOR_OFFSET_Y)


# -----------------------------------------------------------------------------
# UI rendering and interactions
# -----------------------------------------------------------------------------
def _draw_storage_hover_modelid_tooltip(available_storage_bags):
	"""Show an ImGui tooltip with type and model info when hovering over a storage item."""
	try:
		hovered_item_id = int(GLOBAL_CACHE.Inventory.GetHoveredItemID())
	except Exception:
		return

	if hovered_item_id <= 0:
		return

	for bag_index, bag_enum in enumerate(available_storage_bags, start=1):
		try:
			bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
			items = bag.GetItems()
		except Exception:
			continue

		for item in items:
			if not item or int(item.item_id) != hovered_item_id:
				continue

			try:
				model_id = int(item.model_id) if hasattr(item, "model_id") else int(GLOBAL_CACHE.Item.GetModelID(hovered_item_id))
			except Exception:
				model_id = 0

			try:
				type_id, type_name = GLOBAL_CACHE.Item.GetItemType(hovered_item_id)
				if not type_name:
					type_name = f"Type {type_id}"
				resolved_type_name = _resolve_item_type_name(hovered_item_id, type_name, model_id)
			except Exception:
				resolved_type_name = "Unknown"

			if PyImGui.begin_tooltip():
				PyImGui.text(f"ModelID: {model_id}")
				PyImGui.text(f"Type: {resolved_type_name}")
				PyImGui.end_tooltip()
			return


def _draw_toggle_icon_window():
	"""Draw the 40×40 frameless icon button that toggles the main Xunlai Manager panel."""
	global SORTER_STATE
	global _tree

	icon_window_size = 40.0
	anchor_pos = _get_storage_anchor_position(icon_window_size)
	if anchor_pos is not None:
		PyImGui.set_next_window_pos(anchor_pos[0] + 60.0, anchor_pos[1] + 55.0)
	PyImGui.set_next_window_size(icon_window_size, icon_window_size)

	icon_window_flags = (
		PyImGui.WindowFlags.NoTitleBar
		| PyImGui.WindowFlags.NoResize
		| PyImGui.WindowFlags.NoScrollbar
		| PyImGui.WindowFlags.NoCollapse
		| PyImGui.WindowFlags.NoBackground
	)
	PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
	if PyImGui.begin("##XunlaiSorterrToggle", icon_window_flags):
		icon_path = MODULE_ICON
		absolute_icon_path = os.path.join(project_root, MODULE_ICON)
		if os.path.exists(absolute_icon_path):
			icon_path = absolute_icon_path

		icon_size = 36.0
		icon_offset = (icon_window_size - icon_size) / 2.0
		cursor_x, cursor_y = PyImGui.get_cursor_screen_pos()
		draw_pos = (cursor_x + icon_offset, cursor_y + icon_offset)
		try:
			ImGui.DrawTextureInDrawList(draw_pos, (icon_size, icon_size), icon_path)
		except Exception:
			PyImGui.set_cursor_screen_pos(draw_pos[0] + 6.0, draw_pos[1] + 8.0)
			PyImGui.text("CM")

		PyImGui.set_cursor_screen_pos(cursor_x, cursor_y)
		clicked_toggle = PyImGui.invisible_button("##XunlaiSorterToggleButton", icon_window_size, icon_window_size)

		if clicked_toggle:
			if Map.IsOutpost() or Map.IsGuildHall():
				SORTER_STATE = not SORTER_STATE

				_tree = BehaviorTree(BTNodes.Bags.SortBags(bags=STORAGE_BAGS))

		if PyImGui.is_item_hovered():
			if PyImGui.begin_tooltip():
				if Map.IsOutpost() or Map.IsGuildHall():
					PyImGui.text("Start Sort" if not SORTER_STATE else "Sorting")
				else:
					PyImGui.text("Not available")
				PyImGui.end_tooltip()
	PyImGui.end()
	PyImGui.pop_style_var(1)


def _draw_window():
	"""Main per-frame render function: draws the icon."""

	if not GLOBAL_CACHE.Inventory.IsStorageOpen():
		return

	_draw_toggle_icon_window()


def _tick_tree():
	global _tree
	global SORTER_STATE
	if Map.IsOutpost() or Map.IsGuildHall():
		if _tree and SORTER_STATE:
			try:
				state = _tree.tick()
				if state != BehaviorTree.NodeState.RUNNING:
					Py4GW.Console.Log(MODULE_NAME, f"Behavior tree '{_tree.root.name}' finished with state: {state.name}", Py4GW.Console.MessageType.Success if state == BehaviorTree.NodeState.SUCCESS else Py4GW.Console.MessageType.Warning)
					_tree = None
					SORTER_STATE = False

			except Exception as e:
				Py4GW.Console.Log(MODULE_NAME, f"Error ticking behavior tree: {e}")


def main():
	try:
		_draw_window()
		_tick_tree()
	except Exception as e:
		ConsoleLog(MODULE_NAME, f"Error in main: {str(e)}", Console.MessageType.Error)


if __name__ == "__main__":
	main()
