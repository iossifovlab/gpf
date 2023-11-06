# # pylint: disable=W0621,C0114,C0116,W0212,W0613

# import textwrap
# from typing import Callable, ContextManager, cast

# import pytest
# from oauth2_provider.models import get_application_model
# from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Group

# from remote.rest_api_client import RESTClient
# from users_api.models import WdaeUser
# from gpf_instance.gpf_instance import WGPFInstance

# from wdae_tests.integration.testing import setup_wgpf_instance, LiveServer

# from dae.testing import setup_directories, setup_genome, \
#     setup_empty_gene_models, setup_pedigree, setup_vcf
# from dae.genomic_resources.repository_factory import \
#     build_genomic_resource_repository

# pytestmark = pytest.mark.skip


# @pytest.fixture
# def wgpf_fixture(tmp_path_factory: pytest.TempPathFactory) -> WGPFInstance:
#     root_path = tmp_path_factory.mktemp("wgpf_instance")

#     setup_directories(root_path / "gpf_instance", {
#         "gpf_instance.yaml": textwrap.dedent("""
#         """),
#     })
#     setup_genome(
#         root_path / "alla_gpf" / "genome" / "allChr.fa",
#         f"""
#         >chrA
#         {100 * "A"}
#         """
#     )
#     setup_empty_gene_models(
#         root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
#     local_repo = build_genomic_resource_repository({
#         "id": "alla_local",
#         "type": "directory",
#         "directory": str(root_path / "alla_gpf")
#     })

#     setup_directories(
#       root_path / "gpf_instance" / "studies" / "test_study", {
#         "test_study.yaml": textwrap.dedent("""
#         id: test_study
#         conf_dir: .
#         has_denovo: False
#         has_cnv: False
#         genotype_storage:
#           id: internal
#           files:
#             pedigree:
#               path: test_study.ped
#             variants:
#             - path: test_study.vcf
#               format: vcf
#         """),
#     })
#     setup_pedigree(
#         root_path / "gpf_instance"
#         / "studies" / "test_study"
#         / "test_study.ped",
#         """
# familyId personId dadId momId sex status role
# f1       mom1     0     0     2   1      mom
# f1       dad1     0     0     1   1      dad
# f1       prb1     dad1  mom1  1   2      prb
# f1       sib1     dad1  mom1  2   2      sib
#         """)
#     setup_vcf(
#         root_path
#         / "gpf_instance" / "studies"
#         / "test_study" / "test_study.vcf.gz",
#         """
# ##fileformat=VCFv4.2
# ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
# ##contig=<ID=chr1>
# ##contig=<ID=chr2>
# ##contig=<ID=chr3>
# #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 prb1 sib1
# chr1   1   .  A   C   .    .      .    GT     0/1  0/0  0/1  0/0
# chr2   1   .  A   C   .    .      .    GT     0/0  0/1  0/1  0/0
# chr3   1   .  A   C   .    .      .    GT     0/0  0/1  0/0  0/1
#         """)  # noqa

#     return setup_wgpf_instance(
#         root_path / "gpf_instance",
#         reference_genome_id="genome",
#         gene_models_id="empty_gene_models",
#         grr=local_repo
#     )


# @pytest.fixture()
# def admin() -> WdaeUser:
#     user_model = get_user_model()
#     new_user = user_model.objects.create(
#         email="admin@example.com",
#         name="Admin",
#         is_staff=True,
#         is_active=True,
#         is_superuser=True,
#     )
#     new_user.set_password("secret")
#     new_user.save()

#     admin_group, _ = Group.objects.get_or_create(
#       name=WdaeUser.SUPERUSER_GROUP)
#     new_user.groups.add(admin_group)

#     return cast(WdaeUser, new_user)


# @pytest.fixture()
# def oauth_app() -> None:
#     # pylint: disable=invalid-name
#     Application = get_application_model()
#     new_application = Application(**{
#         "name": "remote federation testing app",
#         "user_id": 1,
#         "client_type": "confidential",
#         "authorization_grant_type": "client-credentials",
#         "client_id": "federation",
#         "client_secret": "secret"
#     })
#     new_application.full_clean()
#     new_application.save()


# @pytest.fixture()
# def test_oauth_credentials() -> str:
#     return "ZmVkZXJhdGlvbjpzZWNyZXQ="


# @pytest.fixture()
# def build_rest_client() -> Callable[[LiveServer, str], RESTClient]:
#     def builder(
#         server: LiveServer, credentials: str, base_url: str = "api/v3"
#     ) -> RESTClient:
#         return RESTClient(
#             "test", server.thread.host,
#             credentials,
#             base_url=base_url,
#             port=server.thread.port
#         )
#     return builder


# def test_rest_client_on_remote(
#     wdae_django_server: Callable[
#         [WGPFInstance, str], ContextManager[LiveServer]
#     ],
#     wgpf_fixture: WGPFInstance,
#     test_oauth_credentials: str,
#     build_rest_client: Callable[[LiveServer, str], RESTClient]
# ) -> None:
#     with wdae_django_server(
#         wgpf_fixture,
#         "wdae.test_settings"
#     ) as server:
#         # pylint: disable=invalid-name
#         client = build_rest_client(server, test_oauth_credentials)
#         datasets = client.get_datasets()
#         assert datasets is not None
#         assert len(datasets["data"]) == 1
#         assert datasets["data"][0]["id"] == "test_study"
