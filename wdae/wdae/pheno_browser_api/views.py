from rest_framework.response import Response
from rest_framework import status
from django.http.response import StreamingHttpResponse

from django.http.response import HttpResponse

from query_base.query_base import QueryBaseView

from utils.streaming_response_util import iterator_to_json


class PhenoBrowserBaseView(QueryBaseView):
    def __init__(self):
        super(PhenoBrowserBaseView, self).__init__()
        self.pheno_config = self.gpf_instance.get_phenotype_db_config()

    def get_browser_dbfile(self, dataset):
        browser_dbfile = self.gpf_instance.get_pheno_dbfile(dataset)
        assert browser_dbfile is not None
        return browser_dbfile

    def get_browser_images_url(self, dataset):
        browser_images_url = self.gpf_instance.get_pheno_images_url(dataset)
        assert browser_images_url is not None
        return browser_images_url


class PhenoConfigView(PhenoBrowserBaseView):
    def __init__(self):
        super(PhenoConfigView, self).__init__()

    def get(self, request):
        if "db_name" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not self.pheno_config:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dbname = request.query_params["db_name"]

        return Response(self.pheno_config[dbname])


class PhenoInstrumentsView(QueryBaseView):
    def __init__(self):
        super(PhenoInstrumentsView, self).__init__()

    def get(self, request):
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not self.gpf_instance.has_pheno_data(dataset):
            return Response(status=status.HTTP_404_NOT_FOUND)

        instruments = sorted(self.gpf_instance.get_instruments(dataset))
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
        if dataset is None or not self.gpf_instance.has_pheno_data(dataset):
            return Response(status=status.HTTP_404_NOT_FOUND)

        res = self.gpf_instance.get_measures_info(dataset)

        return Response(res)


class PhenoMeasuresView(PhenoBrowserBaseView):
    def __init__(self):
        super(PhenoMeasuresView, self).__init__()

    def get(self, request):
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not self.gpf_instance.has_pheno_data(dataset):
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get("instrument", None)
        search_term = request.query_params.get("search", None)

        pheno_instruments = self.gpf_instance.get_instruments(dataset)

        if instrument and instrument not in pheno_instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = self.gpf_instance.search_measures(
            dataset, instrument, search_term)

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
        if dataset is None or not self.gpf_instance.has_pheno_data(dataset):
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
