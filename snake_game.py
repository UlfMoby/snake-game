#!/usr/bin/env python3
"""
Snake Game - Vibe coded by k0rp

Requirements:
  - Python 3.8+
  - pygame (pip install pygame)

Run:
  python3 snake_game.py

Controls:
  - Arrow keys or WASD to move
  - P to pause/resume
  - Esc to go back to menu (from game or how-to)
  - Enter/Space to select in menus
"""
import sys
import random
from dataclasses import dataclass

try:
    import pygame
except ImportError:
    print("This game requires pygame. Install with: pip install pygame")
    sys.exit(1)

# ----------------------------- Config ---------------------------------
TITLE = "Snake Game - Vibe coded by k0rp"
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GRID_SIZE = 20  # size of each cell in pixels
GRID_COLS = WINDOW_WIDTH // GRID_SIZE
GRID_ROWS = WINDOW_HEIGHT // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (60, 60, 60)
DARK_GRAY = (30, 30, 30)
GREEN = (0, 200, 0)
RED = (220, 50, 50)
YELLOW = (240, 200, 0)
CYAN = (0, 200, 200)
MAGENTA = (200, 0, 200)

# Difficulty settings map: name -> moves per second
DIFFICULTIES = {
    "Easy": 8,
    "Medium": 12,
    "Hard": 18,
}

@dataclass
class Direction:
    x: int
    y: int

UP = Direction(0, -1)
DOWN = Direction(0, 1)
LEFT = Direction(-1, 0)
RIGHT = Direction(1, 0)

OPPOSITE = {
    (0, -1): (0, 1),
    (0, 1): (0, -1),
    (-1, 0): (1, 0),
    (1, 0): (-1, 0),
}

# ----------------------------- Helpers --------------------------------

def draw_text(surface, text, font, color, center=None, topleft=None, antialias=True):
    img = font.render(text, antialias, color)
    rect = img.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    surface.blit(img, rect)
    return rect

# ----------------------------- Game Objects ----------------------------

class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        cx, cy = GRID_COLS // 2, GRID_ROWS // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]  # list of (x,y)
        self.dir = RIGHT
        self.grow = 0
        self.alive = True

    def set_direction(self, new_dir: Direction):
        # prevent reversing directly
        if (new_dir.x, new_dir.y) == OPPOSITE[(self.dir.x, self.dir.y)]:
            return
        self.dir = new_dir

    def update(self):
        if not self.alive:
            return
        head_x, head_y = self.body[0]
        nx = (head_x + self.dir.x) % GRID_COLS
        ny = (head_y + self.dir.y) % GRID_ROWS
        new_head = (nx, ny)
        # Collision with self
        if new_head in self.body:
            self.alive = False
            return
        self.body.insert(0, new_head)
        if self.grow > 0:
            self.grow -= 1
        else:
            self.body.pop()

    def eat(self):
        self.grow += 1

class Food:
    def __init__(self, snake: Snake):
        self.pos = self._random_pos(snake)

    def _random_pos(self, snake: Snake):
        while True:
            x = random.randint(0, GRID_COLS - 1)
            y = random.randint(0, GRID_ROWS - 1)
            if (x, y) not in snake.body:
                return (x, y)

    def respawn(self, snake: Snake):
        self.pos = self._random_pos(snake)

# ----------------------------- Screens ---------------------------------

