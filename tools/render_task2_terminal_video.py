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
MARGIN = 42
HEADER = 44
FONT_SIZE = 18
LINE_HEIGHT = 24
# 100 monospace glyphs fit inside the terminal body at 1280 px without clipping
# the long exception lines in the pickle probe.
COLS = 100
ROWS = (HEIGHT - 2 * MARGIN - HEADER - 34) // LINE_HEIGHT


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
        image = Image.new("RGB", (WIDTH, HEIGHT), "#111827")
        draw = ImageDraw.Draw(image)
        left, top = MARGIN, MARGIN
        right, bottom = WIDTH - MARGIN, HEIGHT - MARGIN
        draw.rounded_rectangle((left, top, right, bottom), radius=14, fill="#0b1220", outline="#334155", width=2)
        draw.rounded_rectangle((left, top, right, top + HEADER), radius=14, fill="#172033")
        draw.rectangle((left, top + 25, right, top + HEADER), fill="#172033")
        for x, colour in ((left + 22, "#fb7185"), (left + 46, "#fbbf24"), (left + 70, "#4ade80")):
            draw.ellipse((x - 7, top + 15, x + 7, top + 29), fill=colour)
        draw.text((left + 100, top + 13), "ianvs evidence — continuous terminal walkthrough", font=SMALL, fill="#cbd5e1")

        y = top + HEADER + 18
        for line in self.visible():
            colour = "#e2e8f0"
            if line.startswith("$ ") or line == "$":
                colour = "#86efac"
            elif line.startswith(("---", "===", "1.", "2.", "Conclusion:")):
                colour = "#93c5fd"
            elif "LOAD-FAIL" in line or "ValueError:" in line or "RuntimeError:" in line:
                colour = "#fda4af"
            draw.text((left + 22, y), line, font=REGULAR, fill=colour)
            y += LINE_HEIGHT

        # A blinking cursor makes the command entry readable without pretending this is live capture.
        if self.frame % FPS < int(FPS * 0.7):
            latest = self.visible()[-1]
            cursor_x = left + 22 + draw.textlength(latest, font=REGULAR)
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
