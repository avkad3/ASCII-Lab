"""Ripple effect — wave displacement from mouse."""
import math
from typing import List
from .base import Effect, InteractionState


class RippleEffect(Effect):
    """Characters are displaced in a wave pattern from the mouse."""

    def __init__(self, amplitude: float = 2.0, frequency: float = 0.3):
        self.amplitude = amplitude
        self.frequency = frequency
        self.time = 0

    def apply(self, frame: List[str], state: InteractionState) -> List[str]:
        if not frame:
            return frame
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        if width == 0:
            return frame

        self.time += 0.1
        result = []
        
        for y, row in enumerate(frame):
            new_row = []
            for x, char in enumerate(row):
                dx = x - state.x
                dy = y - state.y
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Wave displacement
                wave = math.sin(dist * self.frequency - self.time) * self.amplitude
                
                src_x = int(x + wave)
                src_y = int(y + wave)
                src_x = max(0, min(width - 1, src_x))
                src_y = max(0, min(height - 1, src_y))
                
                new_row.append(frame[src_y][src_x])
            result.append("".join(new_row))
        
        return result

    def reset(self):
        self.time = 0