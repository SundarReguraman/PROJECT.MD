# PROJECT.MD demo recording. Re-record from the repo root with:
#   vhs docs/demo/demo.tape
# Requires VHS (brew install vhs). The demo writes its context files to
# /tmp/project-md-demo, never into this repository.

Output docs/demo/demo.mp4
Output docs/demo/demo.gif

Set Shell "bash"
Set FontSize 13
Set Width 1280
Set Height 1240
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms
Set PlaybackSpeed 1.0

Hide
Type "export PYTHONPATH=$PWD PS1='\[\e[1;36m\]$ \[\e[0m\]' && rm -rf /tmp/project-md-demo && mkdir -p /tmp/project-md-demo && cd /tmp/project-md-demo && clear"
Enter
Sleep 500ms
Show

# Scene 1: one plain-English sentence in, full pre-flight out.
Type "# Describe what you want to build. That's the only input."
Enter
Sleep 800ms
Type `python3 -m project_md.cli "An app to transcribe doctor handwriting"`
Sleep 600ms
Enter
Sleep 7s

# Scene 2: the idea names a known dead end.
Type "clear"
Enter
Type "# Now ask for the OpenCV approach that dooms most handwriting projects..."
Enter
Sleep 800ms
Type `python3 -m project_md.cli "Use OpenCV contours to read handwritten notes" --no-write`
Sleep 600ms
Enter
Sleep 7s

# Scene 3: native context files for every assistant.
Type "clear"
Enter
Type "# Context files for Claude Code, Cursor, Antigravity and Bob:"
Enter
Sleep 600ms
Type "find . -type f | sort"
Enter
Sleep 2500ms
Type "head -32 CLAUDE.md"
Enter
Sleep 8s
