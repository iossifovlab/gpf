from __future__ import annotations

import csv
import os
import select
import subprocess
from pathlib import Path
from typing import Any, TextIO

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import AnnotationConfigParser
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
)
from dae.annotation.annotator_base import AnnotatorBase

# ruff: noqa: S607


class DemoAnnotatorAdapter(AnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
    ):
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                "annotatable_length",
            ])
        super().__init__(
            pipeline, info, {
                "annotatable_length": ("int", "Positional length "
                                              "of the annotatable"),
            },
        )
        self.work_dir: Path = info.parameters.get("work_dir")

    def _do_annotate(
        self, _annotatable: Annotatable | None,
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "External annotator supports only batch mode",
        )

    def annotate(
        self, _annotatable: Annotatable | None,
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "External annotator supports only batch mode",
        )

    def prepare_input(
        self, file: TextIO, annotatables: list[Annotatable | None],
    ) -> None:
        writer = csv.writer(file, delimiter="\t")
        for annotatable in annotatables:
            writer.writerow([repr(annotatable)])
        file.flush()

    def read_output(
        self, file: TextIO, contexts: list[dict[str, Any]],
    ) -> None:
        """Read and return subprocess output contents."""
        reader = csv.reader(
            file, delimiter="\t",
        )
        for idx, row in enumerate(reader):
            contexts[idx]["annotatable_length"] = int(row[-1])

    def _do_batch_annotate(
        self, annotatables: list[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        if batch_work_dir is None:
            work_dir = self.work_dir
        else:
            work_dir = self.work_dir / batch_work_dir
        os.makedirs(work_dir, exist_ok=True)

        with (work_dir / "input.tsv").open("w+t") as input_file, \
                (work_dir / "output.tsv").open("w+t") as out_file:
            self.prepare_input(input_file, annotatables)
            subprocess.run(
                ["annotate_length", input_file.name, out_file.name],
                check=True,
            )
            out_file.flush()
            self.read_output(out_file, contexts)
        return contexts


class DemoAnnotatorStreamAdapter(DemoAnnotatorAdapter):
    """Annotation pipeline adapter for annotate_length using streams."""

    def _do_batch_annotate(
        self, annotatables: list[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        with subprocess.Popen(
            ["annotate_length"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        ) as proc:
            writer = csv.writer(proc.stdin, delimiter="\t")
            reader = csv.reader(
                proc.stdout, delimiter="\t",
            )
            poll = select.poll()
            poll.register(proc.stdin, select.POLLOUT)
            poll.register(proc.stdout, select.POLLIN | select.POLLPRI)
            annotatable_idx = 0
            read_idx = 0
            done = False

            while True:
                if done:
                    break
                fd_states = poll.poll(500)
                for _fd, state in fd_states:
                    if state & select.POLLOUT:
                        annotatable = annotatables[annotatable_idx]
                        writer.writerow([repr(annotatable)])
                        annotatable_idx += 1
                        if annotatable_idx == len(annotatables):
                            poll.unregister(proc.stdin)
                            proc.stdin.close()

                    elif state & select.POLLIN or state & select.POLLPRI:
                        row = next(reader)
                        contexts[read_idx]["annotatable_length"] = int(row[-1])
                        read_idx += 1
                        if read_idx == len(annotatables):
                            poll.unregister(proc.stdout)
                            done = True
                    elif state & select.POLLHUP:
                        for row in reader:
                            contexts[read_idx]["annotatable_length"] = \
                                int(row[-1])
                            read_idx += 1
                        poll.unregister(proc.stdout)
                        done = True
            proc.wait()

        return contexts


def build_demo_external_annotator_adapter(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return DemoAnnotatorAdapter(pipeline, info)


def build_demo_external_annotator_stream_adapter(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return DemoAnnotatorStreamAdapter(pipeline, info)
