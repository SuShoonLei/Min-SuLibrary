"""Site-wide settings that templates and routes share."""

from __future__ import annotations

from datetime import date

SITE_NAME = "Min&Su Library"
SITE_DESCRIPTION = "A living library of our chapters."

# The circular particle ball. Off: the home logo uses a silhouette glow instead.
SHOW_CRYSTAL_BALL = False

# The day we started dating, and the day we met. Chapter ranges live in db/seed.sql.
TOGETHER_SINCE = date(2023, 11, 1)
MET_ON = date(2023, 8, 31)

# Sampled from public/assets/brand/logo.png (the cloud and the pink banner).
ACCENT_MIN = "#C2E0EA"
ACCENT_SU = "#F8BDB2"

PEOPLE = (
    {"slug": "min", "display_name": "Min", "accent_color": ACCENT_MIN},
    {"slug": "su", "display_name": "Su", "accent_color": ACCENT_SU},
)


def days_together(today: date | None = None) -> int:
    """Days together, counting the anniversary date itself as day one."""
    current = today or date.today()
    return (current - TOGETHER_SINCE).days + 1
