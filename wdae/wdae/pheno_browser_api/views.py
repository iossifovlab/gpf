import logging

from rest_framework.response import Response
from rest_framework import status
from django.http.response import StreamingHttpResponse

from django.http.response import HttpResponse

from query_base.query_base import QueryBaseView

from utils.streaming_response_util import iterator_to_json


logger = logging.getLogger(__name__)


class PhenoBrowserBaseView(QueryBaseView):
    def __init__(self):
        super(PhenoBrowserBaseView, self).__init__()
        self.pheno_config = self.gpf_instance.get_phenotype_db_config()


class PhenoConfigView(PhenoBrowserBaseView):
    def __init__(self):
        super(PhenoConfigView, self).__init__()

    def get(self, request):
        logger.debug(f"pheno_config: {self.pheno_config}")

        if "db_name" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        logger.debug(f"self.pheno_config: {self.pheno_config}")

        if not self.pheno_config:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dbname = request.query_params["db_name"]
        logger.debug(f"dbname: {dbname}")

        return Response(self.pheno_config[dbname])


class PhenoInstrumentsView(QueryBaseView):
    def __init__(self):
        super(PhenoInstrumentsView, self).__init__()

    def get(self, request):
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not dataset.has_pheno_data():
            return Response(status=status.HTTP_404_NOT_FOUND)

        instruments = sorted(dataset.phenotype_data.get_instruments())
        res = {
            "instruments": instruments,
            "default": instruments[0],
        }
        return Response(res)


class PhenoMeasuresInfoView(PhenoBrowserBaseView):
    def __init__(self):
        super(PhenoMeasuresInfoView, self).__init__()

    def get(self, request):
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not dataset.has_pheno_data():
            return Response(status=status.HTTP_404_NOT_FOUND)

        res = dataset.phenotype_data.get_measures_info()

        return Response(res)


class PhenoMeasureDescriptionView(PhenoBrowserBaseView):
    def get(self, request):
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not dataset.has_pheno_data():
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
    def __init__(self):
        super(PhenoMeasuresView, self).__init__()

    def get(self, request):
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not dataset.has_pheno_data():
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


class PhenoMeasuresDownload(QueryBaseView):
    def __init__(self):
        super(PhenoMeasuresDownload, self).__init__()

    def get(self, request):
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not dataset.has_pheno_data():
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get("instrument", None)
        if not instrument:
            measure_ids = list(dataset.phenotype_data.measures.keys())
            values_iterator = dataset.phenotype_data.get_values_streaming_csv(
                measure_ids)
            response = StreamingHttpResponse(
                values_iterator, content_type="text/csv")
        else:
            if instrument not in dataset.phenotype_data.instruments:
                return Response(status=status.HTTP_404_NOT_FOUND)
            df = dataset.phenotype_data.get_instrument_values_df(instrument)
            df_csv = df.to_csv(index=False, encoding="utf-8")

            response = HttpResponse(df_csv, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=instrument.csv"
        response["Expires"] = "0"
        return response
