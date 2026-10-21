"""Owned declaration admission cases; no browser, network or active inputs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src import producer_core as producer, checker_core as checker
from src.output_paths import write_text_exclusive

HERE = Path(__file__).resolve().parents[1]
CORES = (producer, checker)


def document(body='<p>Notes</p>'):
    return '<!doctype html><html><head><title>Notes</title></head><body>' + body + '</body></html>'


class HtmlDeclarationTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix='iwb-declarations-')
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name).resolve()
        self.serial = 0

    def bundle(self, text):
        self.serial += 1
        path = self.root / str(self.serial)
        write_text_exclusive(path / 'bundle.json', json.dumps({
            'format': 'iwb-1', 'root': 'index.html', 'resources': ['index.html']}))
        write_text_exclusive(path / 'index.html', text)
        return path

    def rejected(self, text, code='unknown-declaration'):
        root = self.bundle(text)
        errors = []
        for core in CORES:
            with self.assertRaises(core.AdmissionError) as raised:
                core.parse_bundle(root)
            self.assertEqual(raised.exception.code, code)
            errors.append(raised.exception.as_dict())
        self.assertEqual(errors[0], errors[1])
        return root, errors[0]

    def test_unknown_declaration_prefixes_are_not_comments(self):
        for token in ('<!review-note>', '<![review-note>', '<![CDATA[Notes]]>', '<!>'):
            for text in (token + document(),
                         document().replace('<html>', token + '<html>', 1),
                         document(token + '<p>Notes</p>')):
                with self.subTest(token=token, text=text):
                    self.rejected(text)

    def test_unknown_declarations_inside_text_do_not_coalesce(self):
        self.rejected(document('<p>No<!review-note>tes</p>'))
        self.rejected(document('<p>No<![review-note>tes</p>'))

    def test_comments_and_doctype_remain_admitted(self):
        left = self.bundle(document())
        for text in (document().replace('<!doctype html>', '<!DOCTYPE HTML>', 1),
                     '<!--before-->' + document() + '<!--after-->',
                     document('<p>No<!-- benign --><!--second-->tes</p>'),
                     document().replace('<html>', '<!--head--><html>', 1)):
            right = self.bundle(text)
            cert = producer.make_certificate(left, right)
            self.assertEqual(cert['decision'], 'equivalent')
            self.assertTrue(checker.verify_certificate(left, right, cert)['accepted'])

    def test_quoted_and_decoded_declaration_shapes_are_literal(self):
        root = self.bundle(document('<p title="<!review-note>">'
                                    'No&lt;!review-note&gt;tes'
                                    '<!-- <!review-note> --></p>'))
        for core in CORES:
            events = core.parse_bundle(root).resources['index.html']['events']
            self.assertIn('No<!review-note>tes', [e.data for e in events if e.kind == 'text'])
            attrs = [dict(e.data[1]) for e in events
                     if e.kind == 'start' and e.data[0] == 'p']
            self.assertEqual(attrs, [{'title': '<!review-note>'}])

    def test_chunk_boundaries_preserve_records_and_exact_errors(self):
        texts = (document(), '<!--before-->' + document('<p>No<!--c-->tes</p>'),
                 document('<p title="<!review-note>">Notes</p>'),
                 '<!review-note>' + document(),
                 document('<p>No<!review-note>tes</p>'),
                 document('<![review-note><p>Notes</p>'))
        for core in CORES:
            for text in texts:
                def outcome(chunks):
                    parser = core._HTMLCollector('index.html')
                    try:
                        for chunk in chunks:
                            parser.feed(chunk)
                        parser.close_checked()
                        return 'admitted', parser.events
                    except core.AdmissionError as exc:
                        return 'excluded', exc.as_dict()
                expected = outcome([text])
                self.assertEqual(outcome(list(text)), expected)
                for split in range(1, len(text)):
                    self.assertEqual(outcome([text[:split], text[split:]]), expected)

    def test_incomplete_declarations_fail_before_eof_recovery(self):
        for suffix in ('<!review-note', '<![review-note', '<!'):
            self.rejected(document() + suffix)
        self.rejected(document() + '<!doctype html', 'bad-doctype')

    def test_wrong_or_duplicate_doctype_is_still_rejected(self):
        for text in (document().replace('<!doctype html>', '<!doctype svg>', 1),
                     document().replace('<!doctype html>', '<!doctype html SYSTEM "notes">', 1),
                     document('<!doctype html><p>Notes</p>')):
            self.rejected(text, 'bad-doctype')

    def test_public_cli_issues_exclusion_and_rejects_positive_replay(self):
        valid = self.bundle(document())
        positive = producer.make_certificate(valid, valid)
        positive_path = self.root / 'positive.json'
        write_text_exclusive(positive_path, json.dumps(positive))
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
        for text in ('<!review-note>' + document(), document('<p>No<!review-note>tes</p>')):
            invalid = self.bundle(text)
            for left, right, side in ((valid, invalid, 'right'), (invalid, valid, 'left')):
                proposal = subprocess.run([sys.executable, '-B', str(HERE / 'certify.py'),
                                           str(left), str(right)], cwd=HERE, env=env,
                                          capture_output=True, text=True, encoding='utf-8', timeout=15)
                self.assertEqual(proposal.returncode, 0, proposal.stdout + proposal.stderr)
                cert = json.loads(proposal.stdout)
                self.assertEqual((cert['decision'], cert['side'], cert['witness']['code']),
                                 ('out-of-language', side, 'unknown-declaration'))
                cert_path = self.root / f'certificate-{self.serial}-{side}.json'
                write_text_exclusive(cert_path, proposal.stdout)
                replay = subprocess.run([sys.executable, '-B', str(HERE / 'check.py'),
                                         str(left), str(right), str(cert_path)], cwd=HERE, env=env,
                                        capture_output=True, text=True, encoding='utf-8', timeout=15)
                self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
                self.assertTrue(json.loads(replay.stdout)['accepted'])
            replay = subprocess.run([sys.executable, '-B', str(HERE / 'check.py'),
                                     str(valid), str(invalid), str(positive_path)], cwd=HERE, env=env,
                                    capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(replay.returncode, 2)
            self.assertEqual(json.loads(replay.stdout)['reason'],
                             'endpoint-out-of-language:unknown-declaration')


if __name__ == '__main__':
    unittest.main(verbosity=2)
