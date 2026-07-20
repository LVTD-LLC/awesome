const FIRST_LIKE_SELECTOR = '[data-first-repository-like="true"]';

export function initRepositoryLikes() {
  animateFirstRepositoryLike(document);

  document.addEventListener("htmx:afterSwap", () => {
    animateFirstRepositoryLike(document);
  });
}

function animateFirstRepositoryLike(root) {
  root.querySelectorAll(FIRST_LIKE_SELECTOR).forEach((form) => {
    form.removeAttribute("data-first-repository-like");

    if (prefersReducedMotion()) {
      return;
    }

    const heart = form.querySelector("[data-repository-like-heart]");
    heart?.animate(
      [
        { transform: "scale(1)" },
        { transform: "scale(1.3)", offset: 0.45 },
        { transform: "scale(0.94)", offset: 0.7 },
        { transform: "scale(1)" },
      ],
      { duration: 520, easing: "ease-out" },
    );

    showFirstSaveCount(form);
  });
}

function showFirstSaveCount(form) {
  const badge = document.createElement("span");
  badge.setAttribute("aria-hidden", "true");
  badge.textContent = "0 saved";
  Object.assign(badge.style, {
    background: "#166534",
    borderRadius: "9999px",
    color: "#ffffff",
    fontSize: "0.6875rem",
    fontWeight: "700",
    lineHeight: "1",
    padding: "0.35rem 0.5rem",
    pointerEvents: "none",
    position: "absolute",
    right: "-0.5rem",
    top: "-0.75rem",
    whiteSpace: "nowrap",
    zIndex: "10",
  });

  form.style.position = "relative";
  form.appendChild(badge);
  badge.animate(
    [
      { opacity: 0, transform: "translateY(0.35rem)" },
      { opacity: 1, transform: "translateY(0)" },
    ],
    { duration: 180, easing: "ease-out", fill: "forwards" },
  );

  window.setTimeout(() => {
    badge.textContent = "1 saved";
    badge.animate(
      [
        { transform: "translateY(0.25rem)" },
        { transform: "translateY(0)" },
      ],
      { duration: 180, easing: "ease-out" },
    );
  }, 220);

  window.setTimeout(() => {
    const animation = badge.animate(
      [
        { opacity: 1, transform: "translateY(0)" },
        { opacity: 0, transform: "translateY(-0.35rem)" },
      ],
      { duration: 220, easing: "ease-in", fill: "forwards" },
    );
    animation.addEventListener("finish", () => badge.remove(), { once: true });
  }, 1400);
}

function prefersReducedMotion() {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}
