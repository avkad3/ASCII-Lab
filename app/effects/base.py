"""Base class for ASCII visual effects."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class InteractionState:
    """Mouse/interaction state for effects."""
    def __init__(self, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0,
                 pressed: bool = False, button: int = 0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.pressed = pressed
        self.button = button


class Effect(ABC):
    """Base class for ASCII visual effects."""

    @abstractmethod
    def apply(self, frame: List[str], state: InteractionState) -> List[str]:
        """Apply effect to an ASCII frame.
        
        Args:
            frame: List of row strings.
            state: Current interaction state.
            
        Returns:
            Modified frame.
        """
        ...

    def reset(self):
        """Reset effect internal state."""
        pass