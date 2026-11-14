# Unit and security tests for the Demo Narrative Builder tools (standard library unittest).
# Run: python -m unittest discover -s tests -v   (from the asset folder, using its virtual environment)
#
# Change log
# Sat 14 Nov 2026 19:14 CET - Initial version: ingest formats, SSRF/URL guards, DOCX entity attack, validator.
# Sat 14 Nov 2026 19:28 CET - Skill system: registry consistency, approval record, step 9 gate, step status.
# Sat 14 Nov 2026 20:04 CET - README check finds the merged README in the package root or the repository root.

import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import approval  # noqa: E402
import ingest  # noqa: E402
import production  # noqa: E402
import skills  # noqa: E402
import validate_script as V  # noqa: E402

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SAMPLE_TXT = ROOT / "examples" / "sample_source.txt"
SAMPLE_SCRIPT = ROOT / "examples" / "sample_script_v1.md"
README = next((p for p in (ROOT / "README.md", ROOT.parent / "README.md") if p.is_file()), None)  # zip or repository


# Build a small DOCX in memory - Sat 14 Nov 2026 19:14 CET
def make_docx(body_xml, doctype=""):
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>{doctype}<w:document xmlns:w="{W_NS}"><w:body>'
           f"{body_xml}</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


# Build a minimal one-page PDF with a text layer - Sat 14 Nov 2026 19:14 CET
def make_pdf(text):
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, xref)
    return out


class IngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_txt(self):
        r = ingest.ingest(str(SAMPLE_TXT), self.dir)
        self.assertEqual(r["type"], "txt")
        self.assertEqual(r["title"], "Why Release Notes Get Ignored")
        self.assertGreaterEqual(r["section_count"], 4)
        rec = json.loads((self.dir / r["slug"] / "source.json").read_text())
        self.assertTrue(rec["untrusted_content"])
        self.assertTrue((self.dir / r["slug"] / "source.txt").read_text().startswith("<!-- UNTRUSTED"))

    def test_docx(self):
        body = ('<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>My Doc</w:t></w:r></w:p>'
                '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Intro</w:t></w:r></w:p>'
                '<w:p><w:r><w:t>Hello</w:t></w:r><w:r><w:t xml:space="preserve"> world.</w:t></w:r></w:p>')
        f = self.dir / "doc.docx"
        f.write_bytes(make_docx(body))
        r = ingest.ingest(str(f), self.dir / "out")
        self.assertEqual(r["title"], "My Doc")
        rec = json.loads((self.dir / "out" / r["slug"] / "source.json").read_text())
        self.assertEqual(rec["sections"][0]["text"], "Hello world.")

    def test_docx_entity_attack_rejected(self):
        dtd = '<!DOCTYPE d [<!ENTITY x "boom">]>'
        f = self.dir / "evil.docx"
        f.write_bytes(make_docx("<w:p><w:r><w:t>&x;</w:t></w:r></w:p>", dtd))
        with self.assertRaises(ingest.IngestError):
            ingest.ingest(str(f), self.dir / "out")

    def test_pdf(self):
        f = self.dir / "paper.pdf"
        f.write_bytes(make_pdf("Hello from a PDF"))
        r = ingest.ingest(str(f), self.dir / "out")
        rec = json.loads((self.dir / "out" / r["slug"] / "source.json").read_text())
        self.assertIn("Hello from a PDF", rec["sections"][0]["text"])
        self.assertTrue(r["warnings"])   # fewer than MIN_WORDS_WARN words

    def test_corrupt_pdf_and_docx_rejected(self):
        for name in ("bad.pdf", "bad.docx"):
            f = self.dir / name
            f.write_bytes(b"not a real file")
            with self.assertRaises(ingest.IngestError):
                ingest.ingest(str(f), self.dir / "out")

    def test_html_prefers_article_and_skips_scripts(self):
        words = " ".join(["word"] * 120)
        html = (f"<html><head><title>T</title><script>evil()</script></head><body><nav><p>menu</p></nav>"
                f"<article><h1>Heading</h1><p>{words}</p></article><footer><p>legal</p></footer></body></html>")
        doc = ingest.parse_html(html.encode(), "utf-8")
        text = " ".join(s["text"] for s in doc.sections())
        self.assertNotIn("evil", text)
        self.assertNotIn("menu", text)
        self.assertNotIn("legal", text)
        self.assertEqual(doc.sections()[0]["heading"], "Heading")

    def test_unsupported_extension_and_missing_file(self):
        f = self.dir / "x.exe"
        f.write_bytes(b"MZ")
        for src in (str(f), str(self.dir / "missing.txt")):
            with self.assertRaises(ingest.IngestError):
                ingest.ingest(src, self.dir / "out")

    def test_oversize_file_rejected(self):
        f = self.dir / "big.txt"
        f.write_bytes(b"a" * 2048)
        old = ingest.C.MAX_BYTES
        ingest.C.MAX_BYTES = 1024
        try:
            with self.assertRaises(ingest.IngestError):
                ingest.ingest(str(f), self.dir / "out")
        finally:
            ingest.C.MAX_BYTES = old

    def test_slug_cannot_escape_output_folder(self):
        r = ingest.ingest(str(SAMPLE_TXT), self.dir / "out", slug="../../etc/passwd")
        self.assertEqual(Path(r["folder"]).parent, self.dir / "out")
        self.assertNotIn("..", r["slug"])


