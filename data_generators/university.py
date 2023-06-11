from faker import Faker
from random import sample
import csv
from pathlib import Path


# Global Variables
fake = Faker()

# Parameters
CSV_DESTINATION_PATH = Path(".").parent.absolute().joinpath("data/university")
STUDENT_COUNT = 100000
PREREQ_COUNT = 200000
RECURSION_DEPTH = 100
COURSE_PER_STUDENT = 3

assert (RECURSION_DEPTH >= 1)

# Fields shared accros tables
student_ids = [fake.unique.random_int(min=19000000, max=19200000) for _ in range(STUDENT_COUNT)]
course_ids = []
class_codes = set()


def generate_prereq():
    with open(CSV_DESTINATION_PATH.joinpath("prereq.csv"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        field_names = ['course_id', 'prereq_id']
        writer.writerow(field_names)
        for _ in range(PREREQ_COUNT // RECURSION_DEPTH):
            class_code = fake.random_uppercase_letter() + fake.random_uppercase_letter() + fake.random_uppercase_letter()
            while class_code in class_codes:
                class_code = fake.random_uppercase_letter() + fake.random_uppercase_letter() + fake.random_uppercase_letter()

            class_codes.add(class_code)

            course_ids.append(class_code + "-" + str(100))
            for j in range(101, 101 + RECURSION_DEPTH):
                course_id = class_code + "-" + str(j)
                prereq_id = class_code + "-" + str(j - 1)

                writer.writerow([course_id, prereq_id])
                course_ids.append(course_id)


def generate_course():
    with open(CSV_DESTINATION_PATH.joinpath("course.csv"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        field_names = ['course_id', 'title']
        writer.writerow(field_names)
        for course_id in course_ids:
            writer.writerow([course_id, fake.bs()])


def generate_student():
    with open(CSV_DESTINATION_PATH.joinpath("student.csv"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        field_names = ['student_id', 'name']
        writer.writerow(field_names)
        for student_id in student_ids:
            writer.writerow([student_id, fake.name()])


def generate_takes():
    with open(CSV_DESTINATION_PATH.joinpath("takes.csv"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        field_names = ['student_id', 'course_id', 'year', 'semester', 'grade']
        writer.writerow(field_names)
        for student_id in student_ids:
            takes_courses = sample(course_ids, k=COURSE_PER_STUDENT)
            writer.writerows([(student_id, course_id, sample(range(2010, 2020), k=1)[0],
                               sample(["fall", "spring"], k=1)[0],
                               round(fake.pyfloat(min_value=2.0, max_value=4.0), 2)) for course_id in takes_courses])


if __name__ == "__main__":
    generate_prereq()
    generate_course()
    generate_student()
    generate_takes()
