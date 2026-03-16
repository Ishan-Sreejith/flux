from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from animal1010101.engine import LexicalEngine
from animal1010101.lexicon_store import LexiconStore
from animal1010101.schema_engine import SchemaEngine
from animal1010101.wikidata_lookup import category_entities, describe_many


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Animal1010101 lexical engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode")
    enc.add_argument("word")

    cmp = sub.add_parser("compare")
    cmp.add_argument("word_a")
    cmp.add_argument("word_b")

    sim = sub.add_parser("similarity")
    sim.add_argument("word_a")
    sim.add_argument("word_b")

    prm = sub.add_parser("params")
    prm.add_argument("word")

    auto = sub.add_parser("lookup")
    auto.add_argument("word")

    amap = sub.add_parser("automap")
    amap.add_argument("word")

    sch = sub.add_parser("schema")
    sch.add_argument("text")

    scr = sub.add_parser("script")
    scr.add_argument("key")

    train = sub.add_parser("train-category")
    train.add_argument("qid", help="Wikidata QID (e.g. Q7377 for mammals)")
    train.add_argument("--limit", type=int, default=50)
    train.add_argument("--out", type=Path, default=None)

    imp = sub.add_parser("import-lexicon")
    imp.add_argument("path", type=Path)
    imp.add_argument("--reset", action="store_true", help="Replace lexicon_auto.json instead of merging")

    learn = sub.add_parser("learn")
    learn.add_argument("word", nargs="+")

    snap = sub.add_parser("snapshot")
    snap.add_argument("--reason", type=str, default="manual")

    snaps = sub.add_parser("snapshots")

    rollback = sub.add_parser("rollback")
    rollback.add_argument("--to", type=Path, default=None)

    train_list = sub.add_parser("train-list")
    train_list.add_argument("path", type=Path)
    train_list.add_argument("--limit", type=int, default=10000)
    train_list.add_argument("--sleep-ms", type=int, default=120)
    train_list.add_argument("--out", type=Path, default=None)
    train_list.add_argument("--import", dest="do_import", action="store_true")
    train_list.add_argument("--prefetch", action="store_true", help="Prefetch Wikidata descriptions in parallel")
    train_list.add_argument("--prefetch-workers", type=int, default=None)

    warm = sub.add_parser("warm-cache")
    warm.add_argument("path", type=Path, help="Text file with one term per line")
    warm.add_argument("--limit", type=int, default=2000)
    warm.add_argument("--workers", type=int, default=None)

    evalp = sub.add_parser("eval")
    evalp.add_argument("--auto-learn", action="store_true")

    tw = sub.add_parser("train-weights")
    tw.add_argument("--data", type=Path, default=Path(__file__).resolve().parent / "train_data.json")
    tw.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "model_weights.json")

    td = sub.add_parser("train-disambig")
    td.add_argument("--data", type=Path, default=Path(__file__).resolve().parent / "disambig_data.json")
    td.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "disambig_weights.json")

    exp = sub.add_parser("auto-expand")
    exp.add_argument("--limit", type=int, default=120)

    presets = sub.add_parser("train-preset")
    presets.add_argument("group", type=str, help="mammals | reptiles | birds | fish | animals_common")
    presets.add_argument("--import", dest="do_import", action="store_true")

    animals = sub.add_parser("train-animals")
    animals.add_argument("--limit-per-category", type=int, default=120)
    animals.add_argument("--out", type=Path, default=None)
    animals.add_argument("--import", dest="do_import", action="store_true")

    return p


