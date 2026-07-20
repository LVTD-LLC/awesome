import { initCopyButtons } from "./modules/copy.js";
import { initDocsEnhancements } from "./modules/docs.js";
import { initModals } from "./modules/modals.js";
import { initMessages } from "./modules/messages.js";
import { initNavigationShortcuts } from "./modules/shortcuts.js";
import { initRepositoryLikes } from "./modules/repository-likes.js";
import { showSourceEasterEgg } from "./modules/source-easter-egg.js";
import { initTheme } from "./modules/theme.js";
import { initUserSettingsCache } from "./modules/user-settings.js";

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initModals();
  initNavigationShortcuts();
  initMessages();
  initRepositoryLikes();
  initCopyButtons();
  initDocsEnhancements();
  initUserSettingsCache();
  showSourceEasterEgg();
});
