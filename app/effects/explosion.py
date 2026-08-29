"""Explosion effect — characters disperse on click."""
import math
from typing import List
from .base import Effect, InteractionState


class ExplosionEffect(Effect):
    """Characters disperse outward from click position."""

    def __init__(self, force: float = 5.0, decay: float = 0.9):
        self.force = force
        self.decay = decay
        self.velocities = {}
        self.active = False
        self.center = (0, 0)

    def apply(self, frame: List[str], state: InteractionState) -> List[str]:
        if not frame:
            return frame
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        if width == 0:
            return frame

        # Trigger explosion on click
        if state.pressed and not self.active:
            self.active = True
            self.center = (state.x, state.y)
            self.velocities = {}
            for y in range(height):
                for x in range(width):
                    dx = x - state.x
                    dy = y - state.y
                    dist = math.sqrt(dx*dx + dy*dy) + 0.1
                    self.velocities[(x, y)] = (dx/dist * self.force, dy/dist * self.force)

        if not self.active:
            return frame

        # Apply velocities and decay
        result = [[" " for _ in range(width)] for _ in range(height)]
        new_velocities = {}
        
        for (x, y), (vx, vy) in self.velocities.items():
            new_x = int(x + vx)
            new_y = int(y + vy)
            
            if 0 <= new_x < width and 0 <= new_y < height:
                result[new_y][new_x] = frame[y][x]
                new_velocities[(new_x, new_y)] = (vx * self.decay, vy * self.decay)

        self.velocities = new_velocities
        
        # Stop when velocities are negligible
        if all(abs(vx) < 0.1 and abs(vy) < 0.1 for vx, vy in self.velocities.values()):
            self.active = False
            self.velocities = {}

        return ["".join(row) for row in result]

    def reset(self):
        self.active = False
        self.velocities = {}
        self.time = 0