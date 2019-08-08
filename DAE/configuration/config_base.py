from box import Box


class ConfigBase(Box):

    def __init__(self, config, *args, **kwargs):
        if 'camel_killer_box' not in kwargs:
            kwargs['camel_killer_box'] = True

        super(ConfigBase, self).__init__(config, *args, **kwargs)
