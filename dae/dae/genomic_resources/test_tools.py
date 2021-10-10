from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo


def build_a_test_resource(content: str):
    return GenomicResourceEmbededRepo("", content).get_resource("")


def convert_to_tab_separated(s: str):
    return "\n".join("\t".join(line.strip("\n\r").split())
                     for line in s.split("\n")
                     if line.strip("\r\n") != "")
