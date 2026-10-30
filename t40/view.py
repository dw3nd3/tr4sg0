from enum import Enum
from pathlib import Path
import sys
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame

from .model import Room
from .util import pos2idx, idx2pos
from .sandbox import execute
from . import config
from .plugin import manager as plugin_manager


class TextView:
    def __init__(self, font, bg_color, fg_color, screen):
        self.font = font
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.screen = screen
        self.padding_percentage = (0.1, 0.06)
        self.allowed_width = self.screen.get_width() - self.screen.get_width() * self.padding_percentage[0] * 2
        self.top_left = (
            self.screen.get_width() * self.padding_percentage[0] / 2,
            self.screen.get_height() * self.padding_percentage[1] / 2,
        )

    def print(self, text):
        print(text)
        self.screen.fill(self.bg_color)
        self.renderText(text)
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    return

    def renderText(self, text):
        # Source - https://stackoverflow.com/a/49433498
        # Posted by SpoonMeiser, modified by community. See post 'Timeline' for change history
        # Retrieved 2026-01-17, License - CC BY-SA 3.0
        # Modified by MiguelMJ

        words = text.split()

        lines = []
        while len(words) > 0:
            line_words = []
            while len(words) > 0:
                line_words.append(words.pop(0))
                line_width, _ = self.font.size(" ".join(line_words + words[:1]))
                if line_width > self.allowed_width:
                    break

            line = " ".join(line_words)
            lines.append(line)

        screen_w, screen_h = self.screen.get_size()
        y_offset = 0
        for line in lines:
            line_width, line_height = self.font.size(line)
            font_surface = self.font.render(line, True, self.fg_color)
            self.screen.blit(
                font_surface, (self.top_left[1], self.top_left[0] + y_offset)
            )

            y_offset += line_height


class Avatar:
    class Direction(Enum):
        EAST = 0
        NORTH = 1
        WEST = 2
        SOUTH = 3

    def __init__(self):
        self.surface = None
        self.row = 0
        self.col = 0
        self.row_display = 0
        self.col_display = 0
        self.speed = 0.2
        self.facing = self.Direction.EAST

    def update(self):
        row_delta = self.row - self.row_display
        if abs(row_delta) <= self.speed: self.row_display = self.row
        elif row_delta < 0: self.row_display -= self.speed
        else: self.row_display += self.speed
        col_delta = self.col - self.col_display
        if abs(col_delta) <= self.speed: self.col_display = self.col
        elif col_delta < 0: self.col_display -= self.speed
        else: self.col_display += self.speed
    
    def is_moving(self):
        return self.row != self.row_display or self.col != self.col_display

    @property
    def target(self):
        if self.facing == Avatar.Direction.EAST:
            return (self.row, self.col + 1)
        elif self.facing == Avatar.Direction.NORTH:
            return (self.row - 1, self.col)
        elif self.facing == Avatar.Direction.WEST:
            return (self.row, self.col - 1)
        elif self.facing == Avatar.Direction.SOUTH:
            return (self.row + 1, self.col)


class View:

    def __init__(self):
        self.room = None
        self.base_tile_size = 8
        self.grid_width = 16
        self.grid_height = 16
        self.fps = 30
        self.zoom = config.get("WINDOW", "Scale", 4, int)
        self.sprite_surfaces = {}
        self.avatar = Avatar()
        self.screen = pygame.display.set_mode(
            (self.grid_width * self.tile_size, self.grid_height * self.tile_size),
            pygame.RESIZABLE,
        )
        pygame.display.set_icon(pygame.image.load(Path(__file__).parent / "icon.png"))
        self.textView = None

        for callback in plugin_manager.plugin_on_window_open:
            callback(self.screen)

    @property
    def tile_size(self):
        return self.base_tile_size * self.zoom

    def _build_sprite(self, sprite):
        surface = pygame.Surface((8, 8))
        for y in range(8):
            for x in range(8):
                c = sprite[y * 8 + x]
                surface.set_at((x, y), pygame.Color("0x" + self.room.color(c)))

        return pygame.transform.scale(surface, (self.tile_size, self.tile_size))

    def set_room(self, room):
        self.room = room
        self.textView = TextView(
            pygame.font.SysFont(None, 8 * self.zoom),
            pygame.Color("0x" + self.room.palette[0]),
            pygame.Color("0x" + self.room.palette[1]),
            self.screen,
        )
        self.sprite_surfaces = {
            sprite_id: self._build_sprite(room.sprites[sprite_id])
            for sprite_id in room.sprites
        }
        self.avatar.row, self.avatar.col = self.room.start
        self.avatar.row_display, self.avatar.col_display = self.room.start

    def print(self, text):
        self.textView.print(text)

    def render(self):
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                pos2d = (col * self.tile_size, row * self.tile_size)
                rect = pygame.Rect(
                    col * self.tile_size,
                    row * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )

                sprite_id = self.room.sprite(row, col)
                if sprite_id in self.sprite_surfaces:
                    self.screen.blit(self.sprite_surfaces[sprite_id], pos2d)
                else:
                    pygame.draw.rect(self.screen, pygame.Color("red"), rect)

            self.screen.blit(
                pygame.transform.rotate(
                    self.sprite_surfaces["avatar"], self.avatar.facing.value * 90
                ),
                (self.avatar.col_display * self.tile_size, self.avatar.row_display * self.tile_size),
            )

    def run(self):
        clock = pygame.time.Clock()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_F8, pygame.K_q):
                        running = False
                    
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e, pygame.K_z):
                        program = self.room.interact(*self.avatar.target)
                        if program:
                            for sentence in program:
                                execute(sentence, self)

                for callback in plugin_manager.plugin_on_user_event_callbacks:
                    callback(event)
                



            if not self.avatar.is_moving():
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    if not self.room.is_solid(self.avatar.row, self.avatar.col - 1):
                        self.avatar.col -= 1
                    self.avatar.facing = Avatar.Direction.WEST

                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    if not self.room.is_solid(self.avatar.row, self.avatar.col + 1):
                        self.avatar.col += 1
                    self.avatar.facing = Avatar.Direction.EAST

                elif keys[pygame.K_UP] or keys[pygame.K_w]:
                    if not self.room.is_solid(self.avatar.row - 1, self.avatar.col):
                        self.avatar.row -= 1
                    self.avatar.facing = Avatar.Direction.NORTH

                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    if not self.room.is_solid(self.avatar.row + 1, self.avatar.col):
                        self.avatar.row += 1
                    self.avatar.facing = Avatar.Direction.SOUTH


            self.avatar.update()    

            self.screen.fill(pygame.Color("black"))
            self.render()
            pygame.display.flip()

            yield
            clock.tick(self.fps)

        pygame.quit()
        for callback in plugin_manager.plugin_on_window_close:
            callback(self.screen)


_view = None


def setup():
    global _view
    pygame.init()
    _view = View()


def open(room):
    _view.set_room(room)


def current_room():
    return _view.room


def run():
    return _view.run()


def get_view():
    return _view
