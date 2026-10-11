import json
from pathlib import Path

import pytest

from fiverr_gig import __version__, keywords, pricing, rules
from fiverr_gig.audit import audit
from fiverr_gig.cli import main
from fiverr_gig.lint import lint
from fiverr_gig.loader import GigFormatError, gigs_from_data, load_path, normalize, parse_markdown

EX = Path(__file__).resolve().parent.parent / "examples"


def gig(**over):
    base = load_path(EX / "strong-gig.json")[0]
    base.update(over)
    return base


# ---------- loader ----------
def test_load_json_strong():
    g = load_path(EX / "strong-gig.json")[0]
    assert g["title"].startswith("I will")
    assert len(g["tags"]) == 5
    assert set(g["packages"]) == {"basic", "standard", "premium"}
    assert g["packages"]["basic"]["price"] == 60.0


def test_load_markdown():
    g = load_path(EX / "needs-work-gig.md")[0]
    assert g["packages"]["premium"]["price"] == 900.0
    assert g["packages"]["basic"]["days"] == 7
    assert len(g["faq"]) == 1
    assert g["images"][0]["width"] == 800


def test_legacy_config_format_is_accepted():
    cfg = json.loads((Path(__file__).resolve().parent.parent / "config-example.json").read_text(encoding="utf-8"))
    gigs = gigs_from_data(cfg)
    assert len(gigs) == 1
    assert gigs[0]["packages"]["standard"]["price"] == 247.0
    assert gigs[0]["packages"]["basic"]["days"] == 3
    assert gigs[0]["description"]


