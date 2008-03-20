create table Users (
id integer primary key,
login VARCHAR(16) not null,
password VARCHAR(16) not null,
email VARCHAR(50)
);

create table Messages (
id integer primary key,
user_id integer not null,
karma integer not null,
parent_id integer not null,
deleted integer not null,
caption VARCHAR(50),
message_text text
);

create table Links (
id integer primary key
id_from integer not null,
id_to integer not null
);

create table Votes (
id integer primary key,
voter_id integer not null,
message_id integer not null
);
