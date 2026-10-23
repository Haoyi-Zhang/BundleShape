"""Five fixed owned sizes; charge full exact-decision and certificate paths."""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import statistics
import sys

from comparison_cost import direct, replayed, timed
from src.checker_core import parse_bundle, verify_certificate
from src.producer_core import make_certificate
from src.output_paths import fresh_directory, write_text_exclusive
from src.stress_factory import emit_stress_bundle

HERE = Path(__file__).resolve().parent
POINTS = (1, 2, 4, 8, 16)
BLOCKS = 25


def positive_integer(value, maximum, field):
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f'{field} must be a positive integer at most {maximum}')


def table_tex(rows):
    lines = [r'\begin{tabular}{rrrrr}', r'\toprule',
             r'HTML & Input KiB & Direct ms & Cert. ms & Cert. KiB \\', r'\midrule']
    for row in rows:
        lines.append(f"{row['dimensions']['html_resources']} & {row['input_bytes']/1024:.2f} & "
                     f"{row['median_direct_ms']:.2f} & {row['median_certificate_ms']:.2f} & "
                     f"{row['certificate_bytes']/1024:.2f} " + r'\\')
    return '\n'.join([*lines, r'\bottomrule', r'\end{tabular}']) + '\n'


def run_pair(root, pages, blocks=BLOCKS, repeats=3):
    positive_integer(pages, 16, 'pages')
    positive_integer(blocks, BLOCKS, 'blocks')
    positive_integer(repeats, 3, 'repeats')
    root = fresh_directory(root)
    left, right = root / 'left', root / 'right'
    dimensions = emit_stress_bundle(left, pages=pages, blocks_per_page=blocks)
    emit_stress_bundle(right, pages=pages, blocks_per_page=blocks, transformed=True)
    bindings = {side: {p.relative_to(directory).as_posix(): sha256(p.read_bytes()).hexdigest()
                       for p in sorted(directory.rglob('*')) if p.is_file()}
                for side, directory in (('left', left), ('right', right))}
    parsed_left, parsed_right = parse_bundle(left), parse_bundle(right)
    certificate = make_certificate(left, right)
    if certificate['decision'] != 'equivalent' or not verify_certificate(left, right, certificate)['accepted']:
        raise RuntimeError('owned global renaming did not replay')
    wire = json.dumps(certificate, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    observations = []
    for repeat in range(repeats):
        methods = [('direct', direct), ('certificate', replayed)]
        if repeat % 2:
            methods.reverse()
        measurements = {}
        for name, method in methods:
            answer, measurement = timed(method, left, right)
            if answer != {'decision': 'equivalent'}:
                raise RuntimeError('paired exact decision disagreement')
            measurements[name] = measurement
        observations.append({'repeat': repeat, 'order': [name for name, _ in methods],
                             'measurements': measurements})
    for side, directory in (('left', left), ('right', right)):
        actual = {p.relative_to(directory).as_posix(): sha256(p.read_bytes()).hexdigest()
                  for p in sorted(directory.rglob('*')) if p.is_file()}
        if actual != bindings[side]:
            raise RuntimeError('input changed during measurement')
    return {'dimensions': dimensions,
            'input_bytes': sum(p.stat().st_size for directory in (left, right)
                               for p in directory.rglob('*') if p.is_file()),
            'canonical_bytes': [len(parsed_left.canonical_bytes), len(parsed_right.canonical_bytes)],
            'certificate_bytes': len(wire), 'certificate': certificate,
            'input_sha256': bindings, 'observations': observations,
            'median_direct_ms': statistics.median(r['measurements']['direct']['wall_seconds'] * 1000
                                                 for r in observations),
            'median_certificate_ms': statistics.median(r['measurements']['certificate']['wall_seconds'] * 1000
                                                      for r in observations),
            'median_paired_wall_ratio': statistics.median(r['measurements']['certificate']['wall_seconds'] /
                                                         r['measurements']['direct']['wall_seconds']
                                                         for r in observations)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = fresh_directory(args.out.resolve())
    sources = ('scaling_cost.py', 'comparison_cost.py', 'src/producer_core.py',
               'src/checker_core.py', 'src/limits.py', 'src/stress_factory.py',
               'src/fixture_factory.py', 'src/output_paths.py')
    binding = {name: sha256((HERE / name).read_bytes()).hexdigest() for name in sources}
    rows = [run_pair(out / 'inputs' / f'pages-{pages}', pages) for pages in POINTS]
    if binding != {name: sha256((HERE / name).read_bytes()).hexdigest() for name in sources}:
        raise RuntimeError('code changed during measurement')
    summary = {'points': len(rows), 'content_pages': list(POINTS), 'blocks_per_page': BLOCKS,
               'repeats_per_point': 3, 'paired_measurements': sum(len(r['observations']) for r in rows),
               'decision_disagreements': 0,
               'scope': 'Fixed owned renamed pairs, same-process alternating order; full filesystem admission, proposal, JSON round trip and replay as applicable; excludes fixture generation, startup and preliminary correctness checks. Not natural-site coverage, independent parsing, deployment, asymptotic validation or a replacement of retained timings.'}
    environment = {'python': sys.version, 'platform': platform.platform(),
                   'optimization': sys.flags.optimize, 'source_sha256': binding,
                   'command': ['python', '-B', 'scaling_cost.py', '--out', args.out.as_posix()]}
    for name, value in (('measurements.json', rows), ('summary.json', summary), ('environment.json', environment)):
        write_text_exclusive(out / name, json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    write_text_exclusive(out / 'table.tex', table_tex(rows))
    print(json.dumps({'summary': summary, 'points': [
        {k: row[k] for k in ('dimensions', 'input_bytes', 'certificate_bytes',
                              'median_direct_ms', 'median_certificate_ms', 'median_paired_wall_ratio')}
        for row in rows]}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
