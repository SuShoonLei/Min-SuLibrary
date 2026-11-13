// Animation hooks.
//
// Markup is already marked for a later motion pass. Sections, cards, and
// other blocks carry data-animate (for example data-animate="fade-up").
// When you add motion, query [data-animate] from this file. The templates
// should not need to change.
//
// If window.matchMedia("(prefers-reduced-motion: reduce)").matches,
// leave every element as it is. base.css also short-circuits animation
// and smooth scrolling for that preference.
