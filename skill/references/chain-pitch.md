# Chain / franchise corporate pitch

## THE CHAIN ENGINE HAD NEVER SENT A SINGLE EMAIL

Two bugs, both invisible until the cap was fixed.

**1. The cap compared two different things.**

```python
_sent_today = _count_sent_today()   # total sent by EVERY engine (92)
_cap = _chain_cap()                  # remaining chain ALLOWANCE (8)
if _sent_today >= _cap:              # 92 >= 8 -> ALWAYS true
```

The remaining allowance must be compared against the chain pitches
already sent, not against the whole day's total. The daily cap is a
separate check:

```python
_chain_left = _chain_cap()
_chain_used = _count_chain_today()
if _sent_today >= allocation()['daily'] or _chain_left <= 0:
    break
```

**2. Nothing stopped a brand being pitched twice.** The engine rebuilds
its list from scratch on every run, so the second run pitched the SAME
corporate inbox again - TITLE Boxing Club and Brooklyn Fitboxing each
received the identical pitch twice within seven minutes. A duplicate
corporate pitch reads as spam.

The tracker marker is NOT a reliable guard: `mark_sent()` only stamps
the location rows whose email ends with the brand domain, so a brand
whose corporate address differs from its location addresses (Brooklyn
Fitboxing) records NOTHING. Use a dedicated state file:

```python
CHAIN_STATE = '/home/ubuntu/chain_pitch_sent.json'
```

and check it in the build loop AND record it on every successful send.

## THE EMAIL BODY LEAKED OUR RESEARCH NOTES

The template was:

```
We work with multi-location boxing and martial arts brands, and {b['note']}
We have {b['evidence']}.
```

`evidence` is an INTERNAL field. For TITLE it read *"We have 146
franchised locations (craft.co company profile); 13 tracked locations"* -
a source citation and our internal research went straight into a customer
email. And `note` is a fragment, so the first line read as a broken
sentence.

Every brand now has a `desc` field written as a noun phrase that slots
into the sentence:

```python
return f"""{b['name']} team,

We supply multi-location boxing and martial arts brands like yours - {desc}.
```

**Never interpolate an internal research field into customer copy.**
Keep `evidence` internal; write a separate `desc` for the body.

## 'TITLE' AND 'UFC' ARE ALLOWED ALL-CAPS

The spam checker flagged them. They are the recipients' own brand names,
not shouting, so they go on the allowed list in `spam_check.py`.
