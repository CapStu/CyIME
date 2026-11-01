package com.kingzcheung.xime.association

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ItalianLexiconTest {
    private val lexicon by lazy {
        val path = "src/main/assets/italian/words.txt"
        ItalianLexicon(listOf(File(path), File("app/$path")).first { it.isFile }.readLines().filter { it.isNotBlank() })
    }

    @Test fun `accents do not have to be typed`() {
        assertEquals("città", lexicon.complete("citta", 5).first())
        assertEquals("perché", lexicon.complete("perche", 5).first())
        assertEquals("più", lexicon.complete("piu", 5).first())
        assertEquals("già", lexicon.complete("gia", 5).first())
        assertEquals("può", lexicon.complete("puo", 5).first())
        assertEquals("università", lexicon.complete("universita", 5).first())
        assertEquals("però", lexicon.complete("pero", 5).first())
    }

    @Test fun `completions follow frequency and never repeat the typed word`() {
        assertEquals(listOf("grazie", "grazia", "graziosa"), lexicon.complete("grazi", 3))
        assertFalse("grazie" in lexicon.complete("grazie", 20))
        assertTrue(lexicon.complete("", 5).isEmpty())
        assertTrue(lexicon.complete("zzzz", 5).isEmpty())
    }

    @Test fun `case follows what was typed and proper nouns stay capitalized`() {
        assertEquals("Città", lexicon.complete("Citta", 5).first())
        assertEquals("CITTÀ", lexicon.complete("CITTA", 5).first())
        assertEquals("Milano", lexicon.complete("milano", 5).first())
    }

    @Test fun `a typed accent only matches that letter`() {
        val small = ItalianLexicon(listOf("e", "è", "era", "ed"))
        assertEquals(listOf("è", "era", "ed"), small.complete("e", 5))
        // 打了 è 就只认 è：è 本身已在候选栏第一个，没有别的词。
        assertEquals(emptyList<String>(), small.complete("è", 5))
        assertEquals(listOf("era"), small.complete("er", 5))
    }

    @Test fun `exact accent variants come before longer words, each group by rank`() {
        val small = ItalianLexicon(listOf("citta", "città", "cittadino", "citrico"))
        assertEquals(listOf("città", "cittadino"), small.complete("citta", 5))
        // 打了 à 之后，不带重音的同形与更长的词都不该出现。
        assertEquals(emptyList<String>(), small.complete("città", 5))
    }
}
