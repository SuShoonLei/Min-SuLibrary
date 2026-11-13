/**
 * Starts the one home-page crystal ball. The logo and the CSS ring paint
 * before this module runs. Settings live here so the look stays in one place.
 */
import { createCrystalBall } from "./crystal-ball.js";

const BALL_CONFIG = {
  preset: "frost",
  theme: "light",
  color: "#E58BB4",
  size: 0.92,
  particleShape: "round",
  motion: "fall",
  interactive: true,
  hoverStrength: 0.7
};

const NUMBER_KEYS = [
  "size",
  "strands",
  "crackle",
  "flares",
  "glow",
  "sparks",
  "particleCount",
  "fill",
  "depth",
  "sway",
  "twinkle",
  "haze",
  "speed",
  "dustSpeed",
  "hoverStrength"
];
const STRING_KEYS = ["preset", "color", "theme", "motion", "particleShape"];
const BOOL_KEYS = ["interactive", "intro", "paused"];

const nodes = document.querySelectorAll("[data-crystal-ball]");
const el = nodes[0];
if (el) {
  const stage = el.closest(".hero-stage");
  let ball = null;

  const readOptions = () => {
    const options = { ...BALL_CONFIG };
    STRING_KEYS.forEach((key) => {
      const value = el.dataset[key];
      if (value) options[key] = value;
    });
    NUMBER_KEYS.forEach((key) => {
      const value = el.dataset[key];
      if (value === undefined || value === "") return;
      const number = Number(value);
      if (!Number.isNaN(number)) options[key] = number;
    });
    BOOL_KEYS.forEach((key) => {
      if (el.dataset[key] === "true") options[key] = true;
      if (el.dataset[key] === "false") options[key] = false;
    });
    // Frost's own count is fine on a desktop. A phone gets a lighter cloud.
    if (el.dataset.particleCount === undefined && window.innerWidth < 640) {
      options.particleCount = 8000;
    }
    return options;
  };

  const applyColor = (options) => {
    if (stage && options.color) stage.style.setProperty("--ball-color", options.color);
  };

  try {
    const initial = readOptions();
    applyColor(initial);
    ball = createCrystalBall(el, initial);
  } catch (error) {
    console.error(error);
  }

  const onResize = () => {
    if (!ball) return;
    const options = readOptions();
    applyColor(options);
    ball.update({ particleCount: options.particleCount });
  };
  const widthQuery = window.matchMedia("(max-width: 639px)");
  widthQuery.addEventListener("change", onResize);

  const stop = () => {
    widthQuery.removeEventListener("change", onResize);
    ball?.destroy();
    ball = null;
  };
  window.addEventListener("pagehide", stop, { once: true });
}
