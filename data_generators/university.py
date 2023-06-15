"""Generate the "university" dataset as CSV files in data/university.

Courses form a prerequisite graph: every course above the lowest level depends on the previous
level of its own subject, plus a few random lower-level courses, some from other subjects.
Prerequisites always have a lower level than their course, so the graph has no cycles.
"""
import csv
import random
from pathlib import Path

from faker import Faker

# Fixed seed so every run generates the same data and sample queries can name fixed nodes
SEED = 42
random.seed(SEED)
Faker.seed(SEED)
fake = Faker()

# Parameters
CSV_DESTINATION_PATH = Path("data/university").absolute()
SUBJECT_COUNT = 2000
MIN_LEVEL = 100
MAX_LEVEL = 200
MAX_EXTRA_PREREQS = 2  # random prerequisites on top of the previous level of the same subject
CROSS_SUBJECT_RATE = 0.2  # chance that a random prerequisite comes from another subject
STUDENT_COUNT = 10000
MAJORS_PER_STUDENT = 2  # subjects a student follows from the lowest level upwards
MAX_MAJOR_COURSES = 50
SKIP_RATE = 0.1  # chance to skip a course of a major, leaving a prerequisite missing
ELECTIVES_PER_STUDENT = 5  # random courses from any subject

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
subjects = random.sample([a + b + c for a in LETTERS for b in LETTERS for c in LETTERS], SUBJECT_COUNT)
course_ids = [f"{subject}-{level}" for subject in subjects for level in range(MIN_LEVEL, MAX_LEVEL + 1)]
student_ids = random.sample(range(19000000, 19200000), STUDENT_COUNT)


def write_csv(file_name: str, header: list, rows):
    with open(CSV_DESTINATION_PATH.joinpath(file_name), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerows(rows)


def generate_prereq():
    def rows():
        for subject in subjects:
            for level in range(MIN_LEVEL + 1, MAX_LEVEL + 1):
                prereqs = {f"{subject}-{level - 1}"}
                for _ in range(random.randint(0, MAX_EXTRA_PREREQS)):
                    prereq_subject = random.choice(subjects) if random.random() < CROSS_SUBJECT_RATE else subject
                    prereqs.add(f"{prereq_subject}-{random.randint(MIN_LEVEL, level - 1)}")
                for prereq_id in sorted(prereqs):
                    yield f"{subject}-{level}", prereq_id

    write_csv("prereq.csv", ['course_id', 'prereq_id'], rows())


def generate_course():
    write_csv("course.csv", ['course_id', 'title'], ((course_id, fake.bs()) for course_id in course_ids))


def generate_student():
    write_csv("student.csv", ['student_id', 'name'], ((student_id, fake.name()) for student_id in student_ids))


def generate_takes():
    def rows():
        for student_id in student_ids:
            taken = set(random.sample(course_ids, ELECTIVES_PER_STUDENT))
            for subject in random.sample(subjects, MAJORS_PER_STUDENT):
                last_level = MIN_LEVEL + random.randint(5, MAX_MAJOR_COURSES) - 1
                taken.update(f"{subject}-{level}" for level in range(MIN_LEVEL, last_level + 1)
                             if random.random() >= SKIP_RATE)
            for course_id in sorted(taken):
                yield (student_id, course_id, random.randint(2010, 2019), random.choice(["fall", "spring"]),
                       round(random.uniform(2.0, 4.0), 2))

    write_csv("takes.csv", ['student_id', 'course_id', 'year', 'semester', 'grade'], rows())


if __name__ == "__main__":
    CSV_DESTINATION_PATH.mkdir(parents=True, exist_ok=True)
    generate_prereq()
    generate_course()
    generate_student()
    generate_takes()
