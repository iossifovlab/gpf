#!/usr/bin/env python
import random
import argparse
import sys


# pylint: disable=invalid-name
mateships_count = 20
members_per_mateship = 3


class Person:
    def __init__(self, _id, sex, mom=None, dad=None, status=None):
        self.sex = sex
        self.mom = mom
        self.dad = dad
        if status is None:
            status = "2" if random.randint(0, 5) == 1 else "1"
        self.status = status
        self.id = _id


class Mateship:
    def __init__(self, mom, dad):
        self.mom = mom
        self.dad = dad
        self.id = "{}_{}".format(mom.id, dad.id)
        self.children = []

    def add_child(self, person):
        assert not person.mom
        assert not person.dad

        person.mom = self.mom
        person.dad = self.dad

        self.children.append(person)


class Family:
    def __init__(self, members=None, mateships=None):
        self.members = members
        self.mateships = mateships


class FamilyGenerator:
    def generate(self, mateships_count, children_per_mateship):
        members = {}
        mateships = {}

        def next_person_id():
            next_person_id.people_counter += 1
            return "P{}".format(next_person_id.people_counter)

        next_person_id.people_counter = 0

        for _ in range(mateships_count):
            mom = Person(next_person_id(), "F")
            dad = Person(next_person_id(), "M")

            members[mom.id] = mom
            members[dad.id] = dad

            mateship = Mateship(mom, dad)
            mateships[mateship.id] = mateship

        mateships_list = list(mateships.values())

        for i, mateship in enumerate(mateships_list):
            if i == 0:
                continue

            to_connect_mateship = mateships_list[random.randint(0, i - 1)]
            to_connect_member = random.choice([mateship.mom, mateship.dad])
            to_connect_mateship.add_child(to_connect_member)

        for mateship in mateships_list:
            while len(mateship.children) < children_per_mateship:
                person = Person(next_person_id(), random.choice(["M", "F"]))
                members[person.id] = person
                mateship.add_child(person)

        return Family(members, mateships)


class DeepFamilyGenerator:
    def generate(self, depth, children_per_mateship):
        members = {}
        mateships = {}

        def next_person_id():
            next_person_id.people_counter += 1
            return "P{}".format(next_person_id.people_counter)

        next_person_id.people_counter = 0

        for _ in range(depth):
            mom = Person(next_person_id(), "F")
            dad = Person(next_person_id(), "M")

            members[mom.id] = mom
            members[dad.id] = dad

            mateship = Mateship(mom, dad)
            mateships[mateship.id] = mateship

        mateships_list = list(mateships.values())

        for index, mateship in enumerate(mateships_list):
            if index == 0:
                continue
            prev_mateship = mateships_list[index - 1]

            member = random.choice([mateship.mom, mateship.dad])
            prev_mateship.add_child(member)

        for mateship in mateships_list:
            while len(mateship.children) < children_per_mateship:
                person = Person(next_person_id(), random.choice(["M", "F"]))
                members[person.id] = person
                mateship.add_child(person)

        return Family(members, mateships)


def save_family(family, filename=None):
    if not filename:
        filename = "pedigree-{}-{}.ped".format(
            len(family.mateships), len(family.members)
        )
    sys.stderr.write("Generated file " + str(filename) + "\n")

    with open(filename, "w") as f:
        f.write("familyId\tpersonId\tdadId\tmomId\tsex\tstatus\n")
        for person in family.members.values():
            f.write(
                "\t".join(
                    [
                        "family1",
                        person.id,
                        person.dad.id if person.dad else "",
                        person.mom.id if person.mom else "",
                        "1" if person.sex == "M" else "2",
                        person.status if person.status else "",
                    ]
                )
                + "\n"
            )


def main():
    """Entry-point for the script."""
    desc = "Program to generate family pedigree file."
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mateships",
        type=int,
        action="store",
        default=30,
        help="amount of mateships to generate",
    )
    parser.add_argument(
        "--children",
        type=int,
        action="store",
        default=5,
        help="amount of children per mateship",
    )
    parser.add_argument(
        "--deep", action="store_true", help="generate deep family trees"
    )
    parser.add_argument(
        "--output",
        action="store",
        default=None,
        help="custom generated output filename",
    )
    opts = parser.parse_args()

    if opts.deep:
        fg = DeepFamilyGenerator()
    else:
        fg = FamilyGenerator()
    family = fg.generate(opts.mateships, opts.children)
    save_family(family, opts.output)


if __name__ == "__main__":
    main()
