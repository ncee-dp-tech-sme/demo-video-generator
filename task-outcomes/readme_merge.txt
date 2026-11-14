PROMPT: Merge the 2 README.md files since they now both contain only half of the correct information and steps. @README.md @dist/README.md
TIMESTAMP: Sat 14 Nov 2026 20:06 CET

RESULT
- Root README.md is now the single document (13 sections): overview of repo + package, quick start, prerequisites, installation (zip download, checksum, install, step 9 enablement, manual, verify, rollback, rebuild), usage, architecture, security, testing, step 9, building the demo videos directly, troubleshooting, limitations, change notes.
- dist/README.md removed. The merged README is copied into the zip at build time.
- Zip checksum moved to releases/SHA256SUMS (a README inside the zip cannot contain the zip's own hash). Verify with: shasum -a 256 -c SHA256SUMS.
- dist/tests/test_tools.py: README consistency test now finds the README in the package root or the repository root.
- Checks: 31 tests OK in dist/ and in the unpacked zip; skills.py verify ok (11 skills); zip clean (62 entries, no .env/caches); checksum OK.
