"""Keep the theme faithful to Monokai Pro and installable from git."""

import re
import shutil
import subprocess
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLORS = tomllib.loads((ROOT / "colors.toml").read_text())

# Monokai Pro, default filter: shades darkest to lightest, then the six accents.
MONOKAI_PRO = {
    "#19181a", "#221f22", "#2d2a2e", "#403e41", "#5b595c",
    "#727072", "#939293", "#c1c0c0", "#fcfcfa",
    "#ff6188", "#fc9867", "#ffd866", "#a9dc76", "#78dce8", "#ab9df2",
}  # fmt: skip
# Omarchy asks for brown, which Monokai Pro lacks: orange mixed 50% with black.
DERIVED = {"brown": "#7e4c34"}
REQUIRED = {
    "accent", "selection", "muted",
    "background", "dark_background", "darker_background", "lighter_background",
    "foreground", "dark_foreground", "light_foreground", "bright_foreground",
    "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown",
    "bright_red", "bright_yellow", "bright_green",
    "bright_cyan", "bright_blue", "bright_magenta",
}  # fmt: skip
# `omarchy-theme-set` drops these from a theme cloned by `omarchy theme install`.
DENIED_NAMES = {
    "alacritty.toml",
    "foot.ini",
    "ghostty.conf",
    "kitty.conf",
    "vscode.json",
}
YARU = re.compile(
    r"Yaru(-(blue|dark|magenta|olive|prussiangreen|purple|red|sage|wartybrown|yellow))?"
)


def shipped_files():
    return [
        path
        for path in ROOT.rglob("*")
        if ".git" not in path.relative_to(ROOT).parts
        and "__pycache__" not in path.parts
    ]


class ThemeTest(unittest.TestCase):
    def test_palette_is_complete_dark_and_monokai_pro(self):
        self.assertEqual(COLORS.pop("mode"), "dark")
        self.assertEqual(set(COLORS), REQUIRED)
        for key, value in COLORS.items():
            with self.subTest(key=key):
                self.assertRegex(value, r"^#[0-9a-f]{6}$")
                self.assertIn(value, MONOKAI_PRO | {DERIVED.get(key)})
        COLORS["mode"] = "dark"

    def test_terminal_mapping_follows_official_palette(self):
        self.assertEqual(COLORS["background"], "#2d2a2e")
        self.assertEqual(COLORS["foreground"], "#fcfcfa")
        self.assertEqual(COLORS["blue"], COLORS["orange"])
        for name in ("red", "yellow", "green", "cyan", "blue", "magenta"):
            self.assertEqual(COLORS[f"bright_{name}"], COLORS[name])

    def test_ships_only_what_an_installed_theme_keeps(self):
        for path in shipped_files():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(path.is_symlink())
                self.assertNotEqual(path.suffix, ".lua")
                self.assertNotIn(path.name, DENIED_NAMES)

    def test_assets(self):
        self.assertRegex(
            (ROOT / "icons.theme").read_text().strip(), f"^{YARU.pattern}$"
        )
        backgrounds = sorted((ROOT / "backgrounds").iterdir())
        self.assertTrue(backgrounds)
        for path in backgrounds:
            self.assertIn(path.suffix, {".jpg", ".png", ".webp"})

    @unittest.skipUnless(
        shutil.which("omarchy-theme-color"), "Omarchy is not installed"
    )
    def test_omarchy_resolves_the_palette(self):
        output = subprocess.run(
            ["omarchy-theme-color", "--file", str(ROOT / "colors.toml"), "--all"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        resolved = dict(line.split("\t", 1) for line in output.splitlines())
        self.assertEqual(resolved["color0"], "#2d2a2e")
        self.assertEqual(resolved["color4"], "#fc9867")
        self.assertEqual(resolved["color8"], "#727072")
        self.assertEqual(resolved["cursor"], "#fcfcfa")
        self.assertEqual(resolved["theme_type"], "dark")


if __name__ == "__main__":
    unittest.main()