def main() -> None:
    args = build_parser().parse_args()
    engine = LexicalEngine(Path(__file__).resolve().parent)
    store = LexiconStore(Path(__file__).resolve().parent)

    if args.cmd == "encode":
        res = engine.encode(args.word)
        print(f"{res.prime}{res.bitstring}")
        print(f"path={res.path}")
        print(f"params={res.parameters}")
        return

    if args.cmd == "compare":
        match, ra, rb = engine.compare(args.word_a, args.word_b)
        print(f"match={match}")
        print(f"a={ra.prime}{ra.bitstring} path={ra.path}")
        print(f"b={rb.prime}{rb.bitstring} path={rb.path}")
        return

    if args.cmd == "similarity":
        score, ra, rb = engine.similarity(args.word_a, args.word_b)
        print(f"score={score:.3f}")
        print(f"a={ra.prime}{ra.bitstring} path={ra.path} params={ra.parameters}")
        print(f"b={rb.prime}{rb.bitstring} path={rb.path} params={rb.parameters}")
        return

    if args.cmd == "params":
        res = engine.encode(args.word)
        print(res.parameters)
        return

    if args.cmd == "lookup":
        res = engine.encode(args.word)
        print(f"{res.prime}{res.bitstring}")
        print(f"path={res.path}")
        print(f"params={res.parameters}")
        return

    if args.cmd == "automap":
        res = engine.encode(args.word)
        print(f"{res.prime}{res.bitstring}")
        print(f"path={res.path}")
        print(f"params={res.parameters}")
        return

    if args.cmd == "schema":
        schema = SchemaEngine(Path(__file__).resolve().parent)
        res = schema.interpret(args.text)
        print(f"activated={res.activated}")
        print(f"params={res.parameters}")
        print(f"scripts={res.scripts}")
        print(f"accommodation={res.accommodation}")
        return

    if args.cmd == "script":
        schema = SchemaEngine(Path(__file__).resolve().parent)
        print(schema.script_for(args.key.lower()))
        return

    if args.cmd == "train-category":
        items = category_entities(args.qid, limit=args.limit)
        results = {}
        for item in items:
            res = engine.encode(item)
            results[item.lower()] = {"prime": res.prime, "path": res.path}
        payload = json.dumps(results, indent=2)
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return

    if args.cmd == "import-lexicon":
        store.snapshot("import-lexicon")
        data = json.loads(args.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Lexicon file must be a JSON object")
        if args.reset:
            engine.lexicon_auto = {}
        engine.lexicon_auto.update(data)
        engine.lexicon_auto_path.write_text(
            json.dumps(engine.lexicon_auto, indent=2),
            encoding="utf-8",
        )
        print(f"Imported {len(data)} entries into lexicon_auto.json")
        return

    if args.cmd == "learn":
        store.snapshot("learn")
        for w in args.word:
            res = engine.learn(w)
            print(f"{w} -> {res.prime}{res.bitstring} path={res.path}")
        return

    if args.cmd == "snapshot":
        snap_path = store.snapshot(args.reason)
        print(f"Snapshot saved: {snap_path}")
        return

    if args.cmd == "snapshots":
        for p in store.list_snapshots():
            print(p)
        return

    if args.cmd == "rollback":
        target = args.to or store.latest_snapshot()
        if not target:
            raise ValueError("No snapshots available.")
        data = store.rollback(target)
        engine.lexicon_auto = data
        print(f"Rolled back to {target}")
        return

    if args.cmd == "train-list":
        words = [w.strip().lower() for w in args.path.read_text(encoding="utf-8").splitlines()]
        words = [w for w in words if w]
        if args.limit:
            words = words[: args.limit]
        if args.prefetch:
            describe_many(words, max_workers=args.prefetch_workers)
        results = {}
        for i, w in enumerate(words, 1):
            prime, path = engine.infer(w)
            results[w] = {"prime": prime, "path": path}
            if args.sleep_ms:
                time.sleep(args.sleep_ms / 1000.0)
            if i % 500 == 0:
                print(f"trained {i}/{len(words)}")
        payload = json.dumps(results, indent=2)
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        if args.do_import:
            store.snapshot("train-list")
            engine.lexicon_auto.update(results)
            engine.lexicon_auto_path.write_text(
                json.dumps(engine.lexicon_auto, indent=2),
                encoding="utf-8",
            )
        if not args.out:
            print(payload)
        return

    if args.cmd == "warm-cache":
        terms = [w.strip() for w in args.path.read_text(encoding="utf-8").splitlines()]
        terms = [w for w in terms if w]
        if args.limit:
            terms = terms[: args.limit]
        results = describe_many(terms, max_workers=args.workers)
        hits = sum(1 for v in results.values() if v)
        print(f"Warm cache done. {hits}/{len(results)} with descriptions.")
        return

    if args.cmd == "eval":
        from animal1010101.eval import run

        raise SystemExit(run(auto_learn=args.auto_learn))

    if args.cmd == "train-weights":
        from animal1010101.train_weights import train

        train(args.data, args.out)
        print(f"Saved weights to {args.out}")
        return

    if args.cmd == "train-disambig":
        from animal1010101.train_disambig import train

        train(args.data, args.out)
        print(f"Saved disambiguation weights to {args.out}")
        return

    if args.cmd == "auto-expand":
        from animal1010101.auto_expand import expand

        store.snapshot("auto-expand")
        data = expand(limit=args.limit)
        engine.lexicon_auto.update(data)
        engine.lexicon_auto_path.write_text(
            json.dumps(engine.lexicon_auto, indent=2),
            encoding="utf-8",
        )
        print(f"Auto-expanded {len(data)} entries into lexicon_auto.json")
        return

    if args.cmd == "train-preset":
        from animal1010101.train_presets import load_group

        store.snapshot("train-preset")
        data = load_group(args.group)
        if args.do_import:
            engine.lexicon_auto.update(data)
            engine.lexicon_auto_path.write_text(
                json.dumps(engine.lexicon_auto, indent=2),
                encoding="utf-8",
            )
            print(f"Imported {len(data)} entries into lexicon_auto.json")
        else:
            print(json.dumps(data, indent=2))
        return

    if args.cmd == "train-animals":
        from animal1010101.train_animals import build_animals, save_animals

        store.snapshot("train-animals")
        data = build_animals(limit_per_category=args.limit_per_category)
        if args.out:
            save_animals(args.out, data)
        if args.do_import:
            engine.lexicon_auto.update(data)
            engine.lexicon_auto_path.write_text(
                json.dumps(engine.lexicon_auto, indent=2),
                encoding="utf-8",
            )
            print(f"Imported {len(data)} entries into lexicon_auto.json")
        else:
            print(json.dumps(data, indent=2))
        return


if __name__ == "__main__":
    main()
