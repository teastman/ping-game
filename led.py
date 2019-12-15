import pygame
from typing import Optional

import rx

class Strip:

    """
    Represents a physical LED Strip.
    """

    off_color = (0,0,0)
    on_color = (50,255,50)

    def __init__(self, size: int):
        self.size = size
        self.leds = [self.off_color for i in range(self.size)]

    # def update(self):
        # push the colors to the actual led strip.

    def reset(self):
        self.leds = [self.off_color for i in range(self.size)]      
