# Instruction for the OTHER laptop's Claude — back up its memory

Hand the block below to Claude Code running in this kit folder on the *other*
laptop. It produces a memory dump alongside the one already saved for
`john-Latitude-5450`, named by that laptop's own hostname so the two never
collide in Dropbox.

(Memory is machine-local and is NOT synced by Dropbox, so each laptop must export
its own.)

---

Please back up your persistent memory for this project so it can transfer between
laptops. Steps:

1. Find your memory store (it's machine-local, not in Dropbox) — the directory
   containing `MEMORY.md`, typically
   `~/.claude/projects/<this-project-slug>/memory/`.
2. Run `hostname` to get this machine's name.
3. Create a subfolder in the kit named `claude_memories_<hostname>/` (use the
   actual hostname — do NOT reuse `claude_memories_john-Latitude-5450`, that's
   the other laptop's).
4. Copy all `*.md` files from your memory store into that subfolder.
5. Add a `README_CLAUDE_MEMORIES.md` explaining what the folder is, this
   machine's hostname and username, the original memory-dir path, and
   step-by-step restore instructions for another machine.
6. Verify the copies match the originals (`diff`), and check `lsblk` — if any
   memory hard-codes a drive node like `/dev/sda`, confirm it's correct for this
   machine and fix it in the copy if not.
7. Confirm the folder name and list its contents back to me.
