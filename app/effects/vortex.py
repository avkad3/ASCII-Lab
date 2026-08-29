"""Vortex effect — characters rotate around cursor."""
import math
from typing import List
from .base import Effect, InteractionState


class VortexEffect(Effect):
    """Characters rotate around the mouse position."""

    def __init__(self, strength: float = 0.5):
        self.strength = strength

    def apply(self, frame: List[str], state: InteractionState) -> List[str]:
        if not frame:
            return frame
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        if width == 0:
            return frame

        result = []
        for y, row in enumerate(frame):
            new_row = []
            for x, char in enumerate(row):
                dx = x - state.x
                dy = y - state.y
                dist = math.sqrt(dx*dx + dy*dy) + 1
                
                # Rotation angle
                angle = self.strength / dist
                
                # Rotate around mouse
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                src_x = state.x + (dx * cos_a - dy * sin_a)
                src_y = state.y + (dx * sin_a + dy * cos_a)
                
                src_x = int(src_x)
                src_y = int(src_y)
                src_x = max(0, min(width - 1, src_x))
                src_y = max(0, min(height - 1, src_y))
                
                new_row.append(frame[src_y][src_x])
            result.append("".join(new_row))
        
        return result