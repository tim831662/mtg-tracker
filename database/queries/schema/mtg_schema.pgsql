-- Empty-database initializer. Prefer Alembic for application databases.
-- Adopted from origin/schema (b844754), corrected and extended for the existing app.
-- Frozen schema for migration 002; do not edit after applying this revision.

CREATE TABLE artist (
	pk_artist UUID DEFAULT gen_random_uuid() NOT NULL,
	artist VARCHAR(16) NOT NULL,
	CONSTRAINT pk_artist PRIMARY KEY (pk_artist)
);

CREATE INDEX idx_artist__name ON artist (upper(artist));

CREATE TABLE format (
	pk_format UUID DEFAULT gen_random_uuid() NOT NULL,
	name_format VARCHAR(16) NOT NULL,
	minsz SMALLINT DEFAULT '60' NOT NULL,
	copylimit SMALLINT DEFAULT '4' NOT NULL,
	CONSTRAINT pk_format PRIMARY KEY (pk_format),
	CONSTRAINT ck_format_minimum_size_positive CHECK (minsz > 0),
	CONSTRAINT ck_format_copy_limit_nonnegative CHECK (copylimit >= 0),
	CONSTRAINT uq_format_name_format UNIQUE (name_format)
);

CREATE UNIQUE INDEX idx_format__upper__name ON format (upper(name_format));

CREATE TABLE mana (
	mana SMALLINT NOT NULL,
	name VARCHAR(9) NOT NULL,
	abbr VARCHAR(1) NOT NULL,
	CONSTRAINT pk_mana PRIMARY KEY (mana),
	CONSTRAINT uq_mana_name UNIQUE (name),
	CONSTRAINT uq_mana_abbr UNIQUE (abbr)
);

CREATE TABLE player (
	pk_player UUID DEFAULT gen_random_uuid() NOT NULL,
	name_real VARCHAR(64) NOT NULL,
	username VARCHAR(32),
	source_id VARCHAR(255),
	imported_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_player PRIMARY KEY (pk_player),
	CONSTRAINT uq_player_username UNIQUE (username),
	CONSTRAINT uq_player_source_id UNIQUE (source_id)
);

CREATE UNIQUE INDEX idx_player__upper__name_real ON player (upper(name_real));

CREATE INDEX idx_player__upper__username ON player (upper(username));

CREATE TABLE rarity (
	pk_rarity SMALLINT NOT NULL,
	rarity VARCHAR(20) NOT NULL,
	CONSTRAINT pk_rarity PRIMARY KEY (pk_rarity),
	CONSTRAINT uq_rarity_rarity UNIQUE (rarity)
);

CREATE TABLE card (
	pk_card UUID DEFAULT gen_random_uuid() NOT NULL,
	title VARCHAR(255) NOT NULL,
	coloridentity SMALLINT DEFAULT '63' NOT NULL,
	power VARCHAR(16),
	toughness VARCHAR(16),
	rarity SMALLINT,
	mana_production_type SMALLINT DEFAULT '0' NOT NULL,
	mana_production_amount SMALLINT DEFAULT '0' NOT NULL,
	ispromo BOOLEAN DEFAULT false NOT NULL,
	setcode VARCHAR(8),
	description TEXT,
	mana_cost VARCHAR(100),
	type_line VARCHAR(255),
	imported_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_card PRIMARY KEY (pk_card),
	CONSTRAINT ck_card_color_identity_valid CHECK (coloridentity BETWEEN 0 AND 63),
	CONSTRAINT ck_card_mana_type_valid CHECK (mana_production_type BETWEEN 0 AND 63),
	CONSTRAINT ck_card_mana_amount_nonnegative CHECK (mana_production_amount >= 0),
	CONSTRAINT uq_card_title UNIQUE (title),
	CONSTRAINT fk_card_rarity_rarity FOREIGN KEY(rarity) REFERENCES rarity (pk_rarity)
);

CREATE INDEX idx_card__color_identity ON card (coloridentity);

CREATE INDEX idx_card__is_promo ON card (ispromo);

CREATE INDEX idx_card__mana_production_type ON card (mana_production_type);

CREATE INDEX idx_card__power ON card (power DESC);

CREATE INDEX idx_card__rarity ON card (rarity DESC);

