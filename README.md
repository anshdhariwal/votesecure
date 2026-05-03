# votesecure 🗳️

> **working implementation.** a fully-featured election lifecycle platform with secure dashboards, voter registration, and eci-grade audit reports. 

India votes. Democracy secured. **votesecure** is a dead-simple, high-end platform for managing the entire election lifecycle — from registration to the final tally.

---

**developer:** [@anshdhariwal](https://github.com/anshdhariwal)
**vibe:** v1.0.0-stable-demo

---

## why?
elections are hard. manual counting is slower than a weekend in bangalore traffic. we fixed it.
- **unhackable (mostly):** encrypted ballots, immutable logs.
- **smart logic:** winners are crowned only when the dust settles.
- **no duplicates:** one vote, one citizen. we checked.

## quick start
get it running before your tea gets cold.

1. **deps:** `pip install -r requirements.txt`
2. **test data:** `python testdata.py` (creates the 'National General Elections 2025')
3. **default login:** `ansh@vote.com` // `ansh`
4. **run:** `python manage.py runserver`

## who can do what?
- **admin:** create elections, manage candidates, and hit the 'conclude' button when it's over. generate pdfs when you're done.
- **voter:** register (18+ only), read manifestos, and cast your vote. get a dashboard that tells you when the results are in.

## board features
- **🏆 crowns:** automatic winner determination. no manual math.
- **📜 modals:** consistent bio/manifesto views for every candidate.
- **🔒 lock-in:** irreversible voting. no take-backs.
- **📊 live stats:** turnout % and real-time tallies for concluded races.
- **🎨 aesthetic:** material dark theme with glassmorphism.
- **📄 pdfs:** secure reports generated only when the race is done.

## the tech
- **backend:** django (the reliable choice)
- **frontend:** tailwind + vanilla js (keep it light)
- **database:** sqlite (simple for now)
- **reports:** xhtml2pdf

---
developed with precision for a secure democracy.
