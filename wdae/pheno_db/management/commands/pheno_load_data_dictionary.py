'''
Created on Aug 12, 2016

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from pheno_db.utils.load_raw import V14Loader
from pheno_db.models import VariableDescriptor
from pheno_db.utils.variables import set_variable_descriptor_from_main_row,\
    set_variable_descriptor_from_ssc_row


class Command(BaseCommand):
    help = '''Loads Main Data Dictionary into the database'''
    BULK_SIZE = 200

    def _create_or_update_variable_descriptor(self, df, source, set_func):
        bulk = []
        for _index, row in df.iterrows():
            vd = VariableDescriptor()
            set_func(vd, row, source)
            bulk.append(vd)

            if len(bulk) >= self.BULK_SIZE:
                VariableDescriptor.objects.bulk_create(bulk)
                bulk = []

        if len(bulk) > 0:
            VariableDescriptor.objects.bulk_create(bulk)
            bulk = []

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        loader = V14Loader()

        df = loader.load_ocuv()
        self._create_or_update_variable_descriptor(
            df,
            'ocuv',
            set_variable_descriptor_from_ssc_row
        )

        df = loader.load_cdv()
        self._create_or_update_variable_descriptor(
            df,
            'cdv',
            set_variable_descriptor_from_ssc_row
        )

        df = loader.load_main()
        self._create_or_update_variable_descriptor(
            df,
            'main',
            set_variable_descriptor_from_main_row
        )
