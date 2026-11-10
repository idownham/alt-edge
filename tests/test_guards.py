"""Split and look-ahead/locking guards."""
import pytest

from bloodhound import db
from bloodhound.collect_markets import parse_event_desc, ticker_date
from bloodhound.event_map import candidate_dates, match_score, t_ref
from bloodhound.factbase import parse_calendar, start_utc
from bloodhound.http import PacedClient
from bloodhound.prices import is_word_market, last_candle_at_or_before
from bloodhound.split import period_for_first_close


@pytest.mark.parametrize("close,period", [
    ("2025-04-02T18:00:00Z", "dev"), ("2026-05-31T23:59:59Z", "dev"),
    ("2026-06-01T00:00:00Z", "test"), ("2026-10-14T23:00:00Z", "test"),
    ("2026-10-15T00:00:00Z", "locked"), ("2026-11-08T00:00:00Z", "locked"),
])
def test_split_boundaries(close, period):
    assert period_for_first_close(close) == period


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    for ev, period in (("E-DEV", "dev"), ("E-TEST", "test"), ("E-LOCK", "locked")):
        c.execute("INSERT INTO events(event_ticker, series, period) VALUES (?,?,?)", (ev, "S", period))
        c.execute("INSERT INTO markets(ticker, event_ticker, series) VALUES (?,?,?)", (ev + "-W", ev, "S"))
        c.execute("INSERT INTO results(ticker, result) VALUES (?,?)", (ev + "-W", "yes"))
    return c


def test_dev_outcomes_open(conn):
    assert db.outcomes(conn, "dev") == {"E-DEV-W": "yes"}


@pytest.mark.parametrize("period", ["test", "locked"])
def test_test_and_locked_outcomes_refused(conn, period):
    with pytest.raises(db.LockedPeriodError):
        db.outcomes(conn, period)
    with pytest.raises(db.LockedPeriodError):
        db.outcomes(conn, period, score_test=True)  # no hash
    with pytest.raises(db.LockedPeriodError):
        db.outcomes(conn, period, score_test=True, frozen_hash="abc1234", check_fn=lambda h: None)  # dirty / changed
    with pytest.raises(db.LockedPeriodError):
        db.outcomes(conn, period, score_test=True, frozen_hash="abc1234", check_fn=lambda h: "def1234567")


def test_test_outcomes_with_matching_frozen_hash(conn):
    out = db.outcomes(conn, "test", score_test=True, frozen_hash="abc1234", check_fn=lambda h: "abc1234567")
    assert out == {"E-TEST-W": "yes"}


def test_event_title_and_ticker_parsing():
    t = "What will Donald Trump say during Midterm Rally in Bullhead City, Arizona originally scheduled for October 14, 2026?"
    assert parse_event_desc(t) == "Midterm Rally in Bullhead City, Arizona"
    assert ticker_date("KXTRUMPMENTION-26OCT14") == "2026-10-14"
    assert ticker_date("KXTRUMPMENTION-25JUN25-2") == "2025-06-25"
    assert ticker_date("KXTRUMPMENTION-26MAY01C") == "2026-05-01"


def test_t_ref_and_dst():
    assert start_utc("2026-10-14", "16:00") == "2026-10-14T20:00:00Z"   # EDT
    assert start_utc("2026-01-14", "16:00") == "2026-01-14T21:00:00Z"   # EST
    assert t_ref("2026-10-14T20:00:00Z") == "2026-10-14T19:45:00Z"


def test_event_matching():
    assert match_score("Midterm Rally in Bullhead City, Arizona",
                       "The President holds a political rally in Bullhead City, Arizona [1:00 PM Local]", None) >= 0.75
    assert "2025-10-18" in candidate_dates("2025-10-19", "speech at Camp Pendleton on October 18th")


def test_last_candle_sparse():
    cs = [{"end_period_ts": 100}, {"end_period_ts": 160}, {"end_period_ts": 400}]
    assert last_candle_at_or_before(cs, 300)["end_period_ts"] == 160
    assert last_candle_at_or_before(cs, 160)["end_period_ts"] == 160
    assert last_candle_at_or_before(cs, 50) is None


def test_event_does_not_qualify_excluded():
    assert not is_word_market("Event does not qualify")
    assert is_word_market("Tariff")


def test_calendar_parser_minimal():
    page = """
    <div>Wednesday,</div><div>April 30, 2025</div>
    <div class="x tooltip" data-tooltip="Official Schedule"></div><div>11:00 AM</div>
    <div class="x tooltip" data-tooltip="Official Schedule"></div><div>11:00 AM</div>
    <a href="https://rollcall.com/factbase/trump/transcript/x/"> The President participates in a Cabinet Meeting</a>
    <div>Full Text and Analysis</div><div>Cabinet Room</div>
    """
    ev = parse_calendar(page)
    assert len(ev) == 1
    e = ev[0]
    assert (e["date"], e["time_et"], e["source_tag"], e["location"]) == ("2025-04-30", "11:00", "Official Schedule", "Cabinet Room")
    assert e["transcript_url"].endswith("/transcript/x/")


def test_paced_client_waits_and_backs_off():
    t = [0.0]
    sleeps = []
    def sleep(s):
        sleeps.append(s)
        t[0] += s
    c = PacedClient(min_interval_s=1.0, backoff_429_s=10, sleep=sleep, clock=lambda: t[0])
    responses = iter([(429, b""), (200, b"ok"), (200, b"ok2")])
    c._open = lambda url: next(responses)
    assert c.get_bytes("u") == b"ok"
    assert c.get_bytes("u") == b"ok2"
    assert 10 in sleeps                       # 429 back-off
    assert all(s <= 10 for s in sleeps)
    assert c.requests_made == 3


def test_transcript_parser_segments_and_speaker():
    from bloodhound.transcripts import parse_transcript, speaker_text
    seg = ('<h2 class="text-md inline">{spk}</h2> <span class="text-xs">{a}-{b} (5 sec)</span> <div>No StressLens</div>'
           '<div class=" flex-auto text-md text-gray-600 leading-loose">{txt}</div>')
    page = ('<meta name="twitter:title" content="Remarks: X &amp; Y" />'
            + seg.format(spk="Donald Trump", a="00:00:00", b="00:00:05", txt="We love our &quot;tariffs&quot;.")
            + seg.format(spk="Question", a="00:00:05", b="00:00:07", txt="What about China?")
            + seg.format(spk="Donald Trump", a="00:00:07", b="00:00:09", txt="China is <i>great</i>."))
    d = parse_transcript(page)
    assert d["title"] == "Remarks: X & Y"
    assert [s[0] for s in d["segments"]] == ["Donald Trump", "Question", "Donald Trump"]
    t = speaker_text(d)
    assert t == 'We love our "tariffs". China is great .'
    assert "What about" not in t   # reporters' questions never count as Trump saying a word
