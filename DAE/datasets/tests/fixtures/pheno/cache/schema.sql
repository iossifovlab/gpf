CREATE TABLE family (
	id INTEGER NOT NULL, 
	family_id VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_family_family_id ON family (family_id);
CREATE TABLE measure (
	id INTEGER NOT NULL, 
	measure_id VARCHAR(128) NOT NULL, 
	instrument_name VARCHAR(64) NOT NULL, 
	measure_name VARCHAR(64) NOT NULL, 
	description VARCHAR(255), 
	measure_type VARCHAR(11), 
	individuals INTEGER, 
	default_filter VARCHAR(255), 
	min_value FLOAT, 
	max_value FLOAT, 
	values_domain VARCHAR(255), 
	rank INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT measure_key UNIQUE (instrument_name, measure_name), 
	CONSTRAINT measuretype CHECK (measure_type IN ('continuous', 'ordinal', 'categorical', 'text', 'raw', 'other', 'skipped'))
);
CREATE INDEX ix_measure_instrument_name ON measure (instrument_name);
CREATE INDEX ix_measure_measure_type ON measure (measure_type);
CREATE UNIQUE INDEX ix_measure_measure_id ON measure (measure_id);
CREATE INDEX ix_measure_measure_name ON measure (measure_name);
CREATE TABLE person (
	id INTEGER NOT NULL, 
	family_id INTEGER, 
	person_id VARCHAR(16) NOT NULL, 
	role VARCHAR(21) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	gender VARCHAR(1) NOT NULL, 
	sample_id VARCHAR(16), 
	PRIMARY KEY (id), 
	CONSTRAINT person_key UNIQUE (family_id, person_id), 
	FOREIGN KEY(family_id) REFERENCES family (id), 
	CONSTRAINT role CHECK (role IN ('paternal_grandfather', 'paternal_grandmother', 'maternal_grandfather', 'maternal_grandmother', 'unknown', 'parent', 'spouse', 'mom', 'maternal_uncle', 'maternal_aunt', 'step_dad', 'maternal_cousin', 'dad', 'paternal_uncle', 'paternal_aunt', 'step_mom', 'paternal_cousin', 'prb', 'sib', 'maternal_half_sibling', 'paternal_half_sibling', 'child')), 
	CONSTRAINT status CHECK (status IN ('unaffected', 'affected')), 
	CONSTRAINT gender CHECK (gender IN ('M', 'F'))
);
CREATE INDEX ix_person_person_id ON person (person_id);
CREATE TABLE value_ordinal (
	person_id INTEGER NOT NULL, 
	measure_id INTEGER NOT NULL, 
	value FLOAT NOT NULL, 
	PRIMARY KEY (person_id, measure_id), 
	FOREIGN KEY(person_id) REFERENCES person (id), 
	FOREIGN KEY(measure_id) REFERENCES measure (id)
);
CREATE TABLE value_other (
	person_id INTEGER NOT NULL, 
	measure_id INTEGER NOT NULL, 
	value VARCHAR(127) NOT NULL, 
	PRIMARY KEY (person_id, measure_id), 
	FOREIGN KEY(person_id) REFERENCES person (id), 
	FOREIGN KEY(measure_id) REFERENCES measure (id)
);
CREATE TABLE value_categorical (
	person_id INTEGER NOT NULL, 
	measure_id INTEGER NOT NULL, 
	value VARCHAR(127) NOT NULL, 
	PRIMARY KEY (person_id, measure_id), 
	FOREIGN KEY(person_id) REFERENCES person (id), 
	FOREIGN KEY(measure_id) REFERENCES measure (id)
);
CREATE TABLE value_continuous (
	person_id INTEGER NOT NULL, 
	measure_id INTEGER NOT NULL, 
	value FLOAT NOT NULL, 
	PRIMARY KEY (person_id, measure_id), 
	FOREIGN KEY(person_id) REFERENCES person (id), 
	FOREIGN KEY(measure_id) REFERENCES measure (id)
);
