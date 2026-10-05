#!/usr/bin/env python3
"""Synthetic mapping experiment only; no network, credentials or production code."""
import copy
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def names(edges, role):
    result = []
    for edge in edges or []:
        if edge.get('role', {}).get('name') != role:
            continue
        name = edge.get('person', {}).get('name')
        if nonempty(name) and name not in result:
            result.append(name)
    return ', '.join(result)


def image_url(image):
    value = (image or {}).get('url')
    return value.rstrip('/') + '/large.jpg' if nonempty(value) else None


def title_list(values):
    result = []
    for item in values or []:
        title = item.get('title')
        if nonempty(title) and title not in result:
            result.append(title)
    return result


def map_release(book, release):
    output = {}
    for field in ('title', 'subtitle'):
        value = release.get(field)
        value = value if nonempty(value) else book.get(field)
        if nonempty(value):
            output[field] = value
    for field, value in (
        ('author', names(book.get('people'), 'Author')),
        ('narrator', names(release.get('people'), 'Narrator')),
        ('publisher', (release.get('publisher') or {}).get('name')),
        ('language', (release.get('language') or {}).get('name')),
        ('description', book.get('description')),
        ('isbn', release.get('isbn')),
    ):
        if nonempty(value):
            output[field] = value
    published = release.get('releaseDate')
    try:
        year = datetime.datetime.fromisoformat(published.replace('Z', '+00:00')).year
    except (AttributeError, ValueError):
        year = book.get('copyright')
    if isinstance(year, int) and not isinstance(year, bool) and 1 <= year <= 9999:
        output['publishedYear'] = str(year)
    cover = next((image_url(i) for i in release.get('images', []) if image_url(i)), None)
    cover = cover or image_url(book.get('coverImage'))
    if cover:
        output['cover'] = cover
    milliseconds = release.get('runtimeLengthMs')
    seconds = release.get('runtimeLengthSec')
    if isinstance(milliseconds, int) and milliseconds >= 0:
        output['duration'] = milliseconds // 60000
    elif isinstance(seconds, int) and seconds >= 0:
        output['duration'] = seconds // 60
    for relation in release.get('external', []):
        if relation.get('category', {}).get('title', '').casefold() == 'audible':
            value = relation.get('itemId')
            if nonempty(value):
                output['asin'] = value
                break
    for field in ('genres', 'tags'):
        values = title_list(book.get(field))
        if values:
            output[field] = values
    series = []
    for membership in book.get('series', []):
        title = membership.get('series', {}).get('title')
        if not nonempty(title):
            continue
        value = {'series': title}
        label = (membership.get('position') or {}).get('label')
        label = label if nonempty(label) else membership.get('ordinal')
        if label is not None and str(label).strip():
            value['sequence'] = str(label)
        series.append(value)
    if series:
        output['series'] = series
    return output


def map_case(inputs):
    if inputs.get('resolver', {}).get('status') == 404:
        return {'matches': [], 'release_ids': []}
    books = [b for b in (inputs.get('book'), inputs.get('alternateBook')) if b]
    books_by_id = {b['id']: b for b in books}
    query = inputs.get('query', {})
    seen = set()
    rows = []
    for release in inputs.get('releases', []) + inputs.get('alternateReleases', []):
        if release['id'] in seen:
            continue
        seen.add(release['id'])
        if query.get('isbn') and release.get('isbn') != query['isbn']:
            continue
        if query.get('asin') and not any(
            r.get('category', {}).get('title', '').casefold() == 'audible'
            and r.get('itemId') == query['asin'] for r in release.get('external', [])
        ):
            continue
        book = books_by_id.get(release.get('book', {}).get('id'))
        if not book:
            continue
        mapped = map_release(book, release)
        if 'title' not in mapped:
            continue
        # Stable sorting preserves upstream release order for equal title scores.
        exact = mapped['title'].casefold() == query.get('title', '').casefold()
        rows.append((0 if exact else 1, release['id'], mapped))
    rows.sort(key=lambda row: row[0])
    return {'matches': [r[2] for r in rows[:10]], 'release_ids': [r[1] for r in rows[:10]]}


