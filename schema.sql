DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS future_posts;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE future_posts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  body TEXT NOT NULL
);

INSERT INTO post (author_id, title, body) VALUES (1, 'Web Development', 'I really like web development. It is quite fun indeed.');
INSERT INTO future_posts(title, body) VALUES ('Wood is Cool', 'Yo I think wood is cool man.');
INSERT INTO future_posts(title, body) VALUES ('Wood is Still Cool', 'Wood is even cooler today than it was before.');