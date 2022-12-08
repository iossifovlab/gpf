import os

_DAE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)


def path_to_fixtures(module, *args, **kwargs):
    package = kwargs.pop("package", "dae")
    paths = [_DAE_ROOT, package, module, "tests", "fixtures"] + list(args)
    return os.path.join(*paths)


def change_environment(env_props):
    """Change os.environ variables according to given dictionary.

    Can be used with try/finally to restore the previous environment
    afterwards in the `finally` block.
    """
    env_props_copy = env_props.copy()
    old_env = {}
    for env_key, env_value in env_props_copy.items():
        old_env[env_key] = os.getenv(env_key, None)

        os.environ[env_key] = env_value

    yield

    for env_key, env_value in env_props_copy.items():
        if old_env[env_key] is None:
            os.unsetenv(env_key)
        else:
            os.environ[env_key] = old_env[env_key]
