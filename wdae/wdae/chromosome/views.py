from rest_framework.response import Response

from query_base.query_base import QueryBaseView


class ChromosomeView(QueryBaseView):
    def __init__(self):
        super(ChromosomeView, self).__init__()

        self.chromosomes = self.gpf_instance.get_chromosomes()

    def get(self, request):
        return Response(self.chromosomes)
