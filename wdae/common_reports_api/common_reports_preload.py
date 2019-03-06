from preloaded.register import Preload

from datasets_api.datasets_manager import get_datasets_manager


class CommonReportsPreload(Preload):
    def __init__(self):
        super(CommonReportsPreload, self).__init__()

        self.common_report_facade =\
            get_datasets_manager().get_variants_db().common_report_facade

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
