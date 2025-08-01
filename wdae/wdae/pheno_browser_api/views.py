import logging

from datasets_api.permissions import (
    get_instance_timestamp_etag,
    get_permissions_etag,
)
from django.http.response import HttpResponse, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from gpf_instance.gpf_instance import WGPFInstance
from query_base.query_base import DatasetAccessRightsView, QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy

from pheno_browser_api.pheno_browser_helper import (
    BasePhenoBrowserHelper,
    CountError,
    PhenoBrowserHelper,
)

logger = logging.getLogger(__name__)


class PhenoConfigView(QueryBaseView, DatasetAccessRightsView):  # unused?
    """Phenotype data configuration view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Get the phenotype data configuration."""
        if "db_name" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dbname = request.query_params["db_name"]
        logger.debug("dbname: %s", dbname)

        if dbname not in self.gpf_instance.get_phenotype_data_ids():
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self.gpf_instance.get_phenotype_data_config(dbname))


class PhenoInstrumentsView(QueryBaseView):
    """Phenotype instruments view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Get phenotype instruments."""
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        pheno_browser_helper = create_pheno_browser_helper(
            self.gpf_instance,
            dataset,
        )

        try:
            instruments = pheno_browser_helper.get_instruments()
        except ValueError:
            logger.exception("Error when getting instruments")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        res = {
            "instruments": instruments,
            "default": instruments[0],
        }
        return Response(res)


class PhenoMeasuresInfoView(QueryBaseView):
    """Phenotype measures info view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Get pheno measures info."""
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        pheno_browser_helper = create_pheno_browser_helper(
            self.gpf_instance,
            dataset,
        )

        try:
            res = pheno_browser_helper.get_measures_info()
        except ValueError:
            logger.exception("Error when getting measures info")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(res)


class PhenoMeasureDescriptionView(QueryBaseView):
    """Phenotype measures description view."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request) -> Response:
        """Get pheno measures description."""
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or not dataset.has_pheno_data:
            return Response(
                {"error": "Dataset not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        measure_id = request.query_params["measure_id"]

        if not dataset.phenotype_data.has_measure(measure_id):
            return Response(
                {"error": "Measure not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        res = dataset.phenotype_data.get_measure_description(measure_id)

        return Response(res)


class PhenoMeasuresView(QueryBaseView):
    """Phenotype measures view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Get pheno measures pages."""
        if "dataset_id" not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if (
            request.query_params.get("page") is not None
            or request.query_params.get("sort_by") is not None
            or request.query_params.get("order_by") is not None
        ):
            logger.warning(
                "Received deprecated params %s", request.query_params,
            )

        instrument = request.query_params.get("instrument", None)
        search_term = request.query_params.get("search", None)

        pheno_instruments = dataset.phenotype_data.get_instruments()

        if instrument and instrument not in pheno_instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            measures = dataset.phenotype_data.search_measures(
                instrument, search_term,
            )

            measures_page = list(measures)
        except ValueError:
            logger.exception("Error when searching measures")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if measures_page is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(measures_page)


class PhenoMeasuresDownload(QueryBaseView, DatasetAccessRightsView):
    """Phenotype measure downloads view."""


    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Return a CSV file stream for measures."""
        data = request.query_params

        if "dataset_id" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = data["dataset_id"]

        study = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if not study or not study.has_pheno_data:
            logger.info("Measures not found")
            return Response(status=status.HTTP_404_NOT_FOUND)

        pheno_browser_helper = create_pheno_browser_helper(
            self.gpf_instance,
            study,
        )

        try:
            values_iterator = pheno_browser_helper.get_measure_ids(data)
            response = StreamingHttpResponse(
                values_iterator, content_type="text/csv")
        except ValueError:
            logger.exception("Error")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            logger.info("Measures not found")
            return Response(status=status.HTTP_404_NOT_FOUND)
        except CountError:
            logger.info("Measure count is too large")
            return Response(status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        response["Content-Disposition"] = \
            "attachment; filename=measures.csv"
        response["Expires"] = "0"
        return response

    @method_decorator(etag(get_instance_timestamp_etag))
    #  pylint:disable=method-hidden
    def head(self, request: Request) -> Response:
        """Return a status code validating if measures can be downloaded."""

        data = request.query_params

        if "dataset_id" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = data["dataset_id"]

        study = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if not study or not study.has_pheno_data:
            logger.info("Measures not found")
            return Response(status=status.HTTP_404_NOT_FOUND)

        pheno_browser_helper = create_pheno_browser_helper(
            self.gpf_instance,
            study,
        )
        try:
            measure_ids_count = pheno_browser_helper.count_measure_ids(data)
        except ValueError:
            logger.exception("Error")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            logger.exception("Measures not found")
            return Response(status=status.HTTP_404_NOT_FOUND)

        if measure_ids_count > 1900:
            logger.info("Measure count is too large")
            return Response(status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        if measure_ids_count == 0:
            logger.info("Measure count zero")
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_200_OK)


class PhenoMeasuresCount(QueryBaseView, DatasetAccessRightsView):
    """Phenotype measure search count view."""

    def get_count(self, request: Request) -> int:
        """Return measure count for request."""
        data = request.query_params
        data = {k: str(v) for k, v in data.items()}

        if "dataset_id" not in data:
            raise ValueError
        dataset_id = data["dataset_id"]

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or not dataset.has_pheno_data:
            raise KeyError

        search_term = data.get("search_term", None)
        instrument = data.get("instrument", None)

        if (instrument is not None
                and instrument != ""
                and instrument not in dataset.phenotype_data.instruments):
            raise KeyError

        return dataset.phenotype_data.count_measures(
            instrument, search_term,
        )

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Return a CSV file stream for measures."""
        try:
            count = self.get_count(request)
        except ValueError:
            logger.exception("Error")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            logger.exception("Measures not found")
            return Response(status=status.HTTP_404_NOT_FOUND)
        except CountError:
            logger.exception("Measure count is too large")
            return Response(status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        return Response({"count": count})


class PhenoImagesView(QueryBaseView, DatasetAccessRightsView):
    """Remote pheno images view."""

    @method_decorator(etag(get_permissions_etag))
    def get(
        self, _request: Request, pheno_id: str, image_path: str,
    ) -> Response | HttpResponse:
        """Return raw image data from a remote GPF instance."""
        if image_path == "":
            return Response(status=status.HTTP_400_BAD_REQUEST)

        phenotype_data = self.gpf_instance.get_phenotype_data(pheno_id)

        if phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            image, mimetype = phenotype_data.get_image(image_path)
        except ValueError:
            logger.exception(
                "Could not get image %s for %s",
                image_path,
                pheno_id,
            )
            return Response(status=status.HTTP_404_NOT_FOUND)

        return HttpResponse(image, content_type=mimetype)


def create_pheno_browser_helper(
    gpf_instance: WGPFInstance, study: WDAEAbstractStudy,
) -> BasePhenoBrowserHelper:
    """Create an pheno browser helper for the given dataset."""
    for ext_name, extension in gpf_instance.extensions.items():
        pheno_browser_helper = extension.get_tool(study, "pheno_browser_helper")
        if pheno_browser_helper is not None:
            if not isinstance(pheno_browser_helper, BasePhenoBrowserHelper):
                raise ValueError(
                    f"{ext_name} returned an invalid pheno browser helper!")
            return pheno_browser_helper

    if not isinstance(study, WDAEStudy):
        raise ValueError(  # noqa: TRY004
            f"Pheno browser helper for {study.study_id} is missing!")

    return PhenoBrowserHelper(study)
