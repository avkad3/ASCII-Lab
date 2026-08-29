"""Fire effect — heat/density animation."""
import math
import random
from typing import List
from .base import Effect, InteractionState


class FireEffect(Effect):
    """Characters animate using heat/density changes."""

    def __init__(self, intensity: float = 1.0):
        self.intensity = intensity
        self.heat = []
        self.time = 0

    def apply(self, frame: List[str], state: InteractionState) -> List[str]:
        if not frame:
            return frame
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        if width == 0:
            return frame

        self.time += 0.05
        
        # Initialize heat map
        if not self.heat or len(self.heat) != height or len(self.heat[0]) != width:
            self.heat = [[0.0 for _ in range(width)] for _ in range(height)]

        # Heat rises from bottom + mouse influence
        for y in range(height):
            for x in range(width):
                # Base heat from bottom
                base_heat = (height - y) / height * 0.3
                
                # Mouse heat
                dx = x - state.x
                dy = y - state.y
                dist = math.sqrt(dx*dx + dy*dy) + 1
                mouse_heat = self.intensity / dist
                
                # Turbulence
                turb = math.sin(x * 0.1 + self.time) * math.cos(y * 0.1 + self.time * 0.5) * 0.1
                
                self.heat[y][x] = base_heat + mouse_heat + turb + random.uniform(-0.05, 0.05)
                self.heat[y][x] = max(0, min(1, self.heat[y][x]))

        # Map heat to characters (hot = dense, cold = light)
        chars = " .:-=+*#%@"
        result = []
        for y, row in enumerate(frame):
            new_row = []
            for x, char in enumerate(row):
                h = self.heat[y][x]
                idx = int(h * (len(chars) - 1))
                idx = max(0, min(len(chars) - 1, idx))
                new_row.append(chars[idx])
            result.append("".join(new_row))
        
        return result

    def reset(self):
        self.heat = []
        self.time = 0