"""Gravity effect — characters attracted toward cursor."""
import math
from typing import List
from .base import Effect, InteractionState


class GravityEffect(Effect):
    """Characters are attracted toward the mouse position."""

    def __init__(self, strength: float = 0.3):
        self.strength = strength
        self.positions = []

    def apply(self, frame: List[str], state: InteractionState) -> List[str]:
        if not frame:
            return frame
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        if width == 0:
            return frame

        # Initialize positions on first frame
        if not self.positions:
            self.positions = [
                [(x, y) for x in range(width)]
                for y in range(height)
            ]

        # Simple displacement toward mouse
        result = []
        for y, row in enumerate(frame):
            new_row = []
            for x, char in enumerate(row):
                dx = state.x - x
                dy = state.y - y
                dist = math.sqrt(dx*dx + dy*dy) + 1
                
                # Displacement factor
                factor = self.strength / dist
                
                # Sample from displaced position
                src_x = int(x - dx * factor)
                src_y = int(y - dy * factor)
                src_x = max(0, min(width - 1, src_x))
                src_y = max(0, min(height - 1, src_y))
                
                new_row.append(frame[src_y][src_x])
            result.append("".join(new_row))
        
        return result