def test_loader_errors(tmp_path):
    with pytest.raises(GigFormatError):
        load_path(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{nope", encoding="utf-8")
    with pytest.raises(GigFormatError):
        load_path(bad)
    odd = tmp_path / "x.xml"
    odd.write_text("<a/>", encoding="utf-8")
    with pytest.raises(GigFormatError):
        load_path(odd)
    with pytest.raises(GigFormatError):
        parse_markdown("no title here")


def test_normalize_tag_string_and_price_strings():
    g = normalize({"title": "t", "tags": "a, b, c", "pricing": {"basic": {"price": "$1,200", "del": "5 days"}}})
    assert g["tags"] == ["a", "b", "c"]
    assert g["packages"]["basic"]["price"] == 1200.0
    assert g["packages"]["basic"]["days"] == 5


# ---------- audit ----------
def test_strong_gig_scores_high():
    r = audit(load_path(EX / "strong-gig.json")[0])
    assert r["score"] >= 95
    assert r["grade"] == "A"
    assert r["fixes"] == []


def test_weak_gig_scores_low_with_specific_fixes():
    r = audit(load_path(EX / "needs-work-gig.md")[0])
    assert r["score"] < 55
    assert r["grade"] == "F"
    text = " ".join(r["fixes"])
    assert "101 characters" in text
    assert "WhatsApp" in text
    assert "Prices must rise" in text


def test_middle_gig_in_between():
    r = audit(load_path(EX / "decent-gig.json")[0])
    assert 70 <= r["score"] <= 90
    assert any("6" in f and "tags" in f for f in r["fixes"])


def test_score_ordering():
    s = [audit(load_path(EX / n)[0])["score"] for n in ("strong-gig.json", "decent-gig.json", "needs-work-gig.md")]
    assert s[0] > s[1] > s[2]


def test_title_must_start_with_i_will():
    r = audit(gig(title="Build n8n automations for you"))
    assert any("I will" in f for f in r["fixes"])


def test_title_over_80_flagged():
    r = audit(gig(title="I will " + "x" * 80))
    assert any("limit is 80" in f for f in r["fixes"])


def test_title_over_card_safe_gets_note():
    t = "I will build n8n automations that connect all of your business tools together"
    assert 50 < len(t) <= 80
    r = audit(gig(title=t))
    assert any("safe on the gig card" in f for f in r["fixes"])


def test_too_many_and_too_long_tags():
    r = audit(gig(tags=["a b", "c d", "e f", "g h", "i j", "a very long tag over twenty"]))
    joined = " ".join(r["fixes"])
    assert "allows 5 tags" in joined
    assert "over 20 characters" in joined


def test_duplicate_tags_flagged():
    r = audit(gig(tags=["n8n automation", "N8N automation", "workflow tool", "api integration", "n8n expert"]))
    assert any("duplicate" in f.lower() for f in r["fixes"])


def test_description_over_limit():
    r = audit(gig(description="word " * 300))
    assert any("limit is 1200" in f for f in r["fixes"])


def test_description_off_platform_words_flagged():
    r = audit(gig(description=gig()["description"] + "\nEmail me or WhatsApp."))
    assert any("off-platform" in f for f in r["fixes"])


def test_missing_tier_flagged():
    g = gig()
    del g["packages"]["premium"]
    r = audit(g)
    assert any("missing: premium" in f for f in r["fixes"])


def test_non_ascending_price_flagged():
    g = gig()
    g["packages"]["standard"]["price"] = 50.0
    assert any("Prices must rise" in f for f in audit(g)["fixes"])


def test_image_out_of_range_and_wrong_size():
    r = audit(gig(images=[{"type": "image", "width": 300, "height": 200}]))
    assert any("outside" in f for f in r["fixes"])
    r = audit(gig(images=[{"type": "image", "width": 1000, "height": 600}]))
    assert any("recommends 1280x769" in f for f in r["fixes"])


def test_images_not_scored_when_absent():
    r = audit(gig(images=None))
    cat = next(c for c in r["categories"] if c["name"] == "images")
    assert cat["scored"] is False
    assert r["score"] >= 95


def test_empty_gig_scores_zero_ish():
    r = audit(normalize({"title": ""}))
    assert r["score"] <= 10


def test_too_many_gallery_images():
    r = audit(gig(images=[{"type": "image", "width": 1280, "height": 769}] * 4))
    assert any("1-3 images" in f for f in r["fixes"])


# ---------- lint ----------
def labels(text):
    return {f.label for f in lint(text)}


def test_lint_catches_core_words():
    assert "email" in labels("Send me your email")
    assert "pay/payment" in labels("I will pay later")
    assert "discord" in labels("join my Discord")
    assert "whatsapp" in labels("ping me on WhatsApp")


def test_lint_clean_message():
    assert lint("Thanks for the order! I will start on the first draft today.") == []


def test_lint_no_false_positive_on_pay_attention_or_payload():
    assert lint("I will pay attention to detail.") == []
    assert lint("The payload is JSON.") == []


def test_lint_api_calls_are_fine():
    assert lint("The workflow makes 3 API calls per run.") == []


def test_lint_urls_handles_numbers():
    ls = labels("see https://example.com or @someone or +1 (555) 123-4567")
    assert {"external URL", "@handle", "phone number"} <= ls


def test_lint_email_address_single_finding():
    fs = lint("write to jane@example.com")
    assert [f.label for f in fs] == ["email address"]


def test_lint_obfuscation_is_called_out_as_worse():
    fs = lint("you can p.a.y me directly")
    assert any(f.label == "obfuscated pay" for f in fs)
    assert "evasion" in next(f for f in fs if f.label == "obfuscated pay").suggestion


def test_lint_positions_match_text():
    text = "Join the Discord now"
    f = lint(text)[0]
    assert text[f.start : f.end] == "Discord"


def test_lint_suggestions_present():
    f = next(x for x in lint("send an email") if x.label == "email")
    assert "mailing list" in f.suggestion


# ---------- pricing ----------
def test_net_is_80_percent():
    assert pricing.net_from_gross(100) == 80.0
    assert pricing.net_from_gross(247) == 197.6


def test_gross_for_net_roundtrip():
    assert pricing.gross_for_net(1800) == 2250.0
    assert pricing.net_from_gross(pricing.gross_for_net(333.33)) == pytest.approx(333.33, abs=0.01)


def test_hourly():
    assert pricing.hourly_equivalent(150, 4) == 30.0
    with pytest.raises(ValueError):
        pricing.hourly_equivalent(150, 0)


def test_negative_rejected():
    with pytest.raises(ValueError):
        pricing.net_from_gross(-1)
    with pytest.raises(ValueError):
        pricing.gross_for_net(-5)


def test_ladder_is_strictly_increasing():
    for base in (5, 20, 47, 97, 400):
        lad = pricing.suggest_ladder(base)
        p = [lad[t]["gross"] for t in rules.PACKAGE_TIERS]
        assert p[0] < p[1] < p[2]
    assert pricing.suggest_ladder(50)["premium"]["gross"] == 250


def test_report_needs_exactly_one_input():
    with pytest.raises(ValueError):
        pricing.report()
    with pytest.raises(ValueError):
        pricing.report(gross=10, net_target=8)
    assert pricing.report(net_target=80)["gross"] == 100.0


def test_buyer_estimate_small_order_fee():
    assert pricing.buyer_total_estimate(100) == 109.0
    assert pricing.buyer_total_estimate(1000) == 1055.0


# ---------- keywords ----------
def test_tags_are_valid_length_and_unique():
    cands = keywords.suggest_tags("n8n lead automation")
    tags = [c["tag"] for c in cands]
    assert all(len(t) <= rules.TAG_MAX_LEN for t in tags)
    assert len(tags) == len(set(tags))
    assert tags[0] == "n8n lead automation"


def test_five_tags_max_five():
    five = keywords.build("shopify store setup")["five_tags"]
    assert 1 <= len(five) <= 5


def test_titles_within_limit_and_prefixed():
    for t in keywords.suggest_titles("wordpress speed optimization"):
        assert t["title"].startswith("I will ")
        assert t["length"] <= rules.TITLE_MAX


def test_empty_seed_rejected():
    with pytest.raises(ValueError):
        keywords.suggest_tags("the and for")


def test_llm_off_by_default():
    assert keywords.llm_enabled({}) is False
    with pytest.raises(RuntimeError):
        keywords.llm_suggest("x", env={})


def test_llm_path_filters_output():
    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            body = {"choices": [{"message": {"content": '["n8n expert", "this tag is far too long to be valid", "N8N Expert"]'}}]}
            return json.dumps(body).encode()

    env = {"FIVERR_GIG_LLM_BASE_URL": "https://example.invalid/v1", "FIVERR_GIG_LLM_API_KEY": "k", "FIVERR_GIG_LLM_MODEL": "m"}
    out = keywords.llm_suggest("n8n", env=env, opener=lambda req, timeout: Resp())
    assert out == ["n8n expert"]


# ---------- CLI ----------
def test_cli_audit_exit_codes(capsys):
    assert main(["audit", str(EX / "strong-gig.json"), "--min-score", "90"]) == 0
    assert main(["audit", str(EX / "needs-work-gig.md"), "--min-score", "90"]) == 1
    out = capsys.readouterr().out
    assert "SCORE:" in out


def test_cli_audit_json(capsys):
    main(["audit", str(EX / "decent-gig.json"), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["grade"] in "ABCDF"
    assert len(data["categories"]) == 7


def test_cli_audit_missing_file(capsys):
    assert main(["audit", "nope.json"]) == 2


def test_cli_lint_exit_code(capsys):
    assert main(["lint", "--text", "email me"]) == 1
    assert main(["lint", "--text", "Thanks, starting now."]) == 0


def test_cli_price(capsys):
    assert main(["price", "--gross", "100", "--hours", "2"]) == 0
    out = capsys.readouterr().out
    assert "$80.00" in out and "$40.00" in out


def test_cli_keywords_json(capsys):
    assert main(["keywords", "logo design", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["source"] == "offline"


def test_version_string():
    assert __version__ == "2.0.0"
