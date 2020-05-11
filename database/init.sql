GRANT ALL PRIVILEGES ON *.* TO 'bmc'@'localhost' IDENTIFIED BY 'student';

CREATE DATABASE IF NOT EXISTS tutorFinder;

USE tutorFinder;

CREATE TABLE IF NOT EXISTS users (
                    username varchar(20) not null,
                    password varchar(40) not null,
                    name varchar(30) not null,
                    address varchar(40) not null,
                    email_address varchar(30) not null,
                    phone_no varchar(10) not null,
                    PRIMARY KEY (username)
                  ) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS tutors (
                    tut_id varchar(50) not null,
                    username varchar(20) not null,
                    subject varchar(20) not null,
                    experience smallint not null,
                    channel enum('AtResidence', 'Online') not null,
                    price float not null,
                    timest timestamp not null,
                    PRIMARY KEY (tut_id)
                  ) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS matches (
                    tut_id varchar(50) not null,
                    student_username varchar(20) not null
                  ) ENGINE=INNODB;


DELIMITER //
CREATE PROCEDURE createUser(IN userName varchar(20), IN passwd varchar(40), IN name varchar(30),
                            IN address varchar(40), IN mail varchar(30), IN phoneNo varchar(10))
  BEGIN
    INSERT INTO users (username, password, name, address, email_address, phone_no) VALUES (userName, passwd, name, address, mail, phoneNo);
  END//


DELIMITER //
CREATE PROCEDURE searchUser(IN passwd varchar(30), IN userName varchar(20), OUT ret BOOLEAN, OUT realName varchar(30))
  BEGIN
    DECLARE entry_count smallint DEFAULT 0;
    DECLARE real_passwd varchar(30);
    SELECT COUNT(*) INTO entry_count FROM users WHERE users.username=userName;
    IF entry_count > 0 THEN
      SET ret = TRUE;
      SELECT name, password INTO realName, real_passwd from users WHERE users.username=userName;
      IF real_passwd != passwd THEN
        SET ret = FALSE;
      ELSE
        SET ret = TRUE;
      END IF;
    ELSE
      SET ret = FALSE;
    END IF;
  END//


DELIMITER //
CREATE PROCEDURE searchTutor(IN userName varchar(20), OUT ret BOOLEAN, OUT tutId varchar(50))
  BEGIN
    DECLARE entry_count smallint DEFAULT 0;
    SELECT COUNT(*) INTO entry_count FROM tutors t WHERE t.username=userName;
    IF entry_count > 0 THEN
      SET ret = TRUE;
      SELECT t.tut_id INTO tutId from tutors t WHERE t.username=userName;
    ELSE
      SET ret = FALSE;
    END IF;
  END//



DELIMITER //
CREATE PROCEDURE createTutor(tutId varchar(50), userName varchar(20), subject varchar(20), experience smallint,
                              channel varchar(20), price float)
  BEGIN
    INSERT INTO tutors (tut_id, username, subject, experience, channel, price, timest)
      VALUES (tutId, userName, subject, experience, channel, price, CURRENT_TIMESTAMP());
  END//


DELIMITER //
CREATE PROCEDURE getMatches(IN tutId varchar(50))
  BEGIN
    SELECT u.name, u.email_address, u.phone_no FROM matches m INNER JOIN users u ON m.student_username=u.username
        WHERE m.tut_id=tutId;
  END//

DELIMITER //
CREATE PROCEDURE insertMatch(tutId varchar(50), studentUsername varchar(20))
  BEGIN
    DECLARE entry_count smallint DEFAULT 0;
    SELECT COUNT(*) INTO entry_count FROM matches m WHERE m.student_username=studentUsername;
    IF entry_count = 0 THEN
        INSERT INTO matches (tut_id, student_username) VALUES (tutId, studentUsername);
    END IF;
  END//


DELIMITER //
CREATE PROCEDURE getTutors(subject_filter BOOLEAN, town_filter BOOLEAN, maxprice_filter BOOLEAN,
                              subject_ varchar(30), town_ varchar(20), maxprice_ float)
  BEGIN
    SELECT u.name, t.subject, t.channel, t.price, t.tut_id FROM tutors t INNER JOIN users u ON t.username = u.username
      WHERE ((!subject_filter or LOWER(t.subject)=LOWER(subject_)) and (!town_filter or LOWER(u.address)=LOWER(town_)) and (!maxprice_filter or (t.price <= maxprice_)));
  END//
