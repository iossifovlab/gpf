from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.parquet.schema2.loader import ParquetLoader as Schema2Loader
from dae.utils.regions import Region
from dae.variants_loaders.raw.loader import (
    CLIArgument,
    FullVariantsIterator,
    VariantsGenotypesLoader,
)


class ParquetLoader(VariantsGenotypesLoader):
    """Loader for Schema2 Parquet data."""

    def __init__(
        self,
        data_path: str,
        genome: ReferenceGenome,
        regions: list[Region] | None = None,
    ):
        self._subloader = Schema2Loader.load_from_dir(data_path)

        all_paths = []
        if regions is None:
            for paths in self._subloader.get_summary_pq_filepaths():
                all_paths.extend(paths)
        else:
            for region in regions:
                for paths in self._subloader.get_summary_pq_filepaths(region):
                    all_paths.extend(paths)

        super().__init__(
            self._subloader.families,
            all_paths,
            genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=True,
        )

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "path",
            value_type=str,
            metavar="<Parquet data path>",
            help_text="The path to the parquet study to import",
        ))
        return arguments

    def close(self) -> None:
        pass

    @property
    def chromosomes(self) -> list[str]:
        return list(self._subloader.contigs)

    def _full_variants_iterator_impl(self) -> FullVariantsIterator:
        for region in self.regions:
            yield from self._subloader.fetch_variants(region)