class NetworkGuardTests(unittest.TestCase):
    def test_url_rules(self):
        bad = ["http://example.com/a", "https://user:pw@example.com/", "https://example.com:8443/",
               "https:///nohost", "ftp://example.com/x", "https://example.com/" + "a" * 3000]
        for url in bad:
            with self.assertRaises(ingest.IngestError, msg=url):
                ingest.check_url(url)
        ingest.check_url("https://example.com/post?utm=1")

    def test_private_addresses_blocked(self):
        for ip in ("127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "::1", "::ffff:127.0.0.1", "fd00::1"):
            self.assertFalse(ingest._is_public(ip), ip)
        self.assertTrue(ingest._is_public("93.184.216.34"))

    def test_localhost_url_blocked_without_network(self):
        with self.assertRaises(ingest.IngestError):
            ingest.fetch_url("https://localhost/secret")

    def test_cli_returns_generic_error(self):
        self.assertEqual(ingest.main(["http://example.com/x"]), 2)


class ValidatorTests(unittest.TestCase):
    def test_sample_passes(self):
        rep = V.validate(SAMPLE_SCRIPT.read_text(encoding="utf-8"), 150, None)
        self.assertTrue(rep["ok"], rep["errors"])
        self.assertEqual(rep["scenes"], 4)
        self.assertEqual(rep["runtime_seconds"], 60)

    def test_gap_in_timing_fails(self):
        text = SAMPLE_SCRIPT.read_text(encoding="utf-8").replace("| 0:15–0:35 |", "| 0:16–0:35 |")
        rep = V.validate(text, 150, None)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("previous scene ends" in e for e in rep["errors"]))

    def test_voice_over_overrun_fails(self):
        text = SAMPLE_SCRIPT.read_text(encoding="utf-8").replace("Try it on your next release, and tell us",
                                                                 "Try it on your next release " + "now " * 60 + "and tell us")
        rep = V.validate(text, 150, None)
        self.assertTrue(any("needs about" in e for e in rep["errors"]))

    def test_missing_followups_and_gate_fail(self):
        text = SAMPLE_SCRIPT.read_text(encoding="utf-8")
        text = text.replace("| 4 | Which contact", "| 9 | Which contact").replace("## APPROVAL GATE", "## Done")
        rep = V.validate(text, 150, None)
        self.assertTrue(any("section 4 has no follow-up" in e for e in rep["errors"]))
        self.assertTrue(any("APPROVAL GATE" in e for e in rep["errors"]))

    def test_placeholder_and_runtime_checks(self):
        rep = V.validate(SAMPLE_SCRIPT.read_text(encoding="utf-8") + "\n{{TODO}}\n", 150, 120)
        self.assertTrue(any("placeholders" in e for e in rep["errors"]))
        self.assertTrue(any("target is 120s" in e for e in rep["errors"]))

    def test_template_does_not_pass(self):
        rep = V.validate((ROOT / "templates" / "script_template.md").read_text(encoding="utf-8"), 150, None)
        self.assertFalse(rep["ok"])


    def test_plan_marker_is_error_only_when_required(self):
        text = SAMPLE_SCRIPT.read_text(encoding="utf-8")
        a = text.index("# PRODUCTION PLAN")
        b = text.index("## Appendix")
        pending = text[:a] + "# PRODUCTION PLAN\n\n<!-- PRODUCTION-PLAN-PENDING -->\n\n" + text[b:]
        self.assertTrue(V.validate(pending, 150, None)["ok"])
        rep = V.validate(pending, 150, None, require_plan=True)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("Production plan not filled" in e for e in rep["errors"]))
        self.assertTrue(V.validate(text, 150, None, require_plan=True)["ok"])


