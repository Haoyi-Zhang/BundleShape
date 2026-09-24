# Certified structural equivalence for anchored inert web bundles

This standalone artifact implements and evaluates a deliberately restricted,
non-executable source language for comparing small HTML/CSS/resource bundles.
It never starts a browser, executes JavaScript, submits a form, follows a network
URL, renders a page, or calls a model API. The artifact is intended for defensive
static analysis and for checking the paper's finite evidence.

The central object is an **anchored inert web bundle** (IWB): a manifest, one
root HTML document, reachable local HTML/CSS files, and local image bytes. The
admission rules remove active content and the difficult ambiguous cases that
would invalidate the stated canonicalization theorem. Within the admitted
language, the implementation ignores only declared reorderings and applies one
global bijection to resource paths, HTML IDs, and CSS classes.

## What is claimed

The artifact supports four bounded claims.

1. The written proof in `proofs/correctness.md` shows that, for the admitted
   language, two bundles have the same canonical form exactly when they differ
   only by the declared global renamings and reorderings. Binary resources are
   represented by their exact base64 bytes in the canonical form, not only by a
   digest.
2. An equivalent certificate contains total resource/ID/class bijections. The
   separately packaged checker reparses both endpoints, validates the maps, and
   replays the mapping over HTML, CSS, references, and exact asset bytes.
3. A different certificate identifies the first deterministic mismatch between
   the checker's reconstructed canonical forms. An out-of-language certificate
   identifies the exact deterministic admission error. These witnesses are
   checkable but are not claimed to be minimum explanations.
4. The retained finite evidence contains 480 frozen metamorphic pairs, 512
   seeded combination/differential cases, 5,120 ordered tiny-bundle pairs checked
   against exhaustive bijection search, 360 mutated certificates, 47 unit and
   boundary tests, a cross-resource coupling negative control, and one bounded
   stress instance. Finite agreement is implementation evidence, not a universal
   proof or real-world detection accuracy.

The artifact does **not** claim browser-behavior equivalence, visual equivalence,
semantic JavaScript equivalence, malicious-site provenance, authorship
attribution, or coverage of arbitrary web applications. It also does not claim
that the checker was independently authored or formally verified.

## Requirements

- Linux or another POSIX-like environment
- Python 3.10 or newer
- Python standard library only
- one worker; no network, GPU, model API, browser, or service

The measured campaign used one process and no child workers. Its largest retained
stress instance stayed below the project's 512 MiB per-process address-space
choice. Timing and peak RSS are observations and are excluded from exact-output
comparison.

## Reproduce the retained evidence

From the extracted artifact root:

```sh
python generate_fixtures.py
rm -rf reproduced
python test.py --out reproduced
python evaluate.py --out reproduced
python verify_results.py --actual reproduced --expected results
```

Expected final line from the comparator:

```json
{"compared": 10, "matched": true, "mismatches": []}
```

`evaluate.py` regenerates the owned base and variant suites, then materializes the
deterministic combination and stress working sets before measuring. The comparison is byte-exact for deterministic CSV/JSON fields and removes only
run-specific wall time, process time, peak RSS, and swap observations. A passing
comparison confirms reproduction of the retained finite outputs; it does not
prove the mathematical theorem or external validity.

## Use the certificate interface

Produce and check an equivalent certificate:

```sh
python certify.py \
  fixtures/owned/fixture-00 \
  fixtures/variants/fixture-00/combined-all \
  --output /tmp/equivalent.json
python check.py \
  fixtures/owned/fixture-00 \
  fixtures/variants/fixture-00/combined-all \
  /tmp/equivalent.json
```

Produce and check a structural mismatch:

```sh
python certify.py \
  fixtures/owned/fixture-00 \
  fixtures/variants/fixture-00/changed-text \
  --output /tmp/different.json
python check.py \
  fixtures/owned/fixture-00 \
  fixtures/variants/fixture-00/changed-text \
  /tmp/different.json
```

Inspect one canonical form:

```sh
python canonicalize.py fixtures/owned/fixture-00
```

The producer refuses to overwrite an existing certificate output. The checker
returns exit status 0 only for an accepted certificate. Read the printed
`decision`: an accepted `different` or `out-of-language` certificate is not a
positive clone match. Rejection of a certificate proves neither equivalence nor
difference.

## Frozen result summary

`results/evaluation-summary.json` records:

- 480 pairs: 288 equivalent, 120 structurally different, 72 out of language;
- 480/480 expected producer decisions with accepted checker replay;
- 512/512 seeded combination/differential cases with expected decisions, accepted
  replays, and matching producer/checker parser objects or rejection witnesses;
- 432 unique admitted bundles containing 1,728 resources, 21,168 HTML events,
  2,160 CSS rules, 6,048 declarations, and 2,160 resource edges;
