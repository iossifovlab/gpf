# from dae.backends.vcf.loader import RawVcfLoader


# def test_rebuild(gpf_instance, default_annotation_pipeline):
#     vdb = gpf_instance.variants_db
#     for study_id in [
#             'quads_f2', 'inheritance_trio', 'quads_two_families', 
#             'quads_variant_types', 'quads_in_parent', 'quads_f1', 'quads_in_child',]:
#         study_config = vdb.get_study_config(study_id)
#         assert study_config is not None

#         fvars = RawVcfLoader.load_raw_vcf_variants_from_prefix(study_config.prefix)
#         fvars.annot_df = default_annotation_pipeline.annotate_df(
#             fvars.annot_df)
#         RawVcfLoader.save_annotation_file(
#             fvars.annot_df,
#             "{}-eff.txt".format(study_config.prefix))
