CREATE TABLE Player (
    pk_player UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL,
    username VARCHAR(32) UNIQUE
);

CREATE TABLE Deck (
    pk_deck UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64)
);

CREATE TABLE Card (
    pk_card UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE Card_In_Deck (
    deck UUID NOT NULL,
    card UUID NOT NULL,
    amount SMALLINT NOT NULL,

    CONSTRAINT pk_card_in_deck PRIMARY KEY (deck, card),

    CONSTRAINT fk_card_in_deck__deck FOREIGN KEY (deck) REFERENCES Deck(pk_deck),
    CONSTRAINT fk_card_in_deck__card FOREIGN KEY (card) REFERENCES Card(pk_card),

    CONSTRAINT chk_card_in_deck__amount CHECK (amount > 0)
);

CREATE TABLE Mana (
    mana SMALLINT PRIMARY KEY,
    name VARCHAR(9) UNIQUE NOT NULL,
    abbr CHAR(1) UNIQUE NOT NULL -- for {%c} format
);

INSERT INTO Mana (mana, abbr, name) VALUES
    (1, 'W', 'White'),
    (2, 'U', 'Blue'),
    (3, 'B', 'Black'),
    (4, 'R', 'Red'),
    (5, 'G', 'Green'),
    (6, 'C', 'Colorless')
;

CREATE TABLE Card_Mana_Cost (
    card UUID NOT NULL,
    /** bit mask for mana cost, where Mana(mana) references the bit in (type)
     * This is to accomodate when multiple options are given for how to pay.
     * Examples:
     *   654321
     * 0b010000 : {G}   this mana can only be green
     * 0b000011 : {W/U} this mana can be blue or white
     * 0b111111 : {#}   this mana can be any color
     */ 
    type SMALLINT NOT NULL DEFAULT 63, -- mana type
    amount SMALLINT NOT NULL,

    CONSTRAINT chk_card_mana_cost__amount__positive CHECK (amount > 0),
    CONSTRAINT chk_card_mana_cost__type__valid CHECK (type > 0 AND type <= 63),

    CONSTRAINT pk_card_mana_cost PRIMARY KEY (card, type),
    CONSTRAINT fk_card_mana_cost__card
        FOREIGN KEY (card) REFERENCES Card(pk_card)
);

CREATE TABLE CardType (
    pk_type SMALLINT PRIMARY KEY,
    name VARCHAR(32) UNIQUE NOT NULL
);

CREATE TABLE Card_Is_Type (
    card UUID NOT NULL,
    type SMALLINT NOT NULL,

    CONSTRAINT pk_card_is_type PRIMARY KEY (card, type),

    CONSTRAINT fk_card_is_type__card FOREIGN KEY (card) REFERENCES Card(pk_card),
    CONSTRAINT fk_card_is_type__type
        FOREIGN KEY (type) REFERENCES CardType(pk_type)
);

CREATE TABLE Format (
    pk_format UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(16) UNIQUE NOT NULL,
    minSz SMALLINT NOT NULL DEFAULT 60,
    copyLimit SMALLINT NOT NULL DEFAULT 4,
         -- 0 for unlimited

    CONSTRAINT chk_format__minSz__positive CHECK (minSz > 0),
    CONSTRAINT chk_format__copyLimit__nonnegative CHECK (copyLimit >= 0)
);

CREATE TABLE FormatRestriction (
    format UUID NOT NULL,
    card UUID NOT NULL,
    max SMALLINT NOT NULL DEFAULT 0, -- use 0 to ban {card} from {format}

    CONSTRAINT pk_format_restriction PRIMARY KEY (format, card),

    CONSTRAINT fk_format_rescriction__format
        FOREIGN KEY (format) REFERENCES Format(pk_format),
    CONSTRAINT fk_format_restriction__card
        FOREIGN KEY (card) REFERENCES Card(pk_card),

    CONSTRAINT chk_format_restriction__max__nonnegative CHECK (max >= 0)
);

CREATE TABLE Tournament (
    pk_tournament UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(126) UNIQUE,
    location VARCHAR(255),
    format UUID,
    occurred DATE,

    CONSTRAINT fk_tournament__format
        FOREIGN KEY (format) REFERENCES Format(pk_format)
);

CREATE TABLE TournamentEntry (
    player UUID NOT NULL,
    tournament UUID NOT NULL,
    deck UUID NOT NULL,
    placement SMALLINT,

    CONSTRAINT pk_tournament_entry PRIMARY KEY (player, tournament),
    
    CONSTRAINT fk_tournament_entry__player
        FOREIGN KEY (player) REFERENCES Player(pk_player),
    CONSTRAINT fk_tournament_entry__tournament
        FOREIGN KEY (tournament) REFERENCES Tournament(pk_tournament),
    CONSTRAINT fk_tournament_entry__deck
        FOREIGN KEY (deck) REFERENCES Deck(pk_deck)
);

CREATE TABLE Tournament_Match (
    pk_match UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament UUID NOT NULL,
    round SMALLINT NOT NULL,
    playerA UUID NOT NULL,
    playerB UUID, -- NULL for bye
    winA SMALLINT DEFAULT 0,
    winB SMALLINT DEFAULT 0,
    draws SMALLINT DEFAULT 0,
    done BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_tournament_match__tournament
        FOREIGN KEY (tournament) REFERENCES Tournament(pk_tournament),
    CONSTRAINT fk_tournament_match__playerA
        FOREIGN KEY (playerA) REFERENCES Player(pk_player),
    CONSTRAINT fk_tournament_match__playerB
        FOREIGN KEY (playerB) REFERENCES Player(pk_player),

    CONSTRAINT chk_tournament_match__results__nonnegative
        CHECK (winA >= 0 AND winB >= 0 AND draws >= 0),
    CONSTRAINT chk_player_order
        CHECK (playerB IS NULL OR playerA > playerB), -- (A v B) == (B v A)
    CONSTRAINT chk_bye CHECK (playerB IS NOT NULL OR (winB = 0 AND draws = 0))
);