# Run a CLI main() and capture stdout and the exit code - Sat 14 Nov 2026 19:28 CET
def run_cli(main, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = main(argv)
    return code, buf.getvalue()


class SkillSystemTests(unittest.TestCase):
    def test_registry_has_nine_steps_with_video_production_as_step_9(self):
        reg = skills.load_registry()
        self.assertEqual([s["step"] for s in reg["steps"]], list(range(1, 10)))
        self.assertEqual(reg["steps"][8]["id"], "narrative-09-video-production")
        self.assertEqual(reg["steps"][8]["tool"], "tools/production.py")

    def test_registry_skills_mode_and_question_bank_are_consistent(self):
        code, out = run_cli(skills.main, ["verify"])
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(out)["skills"], 11)

    @unittest.skipUnless(README is not None, "README.md is not part of an installed copy")
    def test_every_skill_is_documented_in_the_readme(self):
        readme = README.read_text(encoding="utf-8")
        reg = skills.load_registry()
        ids = [s["id"] for s in reg["steps"]] + [x["id"] for x in reg["support"]] + [reg["orchestrator"]["id"]]
        for sid in ids:
            self.assertTrue(sid in readme, f"{sid} missing in README")

    def test_list_and_show_find_step_9(self):
        code, out = run_cli(skills.main, ["list"])
        self.assertEqual(code, 0)
        self.assertIn("narrative-09-video-production", out)
        for key in ("9", "narrative-09-video-production", "video production"):
            code, out = run_cli(skills.main, ["show", key])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["step"], 9)
        self.assertEqual(run_cli(skills.main, ["show", "10"])[0], 2)


class ApprovalAndProductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.folder = self.root / "demo"
        self.folder.mkdir()
        self.script = self.folder / "demo_script_v1.md"
        self.script.write_text(SAMPLE_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_unapproved_script_fails_verify_and_step_9_check(self):
        self.assertFalse(approval.verify(self.script)["ok"])
        rep = production.check(self.script)
        self.assertFalse(rep["ok"])
        self.assertTrue(any(p.startswith("approval:") for p in rep["problems"]))

    def test_record_marks_status_and_verifies_until_the_script_changes(self):
        res = approval.record(self.script, 1)
        self.assertTrue(res["ok"], res)
        text = self.script.read_text(encoding="utf-8")
        self.assertIn("APPROVED (option 1)", text)
        self.assertNotIn("AWAITING EXPLICIT APPROVAL. No video", text)
        self.assertTrue(approval.verify(self.script)["ok"])
        self.script.write_text(text + "\nextra\n", encoding="utf-8")
        self.assertFalse(approval.verify(self.script)["ok"])

    def test_only_options_1_and_2_can_be_recorded(self):
        self.assertFalse(approval.record(self.script, 3)["ok"])
        self.assertFalse((self.folder / "approval.json").exists())

    def test_record_refuses_a_script_with_open_plan(self):
        text = self.script.read_text(encoding="utf-8")
        a, b = text.index("# PRODUCTION PLAN"), text.index("## Appendix")
        self.script.write_text(text[:a] + "# PRODUCTION PLAN\n<!-- PRODUCTION-PLAN-PENDING -->\n" + text[b:],
                               encoding="utf-8")
        res = approval.record(self.script, 1)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "validation failed")

    def test_status_and_check_follow_the_files(self):
        reg = skills.load_registry()
        self.assertFalse(skills.step_done(reg["steps"][7], self.folder))
        approval.record(self.script, 2, "test")
        self.assertTrue(skills.step_done(reg["steps"][7], self.folder))
        self.assertTrue(skills.step_done(reg["steps"][6], self.folder))
        self.assertFalse(skills.step_done(reg["steps"][8], self.folder))
        code, out = run_cli(skills.main, ["--root", str(self.root), "check", "demo", "9"])
        self.assertEqual(code, 0, out)
        code, out = run_cli(skills.main, ["--root", str(self.root), "check", "demo", "4"])
        self.assertEqual(code, 1)
        self.assertIn("factsheet.md", json.loads(out)["missing"])
        code, out = run_cli(skills.main, ["--root", str(self.root), "status", "demo"])
        self.assertIn("Next: step 1", out)

    def test_run_needs_confirmation_and_safe_custom_names(self):
        base = ["run", str(self.script), "--stage", "audio"]
        self.assertEqual(run_cli(production.main, base)[0], 2)
        self.assertEqual(run_cli(production.main, base + ["--confirmed", "--custom-audio", "build_a.py"])[0], 2)
        self.assertEqual(run_cli(production.main, base + ["--confirmed", "--custom-audio", "../evil.py",
                                                          "--custom-video", "build_b.py"])[0], 2)

    def test_run_is_blocked_without_approval(self):
        args = production.argparse.Namespace(stage="audio", custom_audio=None, custom_video=None, at=5.0)
        res = production.run(self.script, args)
        self.assertFalse(res["ok"])
        self.assertFalse((self.folder / "production").exists())


if __name__ == "__main__":
    unittest.main()
