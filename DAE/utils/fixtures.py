import os

_DAE_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', '..'
    )
)


def path_to_fixtures(module, *args, **kwargs):
    package = kwargs.pop('package', 'DAE')
    paths = [_DAE_ROOT, package, module, 'tests', 'fixtures'] + list(args)
    return os.path.join(*paths)