def validate_case(case, mapped):
    matches = mapped['matches']
    name = case['name']
    assert len(mapped['release_ids']) == len(set(mapped['release_ids']))
    allowed = set('title subtitle author narrator publisher publishedYear description cover isbn asin genres tags series language duration'.split())
    for match in matches:
        assert set(match) <= allowed
        assert isinstance(match['title'], str)
        for field in set(match) - {'genres', 'tags', 'series', 'duration'}:
            assert isinstance(match[field], str)
        if 'duration' in match:
            assert isinstance(match['duration'], int) and match['duration'] >= 0
    if name == 'known-title-author':
        assert matches == [{
            'title': 'Invented Example', 'subtitle': 'Synthetic subtitle',
            'author': 'Synthetic Author', 'narrator': 'Narrator A',
            'publisher': 'Synthetic Publisher', 'language': 'English',
            'description': 'Invented description for local fixture testing only.',
            'isbn': '9780000000002', 'asin': 'B000000001', 'publishedYear': '2026',
            'duration': 120, 'cover': 'https://assets.example.invalid/release-cover/large.jpg',
            'genres': ['Synthetic Genre'], 'tags': ['Synthetic Tag'],
        }]
        assert len(matches) == 1 and set(matches[0]) == allowed - {'series'}
        assert matches[0]['duration'] == 120 and matches[0]['publishedYear'] == '2026'
        assert matches[0]['cover'] == 'https://assets.example.invalid/release-cover/large.jpg'
        assert matches[0]['author'] == 'Synthetic Author' and matches[0]['narrator'] == 'Narrator A'
    elif name == 'ambiguous-title':
        assert len(matches) == 2
        assert [m['author'] for m in matches] == ['Synthetic Author', 'Another Synthetic Author']
    elif name == 'multiple-recordings':
        assert len(matches) == 2 and [m['narrator'] for m in matches] == ['Narrator A', 'Narrator B']
    elif name == 'full-cast':
        assert matches[0]['narrator'] == 'Full Cast'
    elif name == 'multiple-authors-narrators':
        assert matches[0]['author'] == 'Synthetic Author, Second Synthetic Author'
        assert matches[0]['narrator'] == 'Narrator A, Second Synthetic Narrator'
    elif name == 'fractional-and-zero-series':
        assert [s['sequence'] for s in matches[0]['series']] == ['0', '0.5']
    elif name == 'missing-cover-identifiers-runtime':
        assert not set('cover isbn asin duration description publisher language narrator'.split()) & set(matches[0])
        assert matches[0]['publishedYear'] == '2026'
    elif name == 'unknown-identifier':
        assert matches == []
    elif name == 'alternate-language':
        assert len(matches) == 2 and [m['language'] for m in matches] == ['English', 'French']
    elif name == 'different-isbn-editions':
        assert len(matches) == 1 and mapped['release_ids'] == ['SR0000000002']
        assert matches[0]['isbn'] == '9780000000019'
    elif name == 'duplicate-release-id':
        assert len(matches) == 1
    else:
        raise AssertionError('unknown scenario')


def main():
    fixtures_path = Path(__file__).with_name('fixtures.json')
    raw = fixtures_path.read_bytes()
    fixtures = json.loads(raw)
    records = []
    for case in fixtures['cases']:
        outputs = [map_case(case['input']) for _ in range(3)]
        assert outputs[0] == outputs[1] == outputs[2]
        validate_case(case, outputs[0])
        records.append({'scenario': case['name'], 'outcome': 'Pass',
                        'match_count': len(outputs[0]['matches']), 'deterministic_runs': 3,
                        'conditional_upstream_support': bool(case.get('condition'))})
    # Additional boundary checks for provisional fallback/rounding rules.
    book = fixtures['cases'][0]['input']['book']
    release = copy.deepcopy(fixtures['cases'][0]['input']['releases'][0])
    release.update(title='', runtimeLengthMs=119999, releaseDate='invalid')
    result = map_release(book, release)
    assert result['title'] == book['title'] and result['duration'] == 1
    assert result['publishedYear'] == '2026'
    release['title'] = '   '
    assert map_release(book, release)['title'] == book['title']
    release['images'] = []
    assert map_release(book, release)['cover'].endswith('/work-cover/large.jpg')
    release.pop('runtimeLengthMs')
    release['runtimeLengthSec'] = 119
    assert map_release(book, release)['duration'] == 1
    known = copy.deepcopy(fixtures['cases'][0]['input'])
    known['query'] = {'asin': 'B000000000'}
    assert map_case(known)['matches'] == []
    folder = ROOT / 'docs/evidence/SPIKE-003'
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    result = {'captured_at_utc': stamp, 'classification': 'synthetic_mapping_experiment',
              'fixture_sha256': hashlib.sha256(raw).hexdigest(),
              'experiment_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'outcome': 'Pass', 'scenarios': records, 'additional_boundaries': 'Pass',
              'limitations': 'Experimental rules only. ISBN fixture selection does not establish upstream ISBN lookup. No live API or UI check. Production mapping must be revalidated after Gate C.'}
    output = folder / ('mapping-' + stamp + '.json')
    with output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(f'Passed {len(records)} mapping scenarios, three runs each, plus fallback/rounding/identifier boundaries.')
    print('Evidence: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
