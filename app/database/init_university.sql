CREATE TABLE IF NOT EXISTS course (
    course_id varchar(20) NOT NULL,
    title varchar(50) NOT NULL,
    PRIMARY KEY (course_id)
);

CREATE TABLE IF NOT EXISTS student (
    student_id varchar(20) NOT NULL,
    name varchar(50) NOT NULL,
    PRIMARY KEY (student_id)
);

CREATE TABLE IF NOT EXISTS takes (
    student_id varchar(20) NOT NULL,
    course_id varchar(20) NOT NULL,
    year varchar(5) NOT NULL,
    semester varchar(10) NOT NULL,
    grade varchar(5) NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES student (student_id),
    FOREIGN KEY (course_id) REFERENCES course (course_id)
);

CREATE TABLE IF NOT EXISTS prereq (
    course_id varchar(20) NOT NULL,
    prereq_id varchar(20) NOT NULL,
    PRIMARY KEY (course_id, prereq_id)
);

