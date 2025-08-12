from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy


class BaseCommonReportsHelper(GPFTool):
    """Base class for common reports helper"""

    def __init__(self) -> None:
        super().__init__("common_reports_helper")


class CommonReportsHelper(BaseCommonReportsHelper):
    """Build enrichment tool test."""

    def __init__(
        self,
        study: WDAEStudy,
    ) -> None:
        super().__init__()
        self.study = study

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        raise NotImplementedError
