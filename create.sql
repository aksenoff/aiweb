drop table if exists Users;
create table Users (
  id integer primary key,
  rating real not null,
  disabled integer not null,

  login VARCHAR(16) not null unique,
  password VARCHAR(16) not null,
  email VARCHAR(50),
  reg_date datetime not null
);

drop table if exists Messages;
create table Messages (
  id integer primary key,
  rating real not null,
  author_id integer not null,
  parent_id integer not null,
  deleted integer not null,

  created datetime not null,
  last_modified datetime not null,
  caption VARCHAR(50),
  message_text text not null
);

drop table if exists Links_to_users;
create table Links_to_users (
  id_from integer not null,
  id_to integer not null,
  primary key (id_from, id_to)
);

drop table if exists Links_to_messages;
create table Links_to_messages (
  id_from integer not null,
  id_to integer not null,
  primary key (id_from, id_to)
);

drop table if exists Votes;
create table Votes (
  voter_id integer not null,
  message_id integer not null,
  sign integer not null
);