CREATE INDEX idx_card__setcode ON card (upper(setcode));

CREATE INDEX idx_card__tough ON card (toughness DESC);

CREATE UNIQUE INDEX idx_card__upper__title ON card (upper(title));

CREATE TABLE deck (
	pk_deck UUID DEFAULT gen_random_uuid() NOT NULL,
	title VARCHAR(64) NOT NULL,
	format UUID NOT NULL,
	archetype VARCHAR(255),
	source_id VARCHAR(255),
	imported_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_deck PRIMARY KEY (pk_deck),
	CONSTRAINT fk_deck_format_format FOREIGN KEY(format) REFERENCES format (pk_format),
	CONSTRAINT uq_deck_source_id UNIQUE (source_id)
);

CREATE INDEX idx_deck__upper__name_deck ON deck (upper(title));

CREATE TABLE tournament (
	pk_tournament UUID DEFAULT gen_random_uuid() NOT NULL,
	id VARCHAR(126),
	name VARCHAR(255) NOT NULL,
	loc VARCHAR(255),
	format UUID NOT NULL,
	occurred DATE NOT NULL,
	description TEXT,
	num_rounds INTEGER DEFAULT '8' NOT NULL,
	source_url TEXT,
	imported_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_tournament PRIMARY KEY (pk_tournament),
	CONSTRAINT ck_tournament_rounds_positive CHECK (num_rounds > 0),
	CONSTRAINT uq_tournament_id UNIQUE (id),
	CONSTRAINT fk_tournament_format_format FOREIGN KEY(format) REFERENCES format (pk_format)
);

CREATE UNIQUE INDEX idx_tournament__id__upper ON tournament (upper(id));

CREATE INDEX idx_tournament__occurred ON tournament (occurred DESC);

CREATE INDEX idx_tournament__upper_loc ON tournament (upper(loc));

CREATE TABLE artist__worked_on__card (
	card UUID NOT NULL,
	artist UUID NOT NULL,
	CONSTRAINT pk_artist__worked_on__card PRIMARY KEY (card, artist),
	CONSTRAINT fk_artist__worked_on__card_card_card FOREIGN KEY(card) REFERENCES card (pk_card),
	CONSTRAINT fk_artist__worked_on__card_artist_artist FOREIGN KEY(artist) REFERENCES artist (pk_artist)
);

CREATE TABLE card_in_deck (
	deck UUID NOT NULL,
	card UUID NOT NULL,
	zone VARCHAR(20) DEFAULT 'main' NOT NULL,
	amount SMALLINT NOT NULL,
	CONSTRAINT pk_card_in_deck PRIMARY KEY (deck, card, zone),
	CONSTRAINT ck_card_in_deck_amount_positive CHECK (amount > 0),
	CONSTRAINT ck_card_in_deck_zone_valid CHECK (zone IN ('main', 'sideboard')),
	CONSTRAINT fk_card_in_deck_deck_deck FOREIGN KEY(deck) REFERENCES deck (pk_deck),
	CONSTRAINT fk_card_in_deck_card_card FOREIGN KEY(card) REFERENCES card (pk_card)
);

CREATE TABLE card_is_type (
	card UUID NOT NULL,
	type VARCHAR(20) NOT NULL,
	CONSTRAINT pk_card_is_type PRIMARY KEY (card, type),
	CONSTRAINT fk_card_is_type_card_card FOREIGN KEY(card) REFERENCES card (pk_card)
);

CREATE TABLE card_mana_cost (
	card UUID NOT NULL,
	type SMALLINT NOT NULL,
	amount SMALLINT DEFAULT '1' NOT NULL,
	CONSTRAINT pk_card_mana_cost PRIMARY KEY (card, type),
	CONSTRAINT ck_card_mana_cost_amount_positive CHECK (amount > 0),
	CONSTRAINT ck_card_mana_cost_type_valid CHECK (type > 0 AND type <= 63),
	CONSTRAINT fk_card_mana_cost_card_card FOREIGN KEY(card) REFERENCES card (pk_card)
);

