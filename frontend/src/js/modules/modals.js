const MODAL_CONFIGS = [
  {
    modalSelector: "[data-highlighted-repo-modal]",
    openSelector: "[data-highlighted-repo-modal-open]",
    closeSelector: "[data-highlighted-repo-modal-close]",
  },
  {
    modalSelector: "[data-sponsor-modal]",
    openSelector: "[data-sponsor-modal-open]",
    closeSelector: "[data-sponsor-modal-close]",
  },
];

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(", ");

const activeModals = [];
let documentKeydownListenerReady = false;

export function initModals(root = document) {
  initDocumentKeydownListener();

  MODAL_CONFIGS.forEach((config) => {
    const modal = root.querySelector(config.modalSelector);
    if (!modal || modal.dataset.modalReady === "true") {
      return;
    }

    modal.dataset.modalReady = "true";
    const dialog = modal.querySelector("[role='dialog']") || modal;
    let previousFocus = null;
    let modalController = null;

    const focusableElements = () =>
      Array.from(modal.querySelectorAll(FOCUSABLE_SELECTOR)).filter((element) => {
        const rect = element.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && !element.hasAttribute("disabled");
      });

    const focusInitialElement = () => {
      const firstFocusable = focusableElements()[0];
      if (firstFocusable) {
        firstFocusable.focus();
        return;
      }

      if (!dialog.hasAttribute("tabindex")) {
        dialog.setAttribute("tabindex", "-1");
      }
      dialog.focus();
    };

    const open = () => {
      if (modal.getAttribute("aria-hidden") === "false") {
        focusInitialElement();
        return;
      }

      previousFocus = document.activeElement;
      modal.classList.remove("hidden");
      modal.classList.add("flex");
      modal.setAttribute("aria-hidden", "false");
      activeModals.push(modalController);
      syncBodyScrollLock();
      requestAnimationFrame(focusInitialElement);
    };

    const close = () => {
      if (modal.getAttribute("aria-hidden") !== "false") {
        return;
      }

      modal.classList.add("hidden");
      modal.classList.remove("flex");
      modal.setAttribute("aria-hidden", "true");
      removeActiveModal(modalController);
      syncBodyScrollLock();

      if (previousFocus && typeof previousFocus.focus === "function" && document.contains(previousFocus)) {
        previousFocus.focus();
      }
      previousFocus = null;
    };

    const trapFocus = (event) => {
      if (event.key !== "Tab" || modal.getAttribute("aria-hidden") === "true") {
        return;
      }

      const focusables = focusableElements();
      if (focusables.length === 0) {
        event.preventDefault();
        dialog.focus();
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      } else if (!modal.contains(document.activeElement)) {
        event.preventDefault();
        first.focus();
      }
    };

    modalController = { close, trapFocus };

    root
      .querySelectorAll(config.openSelector)
      .forEach((button) => button.addEventListener("click", open));
    modal
      .querySelectorAll(config.closeSelector)
      .forEach((button) => button.addEventListener("click", close));
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        close();
      }
    });
  });
}

function initDocumentKeydownListener() {
  if (documentKeydownListenerReady) {
    return;
  }

  documentKeydownListenerReady = true;
  document.addEventListener("keydown", (event) => {
    const activeModal = activeModals[activeModals.length - 1];
    if (!activeModal) {
      return;
    }

    if (event.key === "Escape") {
      activeModal.close();
      return;
    }

    activeModal.trapFocus(event);
  });
}

function removeActiveModal(modalController) {
  const index = activeModals.lastIndexOf(modalController);
  if (index !== -1) {
    activeModals.splice(index, 1);
  }
}

function syncBodyScrollLock() {
  document.body.classList.toggle("overflow-hidden", activeModals.length > 0);
}
