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
    grade numeric NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES student (student_id),
    FOREIGN KEY (course_id) REFERENCES course (course_id)
);

CREATE TABLE IF NOT EXISTS prereq (
    course_id varchar(20) NOT NULL,
    prereq_id varchar(20) NOT NULL,
    PRIMARY KEY (course_id, prereq_id),
    FOREIGN KEY (course_id) REFERENCES course (course_id),
    FOREIGN KEY (prereq_id) REFERENCES course (course_id)
);


-- Foreign key indexes, so joins can start from either side like Neo4j relationships
CREATE INDEX IF NOT EXISTS takes_course_id_idx ON takes (course_id);
CREATE INDEX IF NOT EXISTS prereq_prereq_id_idx ON prereq (prereq_id);
