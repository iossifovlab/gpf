import logging

import csv
from io import StringIO
from typing import Generator, Union

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.http.response import StreamingHttpResponse, HttpResponse

from query_base.query_base import QueryDatasetView
from studies.study_wrapper import RemoteStudyWrapper, StudyWrapper

from utils.streaming_response_util import iterator_to_json
from utils.query_params import parse_query_params


logger = logging.getLogger(__name__)


class PhenoBrowserBaseView(QueryDatasetView):
    def __init__(self) -> None:
        super().__init__()
        self.pheno_config = self.gpf_instance.get_phenotype_db_config()


class PhenoConfigView(PhenoBrowserBaseView):
    def get(self, request: Request) -> Response:
        logger.debug(f"pheno_config: {self.pheno_config}")

        if "db_name" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        logger.debug(f"self.pheno_config: {self.pheno_config}")

        if not self.pheno_config:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dbname = request.query_params["db_name"]
        logger.debug(f"dbname: {dbname}")

        return Response(self.pheno_config[dbname])


class PhenoInstrumentsView(QueryDatasetView):
    def get(self, request: Request) -> Response:
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instruments = sorted(dataset.phenotype_data.get_instruments())
        res = {
            "instruments": instruments,
            "default": instruments[0],
        }
        return Response(res)


class PhenoMeasuresInfoView(PhenoBrowserBaseView):
    def get(self, request: Request) -> Response:
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        res = dataset.phenotype_data.get_measures_info()

        return Response(res)


class PhenoMeasureDescriptionView(PhenoBrowserBaseView):
    def get(self, request: Request) -> Response:
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(
                {"error": "Dataset not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        measure_id = request.query_params["measure_id"]

        if not dataset.phenotype_data.has_measure(measure_id):
            return Response(
                {"error": "Measure not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        res = dataset.phenotype_data.get_measure_description(measure_id)

        return Response(res)


class PhenoMeasuresView(PhenoBrowserBaseView):
    def get(self, request: Request) -> Response:
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get("instrument", None)
        search_term = request.query_params.get("search", None)

        pheno_instruments = dataset.phenotype_data.get_instruments()

        if instrument and instrument not in pheno_instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = dataset.phenotype_data.search_measures(
            instrument, search_term
        )

        response = StreamingHttpResponse(
            iterator_to_json(data),
            status=status.HTTP_200_OK,
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        return response


class PhenoMeasuresDownload(QueryDatasetView):
    """Phenotype measure downloads view."""

    def csv_value_iterator(
        self,
        dataset: Union[RemoteStudyWrapper, StudyWrapper],
        measure_ids: list[str]
    ) -> Generator[str, None, None]:
        """Create CSV content for people measures data."""
        header = ["person_id"] + measure_ids
        buffer = StringIO()
        writer = csv.writer(buffer, delimiter=",")
        writer.writerow(header)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        assert dataset.phenotype_data is not None

        values_iterator = dataset.phenotype_data.get_people_measure_values(
            measure_ids)

        for values_dict in values_iterator:
            output = [values_dict[header[0]]]
            all_null = True
            for col in header[1:]:
                value = values_dict[col]
                if value is not None:
                    all_null = False
                output.append(value)
            if all_null:
                continue
            writer.writerow(output)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

        buffer.close()

    def post(self, request: Request) -> Response:
        """Return a CSV file stream for measures."""
        data = request.data
        if "queryData" in data:
            data = parse_query_params(data)
        if "dataset_id" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = data["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        measure_ids = data.get("measure_ids", None)
        instrument = data.get("instrument", None)
        if instrument is None:
            if measure_ids is None:
                measure_ids = list(dataset.phenotype_data.measures.keys())
        else:
            if instrument not in dataset.phenotype_data.instruments:
                return Response(status=status.HTTP_404_NOT_FOUND)

            instrument_measures = \
                dataset.phenotype_data.get_instrument_measures(instrument)
            if measure_ids is None:
                measure_ids = instrument_measures

            if not set(measure_ids).issubset(set(instrument_measures)):
                return Response(status=status.HTTP_400_BAD_REQUEST)

        if len(measure_ids) > 1900:
            measure_ids = measure_ids[0:1900]

        values_iterator = self.csv_value_iterator(
            dataset, measure_ids
        )

        response = StreamingHttpResponse(
            values_iterator, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=measures.csv"
        response["Expires"] = "0"
        return response


class PhenoMeasureValues(QueryDatasetView):
    """Phenotype measure values view."""

    def post(self, request: Request) -> Response:
        """Return measure values as stream."""
        data = request.data
        if "dataset_id" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = data["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        measure_ids = data.get("measure_ids", None)
        instrument = data.get("instrument", None)
        if instrument is None:
            if measure_ids is None:
                measure_ids = list(dataset.phenotype_data.measures.keys())
        else:
            if instrument not in dataset.phenotype_data.instruments:
                return Response(status=status.HTTP_404_NOT_FOUND)

            instrument_measures = \
                dataset.phenotype_data.get_instrument_measures(instrument)
            if measure_ids is None:
                measure_ids = instrument_measures

            if not set(measure_ids).issubset(set(instrument_measures)):
                return Response(status=status.HTTP_400_BAD_REQUEST)

        if len(measure_ids) > 1900:
            measure_ids = measure_ids[0:1900]

        values_iterator = dataset.phenotype_data.get_people_measure_values(
            measure_ids
        )

        response = StreamingHttpResponse(
            iterator_to_json(values_iterator),
            status=status.HTTP_200_OK,
            content_type="text/event-stream",
        )

        return response


class PhenoRemoteImages(QueryDatasetView):
    """Remote pheno images view."""

    def get(
        self, _request: Request, remote_id: str, image_path: str
    ) -> Union[Response, HttpResponse]:
        """Return raw image data from a remote GPF instance."""
        if image_path == "":
            return Response(status=status.HTTP_400_BAD_REQUEST)

        client = self.gpf_instance.get_remote_client(remote_id)

        if client is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        image, mimetype = client.get_pheno_image(image_path)

        return HttpResponse(image, content_type=mimetype)
