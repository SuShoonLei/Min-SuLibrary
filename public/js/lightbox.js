// Gallery lightbox. Opens from [data-lightbox-item], closes with the button,
// Escape (built into <dialog>), or a click on the backdrop. Arrow keys move
// between photos. Without JavaScript the grid is still visible.

(function () {
  const dialog = document.querySelector("[data-lightbox]");
  if (!dialog || typeof dialog.showModal !== "function") {
    return;
  }

  const items = Array.from(document.querySelectorAll("[data-lightbox-item]"));
  const image = dialog.querySelector("[data-lightbox-image]");
  const caption = dialog.querySelector("[data-lightbox-caption]");
  const prev = dialog.querySelector("[data-lightbox-prev]");
  const next = dialog.querySelector("[data-lightbox-next]");
  const closeButton = dialog.querySelector("[data-lightbox-close]");
  if (!image || !caption || !prev || !next || !closeButton) {
    return;
  }

  let index = 0;

  function show(nextIndex) {
    if (!items.length) {
      return;
    }
    index = (nextIndex + items.length) % items.length;
    const item = items[index];
    const text = item.getAttribute("data-caption") || "";
    const when = item.getAttribute("data-date") || "";
    const who = item.getAttribute("data-author") || "";
    image.src = item.getAttribute("data-src") || "";
    image.alt = text || "Photo";
    const parts = [text, when];
    if (who) {
      parts.push(`Added by ${who}`);
    }
    caption.textContent = parts.filter(Boolean).join(" · ");
    const onlyOne = items.length < 2;
    prev.hidden = onlyOne;
    next.hidden = onlyOne;
  }

  items.forEach((item, itemIndex) => {
    item.addEventListener("click", () => {
      show(itemIndex);
      if (!dialog.open) {
        dialog.showModal();
      }
    });
  });

  closeButton.addEventListener("click", () => dialog.close());
  prev.addEventListener("click", () => show(index - 1));
  next.addEventListener("click", () => show(index + 1));

  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      dialog.close();
    }
  });

  dialog.addEventListener("close", () => {
    image.removeAttribute("src");
    image.alt = "";
    caption.textContent = "";
  });

  dialog.addEventListener("keydown", (event) => {
    if (event.key === "ArrowRight") {
      event.preventDefault();
      show(index + 1);
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      show(index - 1);
    }
  });
})();
