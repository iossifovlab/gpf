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

    def handle_researcher(self, res, additional_groups):
        rid = res['Id']
        email = BaseUserManager.normalize_email(res['Email'])

        user, created = WdaeUser.objects.get_or_create(email=email,
            defaults = {'last_name': res['LastName']})

        if created:
            print("created researcher:{}".format(res))
        else:
            print("Updating researcher id/groups for:{}".format(res))

        user.groups.clear()
        groups = additional_groups + res['Groups'].split(':')

        for group_name in set(groups):
            if group_name == "":
                continue
            group, _ = Group.objects.get_or_create(name=group_name)
            group.user_set.add(user)

        res_id, _ = ResearcherId.objects.get_or_create(researcher_id=rid)
        res_id.researcher.add(user)

    def handle(self, *args, **options):
        if(len(args) < 1):
            raise CommandError('At least one argument is required')

        print(args, options)
        for csv_file in args:
            try:
                with open(csv_file, 'rb') as csvfile:
                    resreader = csv.DictReader(csvfile)

                    for res in resreader:
                        self.handle_researcher(res, options['groups'])

            except csv.Error:
                raise CommandError(
                    'There was a problem while reading "%s"' % csv_file)
            except IOError:
                raise CommandError('File "%s" not found' % csv_file)
