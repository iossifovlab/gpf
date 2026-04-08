import abc

from gain.effect_annotation.annotation_request import AnnotationRequest
from gain.effect_annotation.effect import AnnotationEffect


class EffectChecker(abc.ABC):

    @abc.abstractmethod
    def get_effect(
        self, request: AnnotationRequest,
    ) -> AnnotationEffect | None:
        """Return an annotation effect or None."""
