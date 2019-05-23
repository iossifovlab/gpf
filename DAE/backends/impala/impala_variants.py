from variants.family import FamiliesBase
from impala.util import as_pandas

from variants.attributes import Role, Status, Sex


class ImpalaFamilyVariants(FamiliesBase):

    def __init__(
        self, config,
            impala_host=None, impala_port=None,
            impala_connection=None):

        super(ImpalaFamilyVariants, self).__init__()

        self.config = config.impala
        assert self.config is not None

        if impala_connection is None:
            impala_connection = self.get_connection(impala_host, impala_port)
        self.connection = impala_connection

    @staticmethod
    def import_variants(impala_connection, variants_filename):
        pass

    def _load_pedigree(self):
        with self.connection.cursor() as cursor:
            q = """
                SELECT * FROM {db}.`{pedigree}`
            """.format(db=self.config.db, pedigree=self.config.pedigree)

            cursor.execute(q)
            ped_df = as_pandas(cursor)

        ped_df = ped_df.rename(columns={
            'personId': 'person_id',
            'familyId': 'family_id',
            'momId': 'mom_id',
            'dadId': 'dad_id',
            'sampleId': 'sample_id',
            'sex': 'sex',
            'status': 'status',
            'role': 'role',
            'generated': 'generated',
            'layout': 'layout',
            'phenotype': 'phenotype',
        })
        ped_df.role = ped_df.role.apply(lambda v: Role(v))
        ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))
        ped_df.status = ped_df.status.apply(lambda v: Status(v))
        if 'layout' in ped_df:
            ped_df.layout = ped_df.layout.apply(lambda v: v.split(':')[-1])

        return ped_df
