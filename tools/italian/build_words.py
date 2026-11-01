"""Build app/src/main/assets/italian/words.txt, the Italian completion word list.

Mirrors tools/spanish/build_words.py: frequencies from FrequencyWords (OpenSubtitles 2018,
pinned commit), filtered against the LibreOffice Italian hunspell dictionary so subtitle
noise, English and typos do not reach the completion list.

The spell check is what fixes accents for free: the corpus writes "citta" and "città" both,
only the accented form is a valid Italian word, so the unaccented twin is dropped here
instead of needing a hand-written rule.

    python3 -m venv /tmp/spvenv && /tmp/spvenv/bin/pip install spylls
    curl -O https://raw.githubusercontent.com/LibreOffice/dictionaries/master/it_IT/it_IT.dic
    curl -O https://raw.githubusercontent.com/LibreOffice/dictionaries/master/it_IT/it_IT.aff
    /tmp/spvenv/bin/python tools/italian/build_words.py it_IT app/src/main/assets/italian/words.txt
"""
import re
import sys
import urllib.request

from spylls.hunspell import Dictionary

SOURCE = ("https://raw.githubusercontent.com/hermitdave/FrequencyWords/"
          "525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/it/it_50k.txt")
LIMIT = 40000
COMPOUND_LIMIT = 2000
ITALIAN = re.compile(r"^[a-zàèéìíòóùú']+$")
# Single letters that are real words: a, e, i, o (and è "is"). The rest is subtitle noise.
SINGLE = {"a", "e", "i", "o", "è", "y"}
# Elisions the corpus never writes with the apostrophe (it drops the accent instead).
# Hunspell cannot validate an elided form, so they are carried explicitly.
ELISIONS = {
    "dell'", "all'", "nell'", "sull'", "dall'", "coll'", "un'", "l'", "d'", "c'",
    "s'", "t'", "m'", "v'", "n'", "quest'", "sant'", "mezz'", "anch'", "dov'",
    "com'", "tutt'", "grand'", "bell'", "cent'", "vent'",
    "quell'", "cos'", "dev'", "quand'", "nessun'", "qualcun'", "ciascun'", "po'", "mo'",
}
# The corpus tokenises these apart (dell' + acqua), so the compounds are carried
# explicitly — same list the Rime dictionary build used before this pipeline.
CURATED_COMPOUNDS = {
    "dell'acqua", "dell'aria", "dell'anno", "dell'italia", "dell'uomo",
    "all'inizio", "all'interno", "all'estero", "all'aperto", "all'alba",
    "nell'aria", "nell'acqua", "nell'ambito", "nell'ultimo", "nell'istante",
    "sull'argomento", "sull'isola", "dall'inizio", "dall'altra", "dall'alto",
    "coll'aiuto", "quest'anno", "quest'ultimo", "quest'estate", "quest'oggi",
    "un'ora", "un'idea", "un'altra", "un'altro", "un'estate", "un'immagine",
    "un'azione", "un'occasione", "d'accordo", "d'ora", "d'altra", "d'italia",
    "l'unica", "l'unico", "l'italia", "l'acqua", "l'aria", "l'uomo", "l'anno",
    "c'era", "c'erano", "c'è", "com'è", "dov'è", "tutt'altro", "mezz'ora",
}


def main(dictionary_base: str, output: str) -> None:
    speller = Dictionary.from_files(dictionary_base)
    lines = urllib.request.urlopen(SOURCE).read().decode("utf-8").splitlines()
    seen, words = set(), []
    compounds: list[tuple[str, str]] = []
    dropped = kept_apostrophe = 0
    for line in lines:
        parts = line.split()
        if len(parts) != 2:
            continue
        word, _count = parts
        if not ITALIAN.match(word) or (len(word) == 1 and word not in SINGLE):
            dropped += 1
            continue
        if "'" in word:
            # "dell'acqua" / "quest'anno": kept in a second pass once the plain
            # words are known (the tail must itself be a valid word).
            head, _, tail = word.partition("'")
            if head + "'" in ELISIONS and tail:
                compounds.append((word, tail))
            elif word in ELISIONS:
                kept_apostrophe += 1
                if word not in seen:
                    seen.add(word)
                    words.append(word)
            else:
                dropped += 1
            continue
        form = word if speller.lookup(word) else word.capitalize() if speller.lookup(word.capitalize()) else None
        if form is None:
            dropped += 1
            continue
        if form in seen:
            continue
        seen.add(form)
        words.append(form)
        if len(words) >= LIMIT:
            break

    # Elided compounds are only usable when the tail is a real word: that keeps
    # "dell'acqua" and throws away "dell'cosa"-style corpus noise.
    known = {w.lower() for w in words}
    kept_compound = 0
    for word in sorted(CURATED_COMPOUNDS):
        tail = word.partition("'")[2]
        if tail and tail in known and word not in seen:
            seen.add(word)
            words.append(word)
            kept_compound += 1
    for word, tail in compounds:
        if tail not in known or word in seen:
            continue
        seen.add(word)
        words.append(word)
        kept_compound += 1
        if len(words) >= LIMIT + COMPOUND_LIMIT:
            break
    with open(output, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(words) + "\n")
    print(f"{len(words)} words -> {output} (dropped {dropped}, bare elisions {kept_apostrophe}, "
          f"elided compounds {kept_compound})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
