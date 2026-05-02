from Py4GWCoreLib import ConsoleLog, Console
from Py4GWCoreLib import IniManager
from Sources.inventory_managment.config.inventory_utils_config import InventoryUtilsConfig
from Sources.inventory_managment.json_helper import string_to_dict, dict_to_string

INVENTORY_UTILS_CONFIG = "my_inventory_utils_config"
DEFAULT_JSON = "inventory_utils_config"

INI_PATH = "Widgets/InventoryManagement/BotHubStyle"


# TODO Listeners


def inventory_util_config_load_json() -> InventoryUtilsConfig | None:
    global INVENTORY_UTILS_CONFIG, DEFAULT_JSON
    inventory_utils_config: InventoryUtilsConfig | None
    data: str | None = InventoryConfigSettings().read(INVENTORY_UTILS_CONFIG, DEFAULT_JSON)
    if data is not None:
        inventory_utils_config = string_to_dict(data)
    else:
        inventory_utils_config = InventoryUtilsConfig()

    if not inventory_utils_config:
        inventory_utils_config = InventoryUtilsConfig()

    return inventory_utils_config


def persist_configuration_as_global(inventory_utils_config: InventoryUtilsConfig):
    global INVENTORY_UTILS_CONFIG, DEFAULT_JSON
    InventoryConfigSettings().write_global(INVENTORY_UTILS_CONFIG, DEFAULT_JSON, dict_to_string(inventory_utils_config.__dict__))
    ConsoleLog("InventoryConfigSettings", "configuration saved as global", Console.MessageType.Info)


def persist_configuration_for_account(inventory_utils_config: InventoryUtilsConfig):
    global INVENTORY_UTILS_CONFIG, DEFAULT_JSON
    InventoryConfigSettings().write_for_account(INVENTORY_UTILS_CONFIG, DEFAULT_JSON, dict_to_string(inventory_utils_config.__dict__))
    ConsoleLog("InventoryConfigSettings", "configuration saved for account", Console.MessageType.Info)


def delete_persisted_configuration():
    global INVENTORY_UTILS_CONFIG, DEFAULT_JSON
    InventoryConfigSettings().delete(INVENTORY_UTILS_CONFIG, DEFAULT_JSON)
    ConsoleLog("InventoryConfigSettings", "configuration deleted", Console.MessageType.Info)


class InventoryConfigSettings:

    def __init__(self):
        self._global_ini_filename = "inventory_global.ini"
        self._account_ini_filename = "inventory_account.ini"
        self._global_key: str = ""
        self._account_key: str = ""

    def _ensure_global_key(self) -> str:
        global INI_PATH
        """Ensure the global INI key is created and return it."""
        if not self._global_key:
            self._global_key = IniManager().ensure_global_key(INI_PATH, self._global_ini_filename)
        return self._global_key

    def _ensure_account_key(self) -> str:
        global INI_PATH
        """Ensure the account INI key is created and return it."""
        if not self._account_key:
            self._account_key = IniManager().ensure_key(INI_PATH, self._account_ini_filename)
        return self._account_key

    def read(self, top_level: str, setting_name: str) -> str | None:
        """Read a string value for a skill setting.

        First tries to read from account-specific settings, then falls back to global.

        Args:
            top_level: The name used as section (e.g., "common")
            setting_name: The setting key (e.g., "enabled")

        Returns:
            The value if found, None otherwise.
        """
        # Try account-specific first
        account_key = self._ensure_account_key()
        if account_key:
            result = IniManager().read_key(account_key, top_level, setting_name, "")
            if result != "":
                return result

        # Fall back to global
        global_key = self._ensure_global_key()
        if not global_key:
            return None
        result = IniManager().read_key(global_key, top_level, setting_name, "")
        return result if result != "" else None

    def read_or_default(self, top_level: str, setting_name: str, default: str) -> str:
        """Read a string value for a skill setting, returning a default if not found.

        Args:
            top_level: The name used as section (e.g., "common")
            setting_name: The setting key (e.g., "enabled")
            default: Default value if not found

        Returns:
            The value if found, default otherwise.
        """
        result = self.read(top_level, setting_name)
        return result if result is not None else default

    def write_global(self, top_level: str, setting_name: str, value: str) -> None:
        """Write a string value for a skill setting to global storage.

        Args:
            top_level: The name used as section (e.g., "common")
            setting_name: The setting key (e.g., "enabled")
            value: The value to write
        """
        key = self._ensure_global_key()
        if not key:
            return

        # Get the node and write directly to ini_handler for immediate disk write
        node = IniManager()._handlers.get(key)
        if node:
            node.ini_handler.write_key(top_level, setting_name, value)

    def write_for_account(self, top_level: str, setting_name: str, value: str) -> None:
        """Write a string value for a skill setting to account-specific storage.

        Args:
            top_level: The name used as section (e.g., "common")
            setting_name: The setting key (e.g., "enabled")
            value: The value to write
        """
        key = self._ensure_account_key()
        if not key:
            return

        # Get the node and write directly to ini_handler for immediate disk write
        node = IniManager()._handlers.get(key)
        if node:
            node.ini_handler.write_key(top_level, setting_name, value)

    def delete(self, top_level: str, setting_name: str) -> None:
        """Delete a setting from both global and account-specific storage.

        Args:
            top_level: The name used as section (e.g., "common")
            setting_name: The setting key (e.g., "enabled")
        """
        # Delete from account-specific
        account_key = self._ensure_account_key()
        if account_key:
            node = IniManager()._handlers.get(account_key)
            if node:
                node.ini_handler.delete_key(top_level, setting_name)

        # Delete from global
        global_key = self._ensure_global_key()
        if global_key:
            node = IniManager()._handlers.get(global_key)
            if node:
                node.ini_handler.delete_key(top_level, setting_name)