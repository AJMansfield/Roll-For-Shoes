DROP TABLE IF EXISTS chars CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS rolls CASCADE;

CREATE TABLE chars (
	char_id serial PRIMARY KEY,
	char_name varchar(255) NOT null,
	char_slug varchar(255) NOT null UNIQUE,
	xp integer NOT null DEFAULT 0,
	levelup_level integer DEFAULT null,
	levelup_xp integer DEFAULT null,
	created timestamp NOT null DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE players (
	player_id bigint PRIMARY KEY,
	player_name varchar(255),
	char_id integer REFERENCES chars,
	created timestamp NOT null DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE skills (
	skill_id serial PRIMARY KEY,
	skill_name varchar(255) NOT null DEFAULT 'do anything',
	skill_slug varchar(255) NOT null DEFAULT 'do-anything',
	skill_level integer DEFAULT 1,
	char_id integer REFERENCES chars,
	created timestamp NOT null DEFAULT CURRENT_TIMESTAMP
);
-- CREATE TABLE rolls (
-- 	roll_token char PRIMARY KEY,
-- 	skill_id integer REFERENCES skills,
-- 	roll_comment text,
-- 	created timestamp NOT null DEFAULT CURRENT_TIMESTAMP
-- );

INSERT INTO chars (char_name, char_slug)
VALUES
	('Muuug', 'muuug'),
	('Dorg Dorg', 'dorg-dorg');
	
INSERT INTO skills (char_id)
SELECT char_id FROM chars;

INSERT INTO players (player_id, player_name, char_id)
VALUES
	(341044668269854740, '@AJMansfield#5742', 1),
	(341044668269854741, '@AJMansfield#5742', 2);
