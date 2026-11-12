"""Verify byte integrity, counts, geometry, answer joins, and Medium lineage."""
import collections
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {'small': (70, 32, 4), 'medium': (2406, 64, 5), 'large': (12032, 256, 5)}
SHAPES = {'P1': (512, 128), 'P2': (1024, 1024), 'P3': (8192, 256),
          'P4': (32768, 256), 'P5': (131072, 256)}


def require(condition, description):
    if not condition:
        raise ValueError(description)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    publication = json.loads((ROOT / 'publication-manifest.json').read_text(encoding='utf-8'))
    medium = json.loads((ROOT / 'medium/manifest.json').read_text(encoding='utf-8'))
    parent = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    require(digest(ROOT / 'manifest.json') == medium['parent_manifest_sha256'], 'Medium parent manifest')
    medium_hashes = {}
    large_matches = set()
    for tier, (quality_count, per_bucket, bucket_count) in EXPECTED.items():
        quality_ids = {}
        answer_ids = {}
        perf_ids = []
        categories = collections.Counter()
        buckets = collections.Counter()
        counts = {}
        for kind in ['quality.requests', 'quality.answers', 'performance.requests']:
            rel = f'{tier}/{kind}.jsonl.gz'
            path = ROOT / rel
            meta = publication['data_files'][rel]
            require(path.stat().st_size == meta['bytes'] and digest(path) == meta['sha256'], rel + ' hash')
            original = medium['files'][path.name] if tier == 'medium' else parent['files'][rel]
            require(meta['sha256'] == original['sha256'], rel + ' historical hash')
            seen = set()
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                for line in f:
                    r = json.loads(line)
                    key = (kind, r['id'])
                    require(r['id'] not in seen, rel + ' duplicate ID')
                    seen.add(r['id'])
                    if tier == 'medium' or (tier == 'large' and key in medium_hashes):
                        h = hashlib.sha256(json.dumps(r, ensure_ascii=False, sort_keys=True,
                            separators=(',', ':')).encode()).hexdigest()
                        if tier == 'medium':
                            medium_hashes[key] = h
                        else:
                            require(medium_hashes[key] == h, rel + ' Medium record changed')
                            large_matches.add(key)
                    if 'prompt_token_ids' in r:
                        require(len(r['prompt_token_ids']) == r['input_tokens'], rel + ' token count')
                        require('answer' not in r and 'cot_content' not in r, rel + ' answer leak')
                    if kind == 'performance.requests':
                        buckets[r['bucket']] += 1
                        perf_ids.append(r['id'])
                        require((r['input_tokens'], r['output_tokens']) == SHAPES[r['bucket']], rel + ' shape')
                        require(r['source_split'] == 'validation' and r['synthetic'], rel + ' source')
                        require(all(0 <= s['question_id'] < 70 for s in r['source_segments']), rel + ' source IDs')
                        h = hashlib.sha256(json.dumps(r['prompt_token_ids'], separators=(',', ':')).encode()).hexdigest()
                        require(h == r['token_ids_sha256'], rel + ' token hash')
                    elif kind == 'quality.requests':
                        quality_ids[r['id']] = r['num_options']
                        categories[r['category']] += 1
                    else:
                        answer_ids[r['id']] = r
            counts[kind] = len(seen)
        require(len(quality_ids) == len(answer_ids) == quality_count, tier + ' quality count')
        require(quality_ids.keys() == answer_ids.keys(), tier + ' answer IDs')
        for qid, options in quality_ids.items():
            a = answer_ids[qid]
            require(0 <= a['answer_index'] < options and a['answer'] == chr(65 + a['answer_index']), tier + ' answer')
        require(dict(buckets) == {f'P{i}': per_bucket for i in range(1, bucket_count + 1)}, tier + ' bucket counts')
        if tier == 'medium':
            require(set(quality_ids) == set(medium['quality_ids']), 'Medium quality manifest IDs')
            require(perf_ids == medium['performance_ids'], 'Medium performance manifest order')
            require(dict(categories) == medium['quality_categories'], 'Medium subject quotas')
        print(tier, json.dumps(counts), 'PASS', flush=True)
    require(large_matches == medium_hashes.keys(), 'All Medium records must be unchanged Large subsets')
    print('PASS: 9 files, exact token lengths, hashes, answer joins and Medium lineage')


if __name__ == '__main__':
    main()
