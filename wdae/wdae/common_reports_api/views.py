from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from datasets_api.permissions import user_has_permission

from query_base.query_base import QueryBaseView


class VariantReportsView(QueryBaseView):
    def __init__(self):
        super(VariantReportsView, self).__init__()

    def get(self, request, common_report_id):
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id
        )

        if common_report is not None:
            return Response(common_report.to_dict())
        return Response(
            {"error": "Common report {} not found".format(common_report_id)},
            status=status.HTTP_404_NOT_FOUND,
        )


class FamilyCounterListView(QueryBaseView):
    def __init__(self):
        super().__init__()

    def get(self, request, common_report_id, group_name, counter_id):
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id
        )

        if common_report is None:
            return Response(
                {"error": f"Common report {common_report_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        group = common_report.families_report.families_counters[group_name]

        counter = group.counters[counter_id]

        return Response(counter.families)


class FamilyCounterDownloadView(QueryBaseView):
    def __init__(self):
        super().__init__()

    def get(self, request, common_report_id, group_name, counter_id):
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id
        )

        if common_report is None:
            return Response(
                {"error": f"Common report {common_report_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        group = common_report.families_report.families_counters[group_name]

        counter = group.counters[counter_id]

        response = StreamingHttpResponse(
            ",".join(counter.families),
            content_type="text/csv"
        )
        response["Content-Disposition"] = "attachment; filename=families.csv"
        response["Expires"] = "0"

        return response


class FamiliesDataDownloadView(QueryBaseView):
    def __init__(self):
        super(FamiliesDataDownloadView, self).__init__()

    def get(self, request, dataset_id):
        if not user_has_permission(
            request.user, dataset_id
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        families_data = self.gpf_instance.get_common_report_families_data(
            dataset_id
        )
        if not families_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        response = StreamingHttpResponse(
            families_data, content_type="text/tsv"
        )

        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response