CREATE TABLE formatrestriction (
	format UUID NOT NULL,
	card UUID NOT NULL,
	max SMALLINT DEFAULT '0' NOT NULL,
	CONSTRAINT pk_formatrestriction PRIMARY KEY (format, card),
	CONSTRAINT ck_formatrestriction_maximum_nonnegative CHECK (max >= 0),
	CONSTRAINT fk_formatrestriction_format_format FOREIGN KEY(format) REFERENCES format (pk_format),
	CONSTRAINT fk_formatrestriction_card_card FOREIGN KEY(card) REFERENCES card (pk_card)
);

CREATE TABLE keyword (
	card UUID NOT NULL,
	word VARCHAR(20) NOT NULL,
	CONSTRAINT pk_keyword PRIMARY KEY (card, word),
	CONSTRAINT ck_keyword_word_uppercase CHECK (word = UPPER(word)),
	CONSTRAINT fk_keyword_card_card FOREIGN KEY(card) REFERENCES card (pk_card)
);

CREATE INDEX indx_keyword__word ON keyword (word);

CREATE TABLE subtype (
	card UUID NOT NULL,
	subtype VARCHAR(20) NOT NULL,
	CONSTRAINT pk_subtype PRIMARY KEY (card, subtype),
	CONSTRAINT ck_subtype_subtype_uppercase CHECK (subtype = UPPER(subtype)),
	CONSTRAINT fk_subtype_card_card FOREIGN KEY(card) REFERENCES card (pk_card)
);

CREATE TABLE tournamententry (
	player UUID NOT NULL,
	tournament UUID NOT NULL,
	deck UUID NOT NULL,
	placement SMALLINT,
	seed INTEGER,
	CONSTRAINT pk_tournamententry PRIMARY KEY (player, tournament),
	CONSTRAINT fk_tournamententry_player_player FOREIGN KEY(player) REFERENCES player (pk_player),
	CONSTRAINT fk_tournamententry_tournament_tournament FOREIGN KEY(tournament) REFERENCES tournament (pk_tournament),
	CONSTRAINT fk_tournamententry_deck_deck FOREIGN KEY(deck) REFERENCES deck (pk_deck)
);

CREATE TABLE tournament_match (
	pk_match UUID DEFAULT gen_random_uuid() NOT NULL,
	tournament UUID NOT NULL,
	round SMALLINT NOT NULL,
	playera UUID NOT NULL,
	playerb UUID,
	wina SMALLINT DEFAULT '0' NOT NULL,
	winb SMALLINT DEFAULT '0' NOT NULL,
	draws SMALLINT DEFAULT '0' NOT NULL,
	done BOOLEAN DEFAULT false NOT NULL,
	CONSTRAINT pk_tournament_match PRIMARY KEY (pk_match),
	CONSTRAINT ck_tournament_match_results_nonnegative CHECK (wina >= 0 AND winb >= 0 AND draws >= 0),
	CONSTRAINT ck_tournament_match_player_order CHECK (playerb IS NULL OR playera > playerb),
	CONSTRAINT ck_tournament_match_bye_valid CHECK (playerb IS NOT NULL OR (winb = 0 AND draws = 0)),
	CONSTRAINT ck_tournament_match_round_positive CHECK (round > 0),
	CONSTRAINT fk_match_playera_entry FOREIGN KEY(playera, tournament) REFERENCES tournamententry (player, tournament),
	CONSTRAINT fk_match_playerb_entry FOREIGN KEY(playerb, tournament) REFERENCES tournamententry (player, tournament),
	CONSTRAINT fk_tournament_match_tournament_tournament FOREIGN KEY(tournament) REFERENCES tournament (pk_tournament),
	CONSTRAINT fk_tournament_match_playera_player FOREIGN KEY(playera) REFERENCES player (pk_player),
	CONSTRAINT fk_tournament_match_playerb_player FOREIGN KEY(playerb) REFERENCES player (pk_player)
);

INSERT INTO mana (mana, abbr, name) VALUES (1, 'W', 'White'), (2, 'U', 'Blue'), (3, 'B', 'Black'), (4, 'R', 'Red'), (5, 'G', 'Green'), (6, 'C', 'Colorless');

INSERT INTO rarity (pk_rarity, rarity) VALUES (1, 'common'), (2, 'uncommon'), (3, 'rare'), (4, 'mythic'), (5, 'special'), (6, 'bonus');
