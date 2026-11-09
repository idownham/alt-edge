"""Every example from Kalshi's MENTION.pdf contract terms ("NEWMENTION", fetched 2026-11-09), section
"Additional clarification(s)". Examples that depend on pronunciation can't be decided from transcript
text: they are strict xfails so the limitation stays visible."""
import pytest

from bloodhound.matcher import said, tokenize, plural_forms, cardinal_words

COUNTS = [
    ("Immigrant", "We love legal immigrants."),
    ("Egg", "the eggs' shells were cracked"),
    ("Russia", "Russia's economy"),
    ("Cat", "I saw Cats the musical"),
    ("Wind", "he winds up the clock"),
    ("fire", "the fire station"),
    ("couch", "a couch potato"),
    ("Palestine", "a pro-Palestine march"),
    ("fat", "non-fat milk"),
    ("New York", "a New York-based company"),
    ("MAGA", "it was MAGA-nificent"),
    ("bass", "bass guitar"),
    ("bass", "bass fishing"),
    ("Apple", "Apple Inc. is big"),
    ("Apple", "I ate an apple"),
    ("Will", "Will Smith was there"),
    ("Will", "I will go"),
    ("uber", "I took an Uber"),
    ("five", "it cost five dollars"),
    ("five", "it cost $5"),
    ("trillion", "five trillion dollars"),
    ("410", "four hundred ten"),
    ("410", "four one zero"),
    ("410", "four ten"),
    ("January 6", "January 6th"),
    ("3", "the 3rd time"),
    ("3", "the third time"),
    ("Eight War", "we ended 8 wars"),
    ("Eight War", "the Eighth War"),
    ("NASA", "N-A-S-A"),
    ("Doctor", "Dr. Oz"),
    ("policy", "Nuestra policy es clara"),
    ("Securities", "Bank of America Securities"),
    ("Doge/Dogecoin", "I like Dogecoin"),
    ("Doge/Dogecoin", "DOGE cut spending"),
    ("Veterans", "our veterans' benefits"),
]

DOES_NOT_COUNT = [
    ("Russia", "a Russian ship"),
    ("Economic", "Economics is hard"),
    ("Immigrant", "Immigration is up"),
    ("Run", "I was running"),
    ("Run", "he ran"),
    ("Veterans", "a veteran spoke"),
    ("fire", "a wildfire"),
    ("fire", "the firefighter"),
    ("magnificent", "it was MAGA-nificent"),
    ("write", "you're right"),
    ("lift", "I took a Lyft"),
    ("five", "five hundred people"),
    ("one", "the first time"),
    ("first", "one time"),
    ("AI", "artificial intelligence"),
    ("fire", "fuego"),
]

# Need audio, not text (Kalshi resolves from video; our corpus is text).
NEEDS_AUDIO = [
    ("NASA", "NAH-suh"),            # acronym pronounced as a word -> transcript writes NASA anyway
    ("Mamdani", "Mandani"),         # minor mispronunciation counts
    ("Zelensky", "Zelenskiy"),      # transliteration variants count
    ("fire", "firestation.com"),    # URL read aloud as "fire station dot com" counts
    ("money", "moneyyy"),           # extended sung word counts
]


@pytest.mark.parametrize("word,text", COUNTS)
def test_contract_examples_count(word, text):
    assert said(word, text)


@pytest.mark.parametrize("word,text", DOES_NOT_COUNT)
def test_contract_examples_do_not_count(word, text):
    assert not said(word, text)


@pytest.mark.parametrize("word,text", NEEDS_AUDIO)
@pytest.mark.xfail(strict=True, reason="depends on pronunciation; not decidable from transcript text")
def test_contract_examples_needing_audio(word, text):
    assert said(word, text)


def test_url_apple_dot_com_counts_via_tokenizer():
    # "apple.com" pronounced "apple dot com" counts; the tokenizer splits on '.' so this works.
    assert said("apple", "apple.com is down")


def test_negative_url_wildfire():
    assert not said("fire", "wildfire.com")


def test_tokenize_and_forms():
    assert tokenize("Trump’s pro-Palestine U.S. plan") == ["trump's", "pro", "palestine", "us", "plan"]
    assert {"tariffs", "tariff's", "tariffs'"} <= plural_forms("tariff")
    assert "economics" not in plural_forms("economic")
    assert cardinal_words(410) == ["four", "hundred", "ten"]


def test_ordinals_not_allowed_for_single_number_word():
    assert not said("Eight", "the eighth time")
    assert said("Eight", "eight times")
