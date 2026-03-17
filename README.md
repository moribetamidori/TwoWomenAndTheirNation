# Two Women and Their Nation

A GitHub-friendly manuscript layout for a novel project.

## Structure

- `manuscript/` holds the actual book text
- `notes/` holds worldbuilding, research, and planning
- `meta/` holds publishing and project conventions

## Suggested Workflow

1. Put each chapter in its own Markdown file inside `manuscript/chapters/`
2. Keep filenames ordered with leading zeros, such as `01-prologue.md`
3. Use `manuscript/index.md` as the table of contents
4. Keep spoilers, cut scenes, and planning material out of chapter files

## Current Layout

```text
.
├── README.md
├── manuscript
│   ├── index.md
│   └── chapters
│       ├── 00-front-matter.md
│       └── 01-chapter-one.md
├── notes
│   ├── characters.md
│   ├── timeline.md
│   └── worldbuilding.md
└── meta
    ├── publishing-plan.md
    └── style-guide.md
```

## Notes

If you already have draft chapters elsewhere, move them into `manuscript/chapters/` and keep the numeric prefix so GitHub displays them in reading order.
