// Small page behavior: confirm deletes, scroll to a failed form, mark the
// section in view, and swap a broken image for the placeholder.
// Motion belongs in animations.js, which is intentionally empty for now.

(function () {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.getAttribute("data-confirm") || "Remove this?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  const errored = document.querySelector("[data-form-error]");
  if (errored) {
    errored.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
  }

  document.querySelectorAll("img[data-fallback-src]").forEach((img) => {
    img.addEventListener("error", () => {
      const fallback = img.getAttribute("data-fallback-src");
      if (!fallback || img.src.endsWith(fallback)) {
        return;
      }
      img.src = fallback;
    });
  });

  const links = Array.from(document.querySelectorAll(".chapter-nav a"));
  const sections = links
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);
  if (!links.length || !sections.length) {
    return;
  }

  // The section that has reached the sticky bar is the current one.
  // A tall section above can still intersect the viewport, so an
  // intersection observer by itself highlights the wrong link.
  const markCurrent = () => {
    const nav = document.querySelector(".chapter-nav");
    const line = (nav ? nav.getBoundingClientRect().bottom : 0) + 8;
    let current = sections[0];
    sections.forEach((section) => {
      if (section.getBoundingClientRect().top <= line) {
        current = section;
      }
    });
    links.forEach((link) => {
      const on = link.getAttribute("href") === `#${current.id}`;
      if (on) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  };

  markCurrent();
  document.addEventListener("scroll", markCurrent, { passive: true });
})();
