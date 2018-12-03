from preloaded.register import Preload
from common_reports.common_report_facade import CommonReportFacade


class CommonReportsPreload(Preload):
    def __init__(self):
        super(CommonReportsPreload, self).__init__()
        self.common_report_facade = CommonReportFacade()

    def serialize(self):
        return {}

    def deserialize(self, data):
        self.load()
        return {}

    def is_loaded(self):
        return True

    def get(self):
        return self

    def get_facade(self):
        return self.common_report_facade
