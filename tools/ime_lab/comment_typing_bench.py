"""Can real comments be typed? Replay B站 comments / QQ group chat through the host engine (2026-11-03).

Every message is cut into clauses (runs of Chinese characters between punctuation, emotes, Latin, digits). A clause is
typed in one go as a "sentence" case; jieba words of the clause are typed one at a time as "word" cases. Each case is
replayed by host_replay/RealTypingProbe.java (type mode: no learning, every case starts from the same state), which
gives the target's rank among the first 100 candidates and how many stops a person needs to get it on screen.

  comment_typing_bench.py cases OUT_DIR SOURCE... [--column NAME] [--max-len 20] [--charset 8105.dict.yaml]
      SOURCE: .csv (column NAME, default 内容), .tsv (last column, \\n escaped), anything else one message per line.
      --charset: clauses with a character outside this dictionary (traditional, rare) are left out and counted.
      Writes OUT_DIR/{full,flypy,t9}-{sent,mixed,word}.tsv (id, keys, target, count) for RealTypingProbe; "mixed" are
      clauses typed next to Latin letters or digits (26键), scored apart because the engine never sees that context.
  comment_typing_bench.py userdir REPO USER [t9_ngram.lm]   fresh user directory (rime_ice, flypy, t9 enabled)
  comment_typing_bench.py floors USER FLOORS.tsv            try cyime_domain_terms.tsv-style floors before deploying
  comment_typing_bench.py run OUT_DIR LIB USER CLASSES NEIGHBORS [full,flypy,t9]
  comment_typing_bench.py score OUT_DIR [--private] [--top 40]
      Reads OUT_DIR/result-<scheme>-<kind>.tsv, writes OUT_DIR/summary.json and failures-<scheme>.tsv.
      --private: failures list words only (no clause text), for chat that must not leave the computer.

Pinyin comes from pypinyin (phrase-aware); its wrong readings show up as failures and are checked by hand before
anything is changed. ü is typed as v (lv, nv), as on the phone.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HAN = re.compile(r"[㐀-䶿一-鿿]+")
REPLY = re.compile(r"^回复 @[^:：]{1,40}[:：]")
EMOTE = re.compile(r"\[[^\[\]]{1,16}\]")
# Chunks end at punctuation, symbols and spaces; Latin letters and digits stay inside (they are typed in place).
CHUNK = re.compile(r"[^\w]+|_+")

FLY_INITIAL = {"zh": "v", "ch": "i", "sh": "u"}
FLY_FINAL = {"iu": "q", "ei": "w", "uan": "r", "van": "r", "ue": "t", "ve": "t", "un": "y", "vn": "y", "uo": "o",
             "ie": "p", "ong": "s", "iong": "s", "ai": "d", "en": "f", "eng": "g", "ang": "h", "an": "j",
             "ing": "k", "uai": "k", "iang": "l", "uang": "l", "ou": "z", "ia": "x", "ua": "x", "ao": "c",
             "ui": "v", "v": "v", "in": "b", "iao": "n", "ian": "m"}
FLY_ZERO = {"a": "aa", "e": "ee", "o": "oo", "ang": "ah", "eng": "eg", "ai": "ai", "an": "an", "ao": "ao",
            "ei": "ei", "en": "en", "er": "er", "ou": "ou"}
T9 = {c: d for d, letters in {"2": "abc", "3": "def", "4": "ghi", "5": "jkl", "6": "mno", "7": "pqrs", "8": "tuv",
                              "9": "wxyz"}.items() for c in letters}
INITIALS = ("zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x", "r", "z", "c",
            "s", "y", "w")


def flypy(syllable):
    if syllable in FLY_ZERO:
        return FLY_ZERO[syllable]
    for i in INITIALS:
        if syllable.startswith(i) and len(syllable) > len(i):
            initial, final = i, syllable[len(i):]
            break
    else:
        return syllable  # unexpected, leave it (shows up as a failure)
    if initial in "jqxy" and final.startswith("u"):
        final = "v" + final[1:]  # ju = jü
    key = FLY_FINAL.get(final, final if len(final) == 1 else None)
    if key is None:
        return syllable
    return FLY_INITIAL.get(initial, initial) + key


def messages(path, column):
    path = Path(path)
    if path.suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                yield row.get(column, "")
    elif path.suffix == ".tsv":
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            yield line.split("\t")[-1].replace("\\n", "\n")
    else:
        yield from path.read_text(encoding="utf-8-sig").splitlines()


def clauses(text):
    """(clause, mixed): mixed = typed right after or before Latin letters or digits in the same chunk (26键, Pro版),
    so the engine sees the clause without what was typed next to it."""
    text = EMOTE.sub(" ", REPLY.sub("", text.strip()))
    for chunk in CHUNK.split(text):
        runs = HAN.findall(chunk)
        for run in runs:
            yield run, run != chunk


# pypinyin readings that are wrong in phone/IME talk (checked by hand 2026-11-03): 长按 is not zhang an, 行尾 not
# xing wei, 重试 not zhong shi. 调 as "adjust" (调大, 怎么调) is tiao; pypinyin reads a lone 调 as diao.
READINGS = {"长按": "chang an", "长串": "chang chuan", "长句": "chang ju", "行尾": "hang wei", "行首": "hang shou",
            "每行": "mei hang", "单行": "dan hang", "多行": "duo hang", "一行": "yi hang", "首行": "shou hang",
            "行距": "hang ju", "行高": "hang gao", "行数": "hang shu", "重码": "chong ma", "重试": "chong shi",
            "重启": "chong qi", "重装": "chong zhuang", "重打": "chong da", "重输": "chong shu", "重做": "chong zuo",
            "重来": "chong lai", "重选": "chong xuan", "微调": "wei tiao", "可调": "ke tiao", "长按键": "chang an jian"}
DIAO = ("调查", "调动", "调用", "调度", "调研", "调派", "调换", "调包", "调子", "音调", "声调", "单调", "语调", "曲调",
        "腔调", "格调", "基调", "论调", "强调", "色调", "调兵", "调任", "调职", "调令", "调档", "调配", "外调", "内调",
        "借调", "抽调", "调走", "调来", "调虎离山")


def cases(argv):
    import jieba
    from pypinyin import Style, lazy_pinyin, load_phrases_dict
    jieba.setLogLevel(60)
    column, max_len, out, sources, charset = "内容", 20, None, [], None
    it = iter(argv)
    for a in it:
        if a == "--column":
            column = next(it)
        elif a == "--max-len":
            max_len = int(next(it))
        elif a == "--charset":
            charset = set(re.findall(r"(?m)^(.)\t", Path(next(it)).read_text(encoding="utf-8")))
        elif out is None:
            out = Path(a)
        else:
            sources.append(a)
    out.mkdir(parents=True, exist_ok=True)
    sent, mixed, word = Counter(), Counter(), Counter()
    total_messages = outside = 0
    for source in sources:
        for m in messages(source, column):
            total_messages += 1
            for c, beside in clauses(m):
                if charset is not None and not set(c) <= charset:
                    outside += 1
                    continue
                if 2 <= len(c) <= max_len:
                    (mixed if beside else sent)[c] += 1
                for w in jieba.cut(c, HMM=False):
                    if HAN.fullmatch(w):
                        word[w] += 1

    load_phrases_dict({k: [[x] for x in v.split()] for k, v in READINGS.items()}, style="normal")

    def reading(text):
        syllables = lazy_pinyin(text, style=Style.NORMAL, errors="ignore")
        if "调" in text and len(syllables) == len(text):
            start = 0
            for w in jieba.cut(text, HMM=False):
                for i, ch in enumerate(w):
                    if ch == "调" and w not in DIAO and not any(d in text for d in DIAO):
                        syllables[start + i] = "tiao"
                start += len(w)
        if len(syllables) != len(text) or not all(s.isascii() and s.isalpha() for s in syllables):
            return None
        return [s.replace("ü", "v") for s in syllables]

    skipped = 0
    for kind, table in (("sent", sent), ("mixed", mixed), ("word", word)):
        files = {s: (out / f"{s}-{kind}.tsv").open("w", encoding="utf-8") for s in ("full", "flypy", "t9")}
        for n, (text, count) in enumerate(table.most_common()):
            syllables = reading(text)
            if syllables is None:
                skipped += 1
                continue
            full = "".join(syllables)
            keys = {"full": full, "flypy": "".join(map(flypy, syllables)), "t9": "".join(T9[c] for c in full)}
            for s, f in files.items():
                f.write(f"{kind}{n}\t{keys[s]}\t{text}\t{count}\n")
        for f in files.values():
            f.close()
    info = {"messages": total_messages, "clauses": sum(sent.values()), "unique_clauses": len(sent),
            "mixed_clauses": sum(mixed.values()),
            "words": sum(word.values()), "unique_words": len(word), "skipped_no_reading": skipped,
            "skipped_outside_charset": outside}
    (out / "cases.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))


def load(path, counts):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        f = line.split("\t")
        if len(f) < 9:
            continue
        rows.append({"id": f[0], "keys": f[1], "target": f[2], "rank": int(f[3]), "first": f[4],
                     "stops": int(f[6]), "stuck": f[7] == "1", "top": f[10] if len(f) > 10 else "",
                     "count": counts.get(f[0], 1)})
    return rows


def rates(rows):
    n = sum(r["count"] for r in rows) or 1
    u = len(rows) or 1
    chars = sum(len(r["target"]) * r["count"] for r in rows) or 1
    return {
        "cases": len(rows), "weighted": n,
        "top1": round(100 * sum(r["count"] for r in rows if r["rank"] == 0) / n, 1),
        "top3": round(100 * sum(r["count"] for r in rows if 0 <= r["rank"] < 3) / n, 1),
        "top1_unique": round(100 * sum(1 for r in rows if r["rank"] == 0) / u, 1),
        "top3_unique": round(100 * sum(1 for r in rows if 0 <= r["rank"] < 3) / u, 1),
        "absent_top100": round(100 * sum(r["count"] for r in rows if r["rank"] < 0) / n, 1),
        "stuck": round(100 * sum(r["count"] for r in rows if r["stuck"]) / n, 1),
        "stops_per_100_chars": round(100 * sum(r["stops"] * r["count"] for r in rows) / chars, 1),
    }


def by_length(rows):
    buckets = defaultdict(list)
    for r in rows:
        n = len(r["target"])
        buckets["2-4" if n <= 4 else "5-8" if n <= 8 else "9-12" if n <= 12 else "13+"].append(r)
    return {k: rates(v) for k, v in sorted(buckets.items())}


def sentence_errors(rows):
    """Wrong words inside clauses whose first candidate is wrong: target word -> what the first candidate had there."""
    import jieba
    jieba.setLogLevel(60)
    errors, partial = Counter(), 0
    for r in rows:
        target, first = r["target"], r["first"]
        if r["rank"] == 0:
            continue
        if len(first) != len(target):
            partial += r["count"]
            continue
        start = 0
        for w in jieba.cut(target, HMM=False):
            end = start + len(w)
            if first[start:end] != w:
                errors[(w, first[start:end])] += r["count"]
            start = end
    return errors, partial


def score(argv):
    out = Path(argv[0])
    private = "--private" in argv
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 40
    summary = {"cases": json.loads((out / "cases.json").read_text(encoding="utf-8"))}
    for scheme in ("full", "flypy", "t9"):
        parts = {}
        for kind in ("sent", "mixed", "word"):
            result = out / f"result-{scheme}-{kind}.tsv"
            if not result.is_file():
                continue
            counts = {}
            for line in (out / f"{scheme}-{kind}.tsv").read_text(encoding="utf-8").splitlines():
                f = line.split("\t")
                counts[f[0]] = int(f[3])
            rows = load(result, counts)
            parts[kind] = rows
            summary[f"{scheme}-{kind}"] = rates(rows)
            if kind == "mixed":
                pass
            elif kind == "sent":
                summary[f"{scheme}-sent-by-length"] = by_length(rows)
                errors, partial = sentence_errors(rows)
                summary[f"{scheme}-sent-first-not-whole"] = partial
                with (out / f"sentence-word-errors-{scheme}.tsv").open("w", encoding="utf-8") as f:
                    f.write("count\ttarget_word\tfirst_had\n")
                    for (w, got), n in errors.most_common(top * 10):
                        f.write(f"{n}\t{w}\t{got}\n")
            else:
                summary[f"{scheme}-word-2plus"] = rates([r for r in rows if len(r["target"]) >= 2])
        if "word" in parts:
            words = sorted((r for r in parts["word"] if r["rank"] != 0), key=lambda r: (-r["count"], r["rank"]))
            with (out / f"failures-{scheme}.tsv").open("w", encoding="utf-8") as f:
                f.write("kind\tcount\ttarget\tkeys\trank\tfirst\ttop\n")
                for r in words[: top * 5]:
                    f.write(f"word\t{r['count']}\t{r['target']}\t{r['keys']}\t{r['rank']}\t{r['first']}\t"
                            f"{r['top'] if not private else ''}\n")
                if not private and "sent" in parts:
                    sents = sorted((r for r in parts["sent"] if r["rank"] != 0),
                                   key=lambda r: (-r["count"], -r["stuck"], len(r["target"])))
                    for r in sents[: top * 5]:
                        f.write(f"sent\t{r['count']}\t{r['target']}\t{r['keys']}\t{r['rank']}\t{r['first']}\t"
                                f"{r['top']}\n")
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


SCHEMAS = {"full": "rime_ice", "flypy": "double_pinyin_flypy", "t9": "t9_pinyin"}


def userdir(argv):
    """userdir REPO OUT [NGRAM]: fresh user directory as the app deploys it (rime_ice, flypy, t9 enabled)."""
    import shutil
    repo, out = Path(argv[0]), Path(argv[1])
    assets = repo / "app/src/main/assets"
    if out.exists():
        raise SystemExit(f"{out} exists; use a new directory")
    shutil.copytree(assets / "rime", out)
    text = (assets / "default.custom.yaml").read_text(encoding="utf-8")
    text = re.sub(r"(?m)^    - schema: (?!rime_ice$|double_pinyin_flypy$|t9_pinyin$)\S+\n", "", text)
    (out / "default.custom.yaml").write_text(text, encoding="utf-8")
    skip = {"pinyin_qwjrtk.schema.yaml", "pinyin_cyletix10.schema.yaml", "pinyin_colemak.schema.yaml",
            "pinyin_typewise.schema.yaml"}
    generated = repo / "app/build/generated/chinese-assets/rime_ice"
    if not (generated / "rime_ice.dict.yaml").is_file():
        raise SystemExit(f"{generated} missing: run prepareChineseDictionaries first")
    for root, ice in ((generated, True), (assets / "rime_chinese", False)):
        for p in sorted(root.rglob("*")):
            r = p.relative_to(root).as_posix()
            if (not p.is_file() or r.endswith(".md") or r.startswith("LICENSE") or r.endswith(".custom.yaml")
                    or (ice and r in skip)):
                continue
            (out / r).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, out / r)
    if len(argv) > 2:
        shutil.copyfile(argv[2], out / "t9_ngram.lm")


def floors(argv):
    """floors USER TSV: apply app/data/cyime_domain_terms.tsv-style floors (text, code, weight) to a not yet deployed
    user directory the way tasks-chinese.gradle.kts does, to try a lexicon change without regenerating the assets."""
    user, rows = Path(argv[0]), {}
    for line in Path(argv[1]).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            text, code, weight = line.split("\t")
            rows[(text, code)] = int(weight)
    present, by_text = set(), {text: (text, code) for text, code in rows}
    for name in ("base", "ext", "tencent"):
        path = user / f"cn_dicts/{name}.dict.yaml"
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            f = line.split("\t")
            if len(f) == 3 and (f[0], f[1]) in rows and f[2].isdigit():
                present.add((f[0], f[1]))
                lines[i] = f"{f[0]}\t{f[1]}\t{max(int(f[2]), rows[(f[0], f[1])])}"
            elif len(f) == 2 and f[0] in by_text and f[1].isdigit():  # tencent: text, weight
                present.add(by_text[f[0]])
                lines[i] = f"{f[0]}\t{max(int(f[1]), rows[by_text[f[0]]])}"
        path.write_text("\n".join(lines), encoding="utf-8")
    terms = user / "cyime_terms.dict.yaml"
    present |= {tuple(line.split("\t")[:2]) for line in terms.read_text(encoding="utf-8").splitlines()}
    with terms.open("a", encoding="utf-8") as out:
        for (text, code), weight in rows.items():
            if (text, code) not in present:
                out.write(f"{text}\t{code}\t{weight}\n")


def run(argv):
    """run OUT_DIR LIB USER CLASSES NEIGHBORS [schemes, default full,flypy,t9]: one RealTypingProbe pass per file."""
    import os
    import subprocess
    out, lib, user, classes, neighbors = map(Path, argv[:5])
    schemes = argv[5].split(",") if len(argv) > 5 else list(SCHEMAS)
    neighbor_map = neighbors.read_text(encoding="utf-8").strip()
    for scheme in schemes:
        for kind in ("word", "sent", "mixed"):
            if not (out / f"{scheme}-{kind}.tsv").is_file():
                continue
            env = dict(os.environ, PROBE_SCHEMA=SCHEMAS[scheme])
            # Touch-noise neighbour correction is a 26-key feature; nine-key and double pinyin get no map.
            args = ["java", "-Dstdout.encoding=UTF-8", "-Dfile.encoding=UTF-8", "-cp", str(classes),
                    "RealTypingProbe", "type", str(lib), str(user), str(out / f"{scheme}-{kind}.tsv"),
                    str(out / f"result-{scheme}-{kind}.tsv"), neighbor_map if scheme == "full" else ""]
            print("RUN", scheme, kind, file=sys.stderr, flush=True)
            subprocess.run(args, check=True, env=env, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    {"cases": cases, "score": score, "userdir": userdir, "floors": floors, "run": run}[sys.argv[1]](sys.argv[2:])
