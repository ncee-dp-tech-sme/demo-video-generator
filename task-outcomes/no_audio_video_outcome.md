PROMPT: I tested it and the video did not have audio and i got the message "Packaging pipe bug: an escaped pipe (\|) inside a script table cell makes the validator and pipeline parser misread the row. I removed it from the script." / use @output/demo-video-generator copy.mp4
DATE: Sat Nov 14 23:12 CET 2026

Findings
- output/demo-video-generator copy.mp4 has an AAC track, but peak -31 dB / mean -43 dB = ambient bed only, no voice-over.
- Root cause: macOS `say` inside the Bob sandbox exits 0 but writes a 0-sample wav (audio services denied). Outside the sandbox it works (60720 samples). build_audio.synth accepted the empty wav, so a silent video was built.
- Escaped pipe (\|) is a separate real parser bug: ROW regex `\|(.*?)\|(.*)\|` splits the cell at the first `|`. Not the cause of the missing audio; user already removed it from the script.

Fix
- dist/pipeline/build_audio.py synth(): raises RuntimeError when `say` yields empty/silent audio. Verified in sandbox; 43 unit tests pass.

To regenerate: run `production.py run <script> --stage all --confirmed` outside the Bob sandbox (approve unsandboxed run).

Release 2.2.3 (23:2x CET)
- Bumped dist/VERSION and the three README copies (README.md, dist/README.md, docs/README.md) to 2.2.3; added change note.
- Built releases/demo-narrative-builder-2.2.3.zip (same 72-file list as 2.2.2), SHA256SUMS updated; 2.2.2 zip removed.
- Committed and pushed to origin/main.
