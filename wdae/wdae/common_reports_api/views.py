import json
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from datasets_api.permissions import user_has_permission

from query_base.query_base import QueryBaseView

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.family_tag_builder import check_tag


class VariantReportsView(QueryBaseView):
    def get(self, request, common_report_id):
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id
        )

        if common_report is not None:
            return Response(common_report.to_dict())
        return Response(
            {"error": f"Common report {common_report_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


class VariantReportsFullView(QueryBaseView):
    def get(self, request, common_report_id):
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id
        )

        if common_report is not None:
            return Response(common_report.to_dict(full=True))
        return Response(
            {"error": "Common report {} not found".format(common_report_id)},
            status=status.HTTP_404_NOT_FOUND,
        )


class FamilyCounterListView(QueryBaseView):
    def post(self, request):
        data = request.data

        common_report_id = data["study_id"]
        group_name = data["group_name"]
        counter_id = int(data["counter_id"])

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
    def post(self, request):
        data = json.loads(request.data["queryData"])

        study_id = data["study_id"]
        group_name = data["group_name"]
        counter_id = int(data["counter_id"])

        assert study_id is not None

        common_report = self.gpf_instance.get_common_report(
            study_id
        )

        if common_report is None:
            return Response(
                {"error": f"Common report for {study_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        group = common_report.families_report.families_counters[group_name]

        counter_families = group.counters[counter_id].families

        study_families = self.gpf_instance.get_genotype_data(study_id).families

        counter_families_data = FamiliesData.from_families({
            family_id: study_families[family_id]
            for family_id in counter_families
        })

        ped_df = counter_families_data.ped_df

        response = StreamingHttpResponse(
            ped_df.to_csv(index=False, sep="\t"),
            content_type="text/tab-separated-values"
        )
        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response


class FamiliesDataTagDownload(QueryBaseView):
    def get(self, request):
        study_id = request.GET.get("study_id")
        tags = request.GET.get("tags")

        if study_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        study = self.gpf_instance.get_genotype_data(study_id)

        if study is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        study_families = study.families

        if tags is None or len(tags) == 0:
            result = study_families
        else:
            result = {}
            tags = set(tags.split(","))
            for family_id, family in study_families.items():
                has_tags = True
                for tag in tags:
                    try:
                        tagged = check_tag(family, tag, True)
                        if not tagged:
                            has_tags = False
                            break
                    except ValueError as err:
                        print(err)
                        return Response(status=status.HTTP_400_BAD_REQUEST)

                if has_tags:
                    result[family_id] = family

        result = FamiliesData.from_families(result)

        response = StreamingHttpResponse(
            result.ped_df.to_csv(index=False, sep="\t"),
            content_type="text/tab-separated-values"
        )
        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response


class FamiliesDataDownloadView(QueryBaseView):
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
