import pytest

from core.native_intelligence.tokenizer import SahibexTokenizer


def test_default_vocab_does_not_pretend_unknown_words_are_known():
    tokenizer = SahibexTokenizer()
    encoded = tokenizer.encode("unknown-token")
    assert encoded and all(token_id == 1 for token_id in encoded)


def test_corpus_vocab_encodes_and_decodes_english_and_hindi_words():
    tokenizer = SahibexTokenizer.from_corpus([
        "SAHIBEX learns safely",
        "साहिबेक्स सुरक्षित सीखता है",
    ])

    english = tokenizer.tokenize("SAHIBEX learns safely")
    hindi = tokenizer.tokenize("साहिबेक्स सुरक्षित सीखता है")
    assert english == ["SAHIBEX", "learns", "safely"]
    assert hindi == ["साहिबेक्स", "सुरक्षित", "सीखता", "है"]
    assert 1 not in tokenizer.encode("SAHIBEX learns safely")
    assert 1 not in tokenizer.encode("साहिबेक्स सुरक्षित सीखता है")
    assert tokenizer.decode(tokenizer.encode("SAHIBEX learns safely")) == "SAHIBEX learns safely"


def test_unknown_tokens_use_unknown_id_and_invalid_ids_are_rejected():
    tokenizer = SahibexTokenizer.from_corpus(["known word"])
    assert tokenizer.encode("unknown") == [1]
    with pytest.raises(TypeError):
        tokenizer.decode("not a list")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        tokenizer.decode(["not an int"])  # type: ignore[list-item]


def test_vocab_contract_rejects_duplicates_or_missing_special_tokens():
    with pytest.raises(ValueError):
        SahibexTokenizer(("<pad>", "<unk>", "<bos>", "<eos>", "word", "word"))
    with pytest.raises(ValueError):
        SahibexTokenizer(("word", "<unk>", "<bos>", "<eos>"))
