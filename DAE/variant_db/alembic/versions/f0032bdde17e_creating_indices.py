"""Creating indices

Revision ID: f0032bdde17e
Revises: b4a06157f4ef
Create Date: 2018-01-16 16:40:58.710868

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f0032bdde17e'
down_revision = 'b4a06157f4ef'
branch_labels = None
depends_on = None


def upgrade():
    op.create_primary_key('pk_gene', 'gene', ['id'])
    op.create_primary_key('pk_effect', 'effect', ['id'])
    op.create_primary_key('pk_variant', 'variant', ['id'])
    op.create_primary_key('pk_numeric_attribute', 'numeric_attribute', ['variant_id', 'name'])
    op.create_primary_key('pk_family', 'family', ['id'])
    op.create_primary_key('pk_person', 'person', ['id'])
    op.create_primary_key('pk_family_member', 'family_member', ['family_id', 'person_id'])
    op.create_primary_key('pk_family_variant', 'family_variant', ['family_id', 'variant_id'])
    op.create_primary_key('pk_person_variant', 'person_variant', ['person_id', 'variant_id'])

    op.create_index('uix_gene_symbol', 'gene', ['symbol'], unique=True)

    op.create_foreign_key('fk_effect_gene', 'effect', 'gene', ['gene_id'], ['id'])
    op.create_foreign_key('fk_effect_variant', 'effect', 'variant', ['variant_id'], ['id'])

    op.create_foreign_key('fk_variant_worst_effect', 'variant', 'effect', ['worst_effect_id'], ['id'])
    op.create_index('ix_variant_alt_freq', 'variant', ['alt_freq'], unique=False)
    op.create_index('ix_variant_n_alt_alls', 'variant', ['n_alt_alls'], unique=False)
    op.create_index('ix_variant_n_par_called', 'variant', ['n_par_called'], unique=False)
    op.create_index('ix_variant_prcnt_par_called', 'variant', ['prcnt_par_called'], unique=False)
    op.create_index('ix_variant_variant_type', 'variant', ['variant_type'], unique=False)
    op.create_index('uix_chr_loc_var', 'variant', ['chromosome', 'location', 'variant_type', 'variant'], unique=True)

    op.create_foreign_key('fk_numeric_attribute_variant', 'numeric_attribute', 'variant', ['variant_id'], ['id'])
    op.create_index('ix_name_value', 'numeric_attribute', ['name', 'value'], unique=False)

    op.create_index('uix_family_ext_id', 'family', ['family_ext_id'], unique=True)

    op.create_foreign_key('fk_family_member_family', 'family_member', 'family', ['family_id'], ['id'])
    op.create_foreign_key('fk_family_member_person', 'family_member', 'person', ['person_id'], ['id'])

    op.create_foreign_key('fk_family_variant_family', 'family_variant', 'family', ['family_id'], ['id'])
    op.create_foreign_key('fk_family_variant_variant', 'family_variant', 'variant', ['variant_id'], ['id'])

    op.create_foreign_key('fk_person_variant_person', 'person_variant', 'person', ['person_id'], ['id'])
    op.create_foreign_key('fk_person_variant_variant', 'person_variant', 'variant', ['variant_id'], ['id'])

def downgrade():
    op.drop_index('uix_gene_symbol', table_name='gene')

    op.drop_constraint('fk_effect_gene', 'effect', type_='foreignkey')
    op.drop_constraint('fk_effect_variant', 'effect', type_='foreignkey')

    op.drop_constraint('fk_variant_worst_effect', 'variant', type_='foreignkey')
    op.drop_index('ix_variant_prcnt_par_called', table_name='variant')
    op.drop_index('ix_variant_n_par_called', table_name='variant')
    op.drop_index('ix_variant_n_alt_alls', table_name='variant')
    op.drop_index('ix_variant_alt_freq', table_name='variant')
    op.drop_index('ix_variant_variant_type', table_name='variant')
    op.drop_index('uix_chr_loc_var', 'variant')

    op.drop_constraint('fk_numeric_attribute_variant', 'numeric_attribute', type_='foreignkey')
    op.drop_index('ix_name_value', table_name='numeric_attribute')

    op.drop_index('uix_family_ext_id', 'family')

    op.drop_constraint('fk_family_member_family', 'family_member', type_='foreignkey')
    op.drop_constraint('fk_family_member_person', 'family_member', type_='foreignkey')

    op.drop_constraint('fk_family_variant_family', 'family_variant', type_='foreignkey')
    op.drop_constraint('fk_family_variant_variant', 'family_variant', type_='foreignkey')

    op.drop_constraint('fk_person_variant_person', 'person_variant', type_='foreignkey')
    op.drop_constraint('fk_person_variant_variant', 'person_variant', type_='foreignkey')

    op.drop_constraint('pk_gene', 'gene', type_='primary')
    op.drop_constraint('pk_effect', 'effect', type_='primary')
    op.drop_constraint('pk_variant', 'variant', type_='primary')
    op.drop_constraint('pk_numeric_attribute', 'numeric_attribute', type_='primary')
    op.drop_constraint('pk_family', 'family', type_='primary')
    op.drop_constraint('pk_person', 'person', type_='primary')
    op.drop_constraint('pk_family_member', 'family_member', type_='primary')
    op.drop_constraint('pk_family_variant', 'family_variant', type_='primary')
    op.drop_constraint('pk_person_variant', 'person_variant', type_='primary')
