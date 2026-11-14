PROMPT: chapter 1.2 of the @README.md is wrong. The 2 demo videos were not included in the commit. Rewrite and make sure the other 2 readme files are the same as the one in the root of the repository. They are in @docs/ and @dist/
TIMESTAMP: Sat 14 Nov 2026 20:20 CET

RESULT
- README.md 1.2 rewritten: repo holds scripts and render code, not the rendered videos; output/*.mp4/.srt and build/ are git-ignored and created locally by the pipeline (section 10, macOS).
- 1.1 lists docs/README.md; 4.6 and 6.1 notes updated: root, docs/ and dist/ READMEs are identical copies.
- docs/README.md and dist/README.md overwritten with the root README (identical md5). dist/README.md recreated so it ships in the zip.
- Zip rebuilt (README inside identical to root), SHA256SUMS updated and verified; 31 tests OK.
