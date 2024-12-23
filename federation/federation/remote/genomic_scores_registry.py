from dae.genomic_scores.scores import GenomicScoresRegistry, ScoreDesc
from federation.remote.rest_api_client import RESTClient


class RemoteGenomicScoresRegistry(GenomicScoresRegistry):
    """Class for automatic fetching and usage of remote genomic scores."""

    def __init__(
        self, rest_clients: dict[str, RESTClient],
        local_scores_db: GenomicScoresRegistry,
    ):
        # pylint: disable=super-init-not-called
        self.remote_scores: dict[str, ScoreDesc] = {}
        self.local_db = local_scores_db
        for client in rest_clients.values():
            scores = client.get_genomic_scores()
            if scores is not None:
                for score in scores:
                    desc = score.get("description")
                    if desc is None:
                        desc = score["name"]
                    score["description"] = client.prefix_remote_name(
                        desc,
                    )

                    self.remote_scores[score["name"]] = \
                        ScoreDesc.from_json(score)

    def get_scores(self) -> list[tuple[str, ScoreDesc]]:
        result = []

        result.extend(self.local_db.get_scores())

        for score_id, score in self.remote_scores.items():
            result.append((score_id, score))

        return result

    def get_local_scores(self) -> list[tuple[str, ScoreDesc]]:
        return self.local_db.get_scores()

    def __getitem__(self, score_id: str) -> ScoreDesc:
        if score_id not in self.local_db:
            if score_id not in self.remote_scores:
                raise KeyError
            return self.remote_scores[score_id]
        return self.local_db[score_id]

    def __contains__(self, score_id: str) -> bool:
        return score_id in self.local_db or score_id in self.remote_scores

    def __len__(self) -> int:
        return len(self.scores) + len(self.local_db)