- certificate sizes from 147 to 612 bytes (median 584.5 bytes) in that suite;
- 96 tiny bundles and 5,120 ordered pairs, with 18,176 candidate bijections
  examined and zero canonicalizer/oracle disagreements;
- all 360 targeted certificate mutations rejected and all 47 unit/boundary tests
  passed;
- a 16-page, 19-resource stress pair with 1,200 IDs, 1,201 classes, 1,200 CSS
  rules, and 3,601 declarations, accepted as equivalent in a median retained
  wall time of 0.499 s over five same-process repetitions (110,832 KiB peak RSS).

The routine local-alpha baseline happens to score 1.0 on the 408 admitted
metamorphic pairs. The separate coupling control is therefore essential: that
baseline reports a false positive when two pages require incompatible class
maps, while the global method reports `different` and the checker accepts the
witness. The simple baseline table is diagnostic, not a claim of state-of-the-art
comparative performance.

## Language and certificate boundary

The complete operational definition is in
`docs/language-and-certificates.md`. In brief, admission rejects scripts, forms,
controls, frames, embedded objects, inline event/style attributes, external or
query-bearing URLs, unknown/unreachable files, symlinks, malformed document
skeletons, CSS at-rules, custom properties, shorthands, duplicate declarations,
unsupported selectors, undeclared selector names, duplicate global IDs, and a
class introduction that contains more than one previously unseen class in one
unordered class list.

The last restriction is structural, not aesthetic. It makes the first class
introduction independent of class-token order. Removing it creates a symmetric
choice that this lightweight canonicalizer cannot resolve without a general
nominal-graph canonical-labeling procedure.

## Repository map

- `src/producer_core.py`: admission, canonicalization, and certificate producer
- `src/checker_core.py`: separately packaged parser and certificate replay
- `src/exact_oracle.py`: exhaustive tiny-bundle bijection oracle
- `src/fixture_factory.py`: owned benign bases and metamorphic variants
- `src/baselines.py`: four deliberately simple diagnostic baselines
- `tests/test_iwb.py`: unit, boundary, oracle, coupling, and mutation checks
- `fixtures/`: packaged owned/variant/tiny/coupling inputs; evaluation materializes
  deterministic combination/stress working sets at run time
- `results/`: retained outputs, resource intake, and read-only anchor inventory
- `literature/reference-audit.csv`: one audit row for each of the 70 cited entries
- `literature/literature-calibration.csv`: the 12+5+5 full-text calibration set
- `proofs/correctness.md`: definitions, theorem, proof obligations, and limits
- `docs/language-and-certificates.md`: schemas and operational semantics
- `baseline_trace/`: preserved narrow failure modes from the earlier formulation
- `claim_evidence_ledger.csv`: paper/artifact claim-to-evidence map
- `external_resources.csv`: external metadata and integration record

## External-source and safety boundary

The motivating public repository is MIT-licensed, but no source blob from it is
included. `results/anchor-static-inventory.json` retains only repository metadata
and four GitHub code-search index counts. Those counts overlap and are not an
eligibility denominator. No active page was fetched into this deliverable,
rendered, executed, transformed, or redistributed.

All fixture topics are benign (libraries, museums, gardens, courses, science
clubs, and walking trails). Assets are local one-pixel owned bytes. There are no
credentials, real destinations, form submission paths, phishing brands, or
automated interaction workflows.

## Licensing, authorship, and AI disclosure

The implementation, fixtures, tests, proofs, and documentation are released
under the MIT license in `LICENSE`. External resources are metadata-only and are
listed in `external_resources.csv`; no third-party implementation is vendored.

Substantive research formulation, proof drafting, implementation, experiments,
and manuscript prose were generated with GPT-5.6 Sol Pro in ChatGPT. The named human
authors must review the science, satisfy authorship and originality rules, and
make any required disclosure before external use. A successful self-check is not
independent review, formal verification, or evidence of acceptance.


## Complete clean reproduction (final packet)

From any working directory, with `ARTIFACT` set to this extracted repository
root:

```sh
python "$ARTIFACT/generate_fixtures.py"
rm -rf "$ARTIFACT/reproduced"
python "$ARTIFACT/test.py" --out "$ARTIFACT/reproduced"
python "$ARTIFACT/evaluate.py" --out "$ARTIFACT/reproduced"
python "$ARTIFACT/natural_source_study.py" --out "$ARTIFACT/reproduced"
python "$ARTIFACT/static_assurance.py" --out "$ARTIFACT/reproduced"
python "$ARTIFACT/verify_results.py" \
  --actual "$ARTIFACT/reproduced" --expected "$ARTIFACT/results"
```

`static_assurance.py` compiles every implementation module, confirms that the
checker does not import the producer, and rejects network imports, dynamic
`eval`/`exec`, and `shell=True` in the scientific implementation. These are
static implementation checks, not a proof that the code is vulnerability-free.
