from dae.utils.dae_utils import join_line


def test_join_line() -> None:
    assert join_line(
        ["1", "a", "3.14", ["0", "1.23", "b"], ["single"]]
    ) == "1\ta\t3.14\t0; 1.23; b\tsingle\n"
