import pygame

class Button:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        text="",
        bg_color=None,
        text_color=(0, 0, 0),
        font=None,
        image_path=None
    ):
        # Store the button's position and size as a pygame Rect for easy collision detection
        self.rect       = pygame.Rect(x, y, width, height)
        self.text       = text
        self.bg_color   = bg_color
        self.text_color = text_color

        # Use the provided font, or fall back to a default system font
        self.font = font or pygame.font.SysFont(None, 30)

        # Try to load the icon image for the button.
        # self.image stays None if no path is given or the file is missing —
        # draw() will fall back to drawing a plain colored rectangle instead.
        self.image = None
        if image_path is not None:
            try:
                img = pygame.image.load(image_path).convert_alpha()
                # Scale the icon to 60% of the button height so there is room for the label below
                img_height = int(height * 0.6)
                self.image = pygame.transform.scale(img, (width, img_height))
            except (pygame.error, FileNotFoundError):
                # File not found or unreadable — button will render without an icon
                pass

    def draw(self, surface, enabled=True):
        """
        Draw the button onto surface.

        enabled (bool):
            True  → draw normally (full color / full opacity)
            False → draw greyed-out (faded icon or gray rectangle)
                    to signal that the button cannot be clicked right now
        """
        if self.image is not None:
            # Button has an icon image
            # When disabled, make a copy and lower its opacity so it looks faded
            img = self.image if enabled else self.image.copy()
            if not enabled:
                img.set_alpha(120)   # 0 = invisible, 255 = fully opaque; 120 = dimmed
            img_x = self.rect.x + (self.rect.width - img.get_width()) // 2
            surface.blit(img, (img_x, self.rect.y))
        else:
            # No icon — draw a solid rectangle.
            # Use the assigned bg_color when enabled, or gray when disabled.
            color = self.bg_color if enabled else (180, 180, 180)
            pygame.draw.rect(surface, color,       self.rect, border_radius=10)
            pygame.draw.rect(surface, (0, 0, 0),   self.rect, 2, border_radius=10)  # border

        # Draw the text label if one was provided
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)

            if self.image is not None:
                # Icon button: place the label at the bottom of the button rect
                text_rect = text_surface.get_rect(
                    centerx=self.rect.centerx,
                    bottom=self.rect.bottom - 2
                )
            else:
                # Plain button: center the label inside the rectangle
                text_rect = text_surface.get_rect(center=self.rect.center)

            surface.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        """
        Return True if pos (mouse x, y) falls inside this button's rectangle.
        Used in the event loop to detect mouse clicks on this button.
        """
        return self.rect.collidepoint(pos)