class MenuScreen:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.font_title = fonts["title"]
        self.font_menu = fonts["menu"]
        self.options = ["Play: Easy", "Play: Medium", "Play: Hard", "How to Play", "Quit"]
        self.index = 0

    def draw(self):
        self.screen.fill(BLACK)
        draw_text(self.screen, TITLE, self.font_title, YELLOW, center=(WINDOW_WIDTH // 2, 90))
        draw_text(self.screen, "Use Up/Down to select, Enter to confirm", self.font_menu, GRAY, center=(WINDOW_WIDTH // 2, 140))
        base_y = 200
        for i, opt in enumerate(self.options):
            color = CYAN if i == self.index else WHITE
            draw_text(self.screen, opt, self.font_menu, color, center=(WINDOW_WIDTH // 2, base_y + i * 40))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.index]
        return None

class HowToScreen:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.font_title = fonts["title"]
        self.font_text = fonts["menu"]

    def draw(self):
        self.screen.fill(BLACK)
        draw_text(self.screen, "How to Play", self.font_title, GREEN, center=(WINDOW_WIDTH // 2, 80))
        lines = [
            "Goal: Eat food to grow and score points.",
            "Controls:",
            "  - Move: Arrow Keys or WASD",
            "  - Pause/Resume: P",
            "  - Back to Menu: Esc",
            "Scoring: +1 per food. Don't crash into yourself.",
            "Wrap-around: Going off one edge brings you to the other side.",
            "Press Esc to return to Menu.",
        ]
        y = 140
        for line in lines:
            draw_text(self.screen, line, self.font_text, WHITE, topleft=(50, y))
            y += 34

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "Back"
        return None

class GameScreen:
    def __init__(self, screen, fonts, difficulty_name: str):
        self.screen = screen
        self.font_hud = fonts["menu"]
        self.snake = Snake()
        self.food = Food(self.snake)
        self.score = 0
        self.paused = False
        self.difficulty_name = difficulty_name
        self.moves_per_sec = DIFFICULTIES[difficulty_name]
        self.move_timer = 0.0

    def draw_grid(self):
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, DARK_GRAY, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, DARK_GRAY, (0, y), (WINDOW_WIDTH, y))

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_grid()
        # Draw food
        fx, fy = self.food.pos
        pygame.draw.rect(self.screen, RED, (fx * GRID_SIZE, fy * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        # Draw snake
        for i, (x, y) in enumerate(self.snake.body):
            color = GREEN if i == 0 else (0, 140, 0)
            pygame.draw.rect(self.screen, color, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        # HUD
        draw_text(
            self.screen,
            f"Score: {self.score}    Difficulty: {self.difficulty_name}    P:Pause  Esc:Menu",
            self.font_hud,
            YELLOW,
            topleft=(10, 10),
        )
        if not self.snake.alive:
            draw_text(self.screen, "Game Over! Press Enter to return to Menu", self.font_hud, MAGENTA, center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        if self.paused and self.snake.alive:
            draw_text(self.screen, "Paused", self.font_hud, CYAN, center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

    def update(self, dt):
        if self.paused or not self.snake.alive:
            return
        self.move_timer += dt
        step = 1.0 / float(self.moves_per_sec)
        while self.move_timer >= step:
            self.move_timer -= step
            self.snake.update()
            # Check eat
            if self.snake.body and self.snake.body[0] == self.food.pos:
                self.snake.eat()
                self.score += 1
                self.food.respawn(self.snake)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.snake.set_direction(UP)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.snake.set_direction(DOWN)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.snake.set_direction(LEFT)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.snake.set_direction(RIGHT)
            elif event.key == pygame.K_p:
                self.paused = not self.paused
            elif event.key == pygame.K_ESCAPE:
                return "Menu"
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if not self.snake.alive:
                    return "Menu"
        return None

# ----------------------------- App Controller --------------------------

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        # Fonts
        self.fonts = {
            "title": pygame.font.SysFont("arial", 36, bold=True),
            "menu": pygame.font.SysFont("arial", 20),
        }
        self.clock = pygame.time.Clock()
        self.state = "menu"  # menu | howto | game
        self.menu = MenuScreen(self.screen, self.fonts)
        self.howto = HowToScreen(self.screen, self.fonts)
        self.game = None

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0  # seconds
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self._handle_event(event)

            self._update(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _handle_event(self, event):
        if self.state == "menu":
            result = self.menu.handle_event(event)
            if result:
                if result.startswith("Play: "):
                    diff = result.split(": ")[-1]
                    self.game = GameScreen(self.screen, self.fonts, diff)
                    self.state = "game"
                elif result == "How to Play":
                    self.state = "howto"
                elif result == "Quit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state == "howto":
            result = self.howto.handle_event(event)
            if result == "Back":
                self.state = "menu"
        elif self.state == "game":
            result = self.game.handle_event(event)
            if result == "Menu":
                self.state = "menu"

    def _update(self, dt):
        if self.state == "game" and self.game is not None:
            self.game.update(dt)

    def _draw(self):
        if self.state == "menu":
            self.menu.draw()
        elif self.state == "howto":
            self.howto.draw()
        elif self.state == "game" and self.game is not None:
            self.game.draw()


def main():
    App().run()


if __name__ == "__main__":
    main()

