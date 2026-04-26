pragma Singleton

import qs.config
import Quickshell
import Quickshell.Services.SystemTray

Singleton {
    function shouldHide(item): bool {
        const text = [item.id, item.title, item.tooltipTitle, item.tooltipDescription, item.icon].map(v => String(v ?? "")).join(" ").toLowerCase();

        for (const hidden of Config.bar.tray.hiddenItems) {
            const needle = String(hidden ?? "").toLowerCase();

            if (needle !== "" && text.includes(needle))
                return true;
        }

        return false;
    }

    function visibleItems(items, hiddenItems: list<var>): list<SystemTrayItem> {
        return [...items].filter(item => !shouldHide(item, hiddenItems));
    }
}
