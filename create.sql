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
  author_id integer not null,
  parent_id integer,
  offset integer not null,
  deleted integer not null default 0,
  rating real not null default 0,

  created datetime not null,
  last_modified datetime not null,
  caption VARCHAR(500),
  summary text,
  tags VARCHAR(500),
  message_text text not null
);

drop table if exists LinksToUsers;
create table LinksToUsers (
  id_from integer not null,
  id_to integer not null,
  primary key (id_from, id_to)
);

drop table if exists LinksToMessages;
create table LinksToMessages (
  id_from integer,
  id_to integer,
  primary key (id_from, id_to)
);

drop table if exists Votes;
create table Votes (
  voter_id integer,
  message_id integer,
  sign integer not null,
  primary key (voter_id, message_id)
);

drop table if exists Tags;
create table Tags (
  id integer primary key,
  name varchar(20) not null unique
);

drop table if exists MessageTags;
create table MessageTags (
  message_id integer,
  tag_id integer,
  primary key (message_id, tag_id)
);