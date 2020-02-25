import os

from collections import OrderedDict
from copy import deepcopy


class CommonReportsConfigParser:
    @classmethod
    def parse(cls, config):
        # if not config or not config.study_config or \
        #         not config.study_config.get(cls.SECTION, None):
        #     return None

        study_config = config.study_config
        config_section = deepcopy(study_config.get(cls.SECTION, None))
        config_section.people_groups_info = (
            config.people_group_config.people_group
        )

        config_section = super(CommonReportsConfigParser, cls).parse_section(
            config_section
        )
        if (
            config_section is None
            or config_section.people_groups is None
            or config_section.groups is None
        ):
            return None

        config_section.id = config.id

        config_section.draw_all_families = config_section.get(
            "draw_all_families", cls.DRAW_ALL_FAMILIES_DEFAULT
        )

        config_section.groups = OrderedDict(
            [
                (
                    group.split(":")[1].strip(),
                    group.split(":")[0].strip().split(","),
                )
                for group in config_section.groups.split("|")
            ]
        )

        config_section.effect_types = config_section.get("effect_types", [])
        config_section.effect_groups = config_section.get("effect_groups", [])

        config_file = study_config.get("config_file", "")
        assert os.path.exists(config_file)
        if config_section.get("file_path") is None:
            dirname = os.path.dirname(config_file)
            file_path = os.path.join(dirname, "common_report.json")
            config_section.file_path = file_path

        return config_section
