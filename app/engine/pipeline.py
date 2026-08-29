"""Rendering pipeline abstraction for ASCII Lab."""
from abc import ABC, abstractmethod
from typing import Any, List


class ProcessingStep(ABC):
    """Base class for all processing pipeline steps."""

    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process input data and return transformed output.

        Args:
            data: Input data from previous step or initial input.

        Returns:
            Transformed data for next step.
        """
        ...


class RenderPipeline:
    """Composable pipeline of processing steps."""

    def __init__(self, steps: List[ProcessingStep] = None):
        self.steps = steps or []

    def add_step(self, step: ProcessingStep) -> "RenderPipeline":
        """Add a step to the pipeline."""
        self.steps.append(step)
        return self

    def process(self, data: Any) -> Any:
        """Run data through all pipeline steps sequentially."""
        for step in self.steps:
            data = step.process(data)
        return data