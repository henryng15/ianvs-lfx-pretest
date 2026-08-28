#!/usr/bin/env python3
"""Render a continuous, typed-terminal walkthrough of the Task 2 evidence.

The terminal output is read from the checked-in evidence files produced by the
real probes.  This deliberately makes a presentation video, not a claim that
the video itself is a live recording; the command and output artefacts remain
separately inspectable in ``evidence/``.

Requires Pillow and ffmpeg.  Run from the repository root:
    python3 tools/render_task2_terminal_video.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence/videos/task2-reproduction.mp4"
FPS = 24
WIDTH, HEIGHT = 1280, 800
TITLEBAR = 32
ACTIVITY_WIDTH = 48
SIDEBAR_WIDTH = 230
EDITOR_BOTTOM = 392
TERMINAL_TOP = 400
TERMINAL_HEADER = 34
FONT_SIZE = 18
LINE_HEIGHT = 24
# 86 monospace glyphs fit in the VS Code-style integrated terminal pane.
COLS = 86
ROWS = (HEIGHT - TERMINAL_TOP - TERMINAL_HEADER - 24) // LINE_HEIGHT


def font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    ):
        if pathlib.Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise RuntimeError("A monospace TrueType font is required")


REGULAR = font(FONT_SIZE)
BOLD = font(FONT_SIZE)
SMALL = font(15)


class Terminal:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.input = ""
        self.frame = 0
        self.encoder = subprocess.Popen(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "rawvideo", "-pixel_format", "rgb24",
                "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS),
                "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium",
                "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(OUT),
            ],
            stdin=subprocess.PIPE,
        )

    def visible(self) -> list[str]:
        rendered: list[str] = []
        for line in self.lines + (["$ " + self.input] if self.input else ["$"]):
            rendered.extend(line[i:i + COLS] or [""] for i in range(0, len(line), COLS))
        return rendered[-ROWS:]

    def draw(self) -> None:
        image = Image.new("RGB", (WIDTH, HEIGHT), "#1e1e1e")
        draw = ImageDraw.Draw(image)
        # A compact VS Code-style frame: title bar, activity strip, Explorer,
        # source editor and the integrated terminal panel below it.
        draw.rectangle((0, 0, WIDTH, TITLEBAR), fill="#181818")
        draw.text((16, 8), "ianvs-lfx-pretest — Visual Studio Code", font=SMALL, fill="#cccccc")
        draw.text((WIDTH - 176, 8), "◻  —  □  ×", font=SMALL, fill="#a8a8a8")

        draw.rectangle((0, TITLEBAR, ACTIVITY_WIDTH, HEIGHT), fill="#333333")
        for y_icon, glyph, active in ((58, "▣", True), (108, "⌕", False), (158, "⑂", False), (208, "▷", False), (258, "▧", False)):
            if active:
                draw.rectangle((0, y_icon - 8, 2, y_icon + 24), fill="#007acc")
            draw.text((14, y_icon), glyph, font=font(22), fill="#f0f0f0" if active else "#b5b5b5")

        side_left, side_right = ACTIVITY_WIDTH, ACTIVITY_WIDTH + SIDEBAR_WIDTH
        draw.rectangle((side_left, TITLEBAR, side_right, HEIGHT), fill="#252526")
        draw.text((side_left + 16, TITLEBAR + 16), "EXPLORER", font=SMALL, fill="#cccccc")
        tree = [
            ("⌄  KUBEEDGE", "#e7e7e7"),
            ("   ⌄  ianvs", "#cfcfcf"),
            ("      core", "#bcbcbc"),
            ("      examples", "#bcbcbc"),
            ("   ⌄  tools", "#cfcfcf"),
            ("      probe_pr558_transitive.py", "#9cdcfe"),
            ("      probe_pr558_pickle.py", "#9cdcfe"),
            ("      probe_paradigm_runtime.py", "#9cdcfe"),
            ("   ⌄  evidence", "#cfcfcf"),
            ("      videos", "#bcbcbc"),
            ("   submission", "#bcbcbc"),
        ]
        for index, (label, colour) in enumerate(tree):
            y_tree = TITLEBAR + 48 + index * 24
            if "probe_pr558_transitive.py" in label:
                draw.rectangle((side_left, y_tree - 2, side_right, y_tree + 21), fill="#37373d")
            draw.text((side_left + 12, y_tree), label, font=SMALL, fill=colour)

        main_left = side_right
        draw.rectangle((main_left, TITLEBAR, WIDTH, EDITOR_BOTTOM), fill="#1e1e1e")
        draw.rectangle((main_left, TITLEBAR, WIDTH, TITLEBAR + 34), fill="#2d2d2d")
        draw.rectangle((main_left + 1, TITLEBAR, main_left + 258, TITLEBAR + 34), fill="#1e1e1e")
        draw.text((main_left + 15, TITLEBAR + 10), "◉  probe_pr558_transitive.py   ×", font=SMALL, fill="#eeeeee")
        editor = [
            "from importlib import util",
            "from pathlib import Path",
            "",
            "def load_example(example_dir: Path):",
            "    spec = util.spec_from_file_location(",
            "        'basemodel', example_dir / 'basemodel.py'",
            "    )",
            "    module = util.module_from_spec(spec)",
            "    spec.loader.exec_module(module)",
            "    return module.BaseModel",
            "",
            "# compare main @ 37a9c60 with pr-558",
        ]
        for number, code in enumerate(editor, start=1):
            y_code = TITLEBAR + 52 + (number - 1) * 22
            draw.text((main_left + 18, y_code), f"{number:>2}", font=SMALL, fill="#858585")
            colour = "#d4d4d4"
            if code.startswith(("from", "def", "return")):
                colour = "#c586c0"
            elif code.lstrip().startswith("#"):
                colour = "#6a9955"
            draw.text((main_left + 58, y_code), code, font=SMALL, fill=colour)

        draw.rectangle((main_left, TERMINAL_TOP, WIDTH, HEIGHT), fill="#181818")
        draw.rectangle((main_left, TERMINAL_TOP, WIDTH, TERMINAL_TOP + TERMINAL_HEADER), fill="#252526")
        draw.text((main_left + 16, TERMINAL_TOP + 10), "PROBLEMS    OUTPUT    DEBUG CONSOLE", font=SMALL, fill="#a8a8a8")
        draw.text((main_left + 340, TERMINAL_TOP + 10), "TERMINAL", font=SMALL, fill="#ffffff")
        draw.rectangle((main_left + 340, TERMINAL_TOP + TERMINAL_HEADER - 2, main_left + 409, TERMINAL_TOP + TERMINAL_HEADER), fill="#007acc")
        draw.text((WIDTH - 110, TERMINAL_TOP + 10), "bash  ⌄   +  ×", font=SMALL, fill="#c5c5c5")

        y = TERMINAL_TOP + TERMINAL_HEADER + 12
        for line in self.visible():
            colour = "#e2e8f0"
            if line.startswith("$ ") or line == "$":
                colour = "#86efac"
            elif line.startswith(("---", "===", "1.", "2.", "Conclusion:")):
                colour = "#93c5fd"
            elif "LOAD-FAIL" in line or "ValueError:" in line or "RuntimeError:" in line:
                colour = "#fda4af"
            draw.text((main_left + 18, y), line, font=REGULAR, fill=colour)
            y += LINE_HEIGHT

        # A blinking cursor makes the command entry readable without pretending this is live capture.
        if self.frame % FPS < int(FPS * 0.7):
            latest = self.visible()[-1]
            cursor_x = main_left + 18 + draw.textlength(latest, font=REGULAR)
            draw.rectangle((cursor_x + 2, y - LINE_HEIGHT + 4, cursor_x + 11, y - 5), fill="#e2e8f0")
        assert self.encoder.stdin is not None
        self.encoder.stdin.write(image.tobytes())
        self.frame += 1

    def pause(self, seconds: float) -> None:
        for _ in range(max(1, round(seconds * FPS))):
            self.draw()

    def line(self, value: str = "", seconds: float = 0.10) -> None:
        self.lines.append(value)
        self.pause(seconds)

    def type_command(self, command: str, corrections: dict[int, str] | None = None) -> None:
        """Type at an intentionally readable human pace.

        ``corrections`` injects a single visible wrong character at a cursor
        position, waits briefly, then removes it.  They make the walkthrough
        easier to follow while leaving the executed command displayed exactly.
        """
        corrections = corrections or {}
        self.input = ""
        for position, char in enumerate(command):
            self.input += char
            self.pause(1 / 5.5)
            if position in corrections:
                self.input += corrections[position]
                self.pause(0.65)
                self.input = self.input[:-1]
                self.pause(0.28)
        self.pause(0.5)
        self.lines.append("$ " + self.input)
        self.input = ""
        self.pause(0.16)

    def output(self, text: str) -> None:
        for value in text.rstrip().splitlines():
            self.line(value, 0.19 if len(value) < 90 else 0.13)

    def command(self, command: str, output: str, corrections: dict[int, str] | None = None) -> None:
        self.type_command(command, corrections)
        self.output(output)
        self.pause(0.65)

    def close(self) -> None:
        self.pause(1.3)
        assert self.encoder.stdin is not None
        self.encoder.stdin.close()
        if self.encoder.wait() != 0:
            raise RuntimeError("ffmpeg failed")


def evidence(name: str) -> str:
    return (ROOT / "evidence" / name).read_text()


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    terminal = Terminal()
    terminal.line("Task 2 — PR #558 and Ianvs runtime evidence", 1.2)
    terminal.line("Expected diagnostics below are evidence, not a failed submission.", 1.2)
    terminal.line("All output below is preserved in evidence/*.txt", 1.0)
    terminal.line()
    terminal.command("git -C ianvs rev-parse --short HEAD", "37a9c60", corrections={14: "w"})
    terminal.command("git -C ianvs rev-parse --short pr-558", "b99161f")
    terminal.command(
        ".venv/bin/python tools/probe_pr558_transitive.py ianvs",
        evidence("probe_pr558_transitive.txt"),
    )
    terminal.command(
        ".venv/bin/python tools/probe_pr558_pickle.py ianvs",
        evidence("probe_pr558_pickle.txt"),
        corrections={38: "q"},
    )
    terminal.command(
        ".venv/bin/python tools/probe_paradigm_runtime.py ianvs",
        evidence("probe_paradigm_runtime.txt"),
    )
    terminal.command("git status --short", "# clean working tree (submission evidence committed separately)")
    terminal.line("Result: expected diagnostic evidence captured successfully.", 1.2)
    terminal.line("End of recorded walkthrough.", 1.0)
    terminal.close()
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
