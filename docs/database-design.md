# Database design starting point

PostgreSQL is the selected DBMS in the class brief. No tables are implemented in
this skeleton. Preserve the relational emphasis when adding the first migration.

| Planned area | Entities from the brief |
| --- | --- |
| Card catalog | Card, ManaType, ManaCost, CardType, Card_Is_Type |
| Format rules | Format, Format_Restriction |
| Decklists | Deck, Card_In_Deck |
| Competition | Player, Tournament, Tournament_Entry, TournamentMatch |

Review these issues before translating the diagram into DDL:

- Card references must use the same UUID type as Card's key; several diagram
  fields appear to use SMALLINT for card references. Decide how to distinguish
  card printings from a canonical card identity before enforcing copy limits or
  uniqueness by name. Do not assume every printing has a unique card name.
- Deck-card rows need an explicit main-deck/sideboard zone and a positive quantity.
  Include the zone in the appropriate uniqueness/key design. The diagram's
  deck-card `price` label appears to represent quantity and needs clarification.
- Define the relationship between a deck and its format, which appears in the ER
  diagram but is absent from the proposed Deck table.
- Match participants should reference entries in the same tournament. Define byes,
  draws, incomplete results, and Swiss versus elimination rounds explicitly. A UUID
  ordering check alone does not establish valid participants or prevent duplicate
  matches. Prefer one coherent result representation over conflicting win flags.
- Deck size, copy limits, and legality vary by format and card. Preserve exceptions
  rather than hard-coding every deck to exactly 60/15 or four copies per card.
  Decide whether historical legality snapshots are necessary for tournament data.
- Cross-row rules such as total deck size need a suitable validation/transaction
  strategy; a simple row CHECK is insufficient. Decide which rules use constraints,
  triggers, and service validation, and when an imported deck is considered complete.
- Choose how archetypes are identified before calculating archetype matchup rates.
  Define denominators for win rates and how byes, draws, and missing matches count.
- Specify stable source identifiers, deduplication, and provenance before imports.

Keep these as design decisions for the team. No speculative fixes are baked into
an initial schema here.
