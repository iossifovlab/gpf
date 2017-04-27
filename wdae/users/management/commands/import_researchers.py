import csv

from django.core.management.base import BaseCommand, CommandError

from users.models import WdaeUser, ResearcherId
from django.contrib.auth.models import BaseUserManager, Group


class Command(BaseCommand):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv. ' \
        'Required column names for the csv file - LastName, Email and Id.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--additional-group', '-g',
            action='append',
            dest='groups',
            default=[],
            help='Add users to this group(s) in addition to the ones \
                  in the file. Can be specified multiple times\
                  e.g. -g GROUP1 -g GROUP2',
        )

        parser.add_argument(
            '-r',
            action='store_true',
            dest='replace',
            help='Replace all groups and researcher ids for users in the file',
        )

    def handle_researcher(self, res, additional_groups, replace):
        email = BaseUserManager.normalize_email(res['Email'])

        user, created = WdaeUser.objects.get_or_create(email=email,
            defaults = {'last_name': res['LastName']})

        if created:
            print("created researcher:{}".format(res))
        else:
            print("Updating researcher:{}".format(res))

        if replace:
            user.groups.clear()
        groups = additional_groups + res['Groups'].split(':')
        for group_name in set(groups):
            if group_name == "":
                continue
            group, _ = Group.objects.get_or_create(name=group_name)
            group.user_set.add(user)

        if replace:
            user.researcherid_set.clear()
        for rid in set(res['Id'].split(':')):
            if rid == "":
                continue
            res_id, _ = ResearcherId.objects.get_or_create(researcher_id=rid)
            res_id.researcher.add(user)

        if "FirstName" in res:
            user.first_name = res["FirstName"]

        if "Superuser" in res:
            user.is_superuser = res["Superuser"] == 'True'

        if "Staff" in res:
            user.is_staff = res["Staff"] == 'True'

        if "Active" in res:
            user.is_active = res["Active"] == 'True'

        if "Password" in res:
            user.password = res["Password"]

        user.save()

    def handle(self, *args, **options):
        if(len(args) < 1):
            raise CommandError('At least one argument is required')

        print(args, options)
        for csv_file in args:
            try:
                with open(csv_file, 'rb') as csvfile:
                    resreader = csv.DictReader(csvfile)

                    for res in resreader:
                        self.handle_researcher(res, options['groups'],
                                               options['replace'])

            except csv.Error:
                raise CommandError(
                    'There was a problem while reading "%s"' % csv_file)
            except IOError:
                raise CommandError('File "%s" not found' % csv_file)
