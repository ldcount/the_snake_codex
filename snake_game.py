import random
import pygame


class GameObject:
    def __init__(self, x: int, y: int, size: int, color: tuple[int, int, int]):
        self.x = x
        self.y = y
        self.size = size
        self.color = color

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect)


class Snake(GameObject):
    def __init__(self, x: int, y: int, size: int):
        super().__init__(x, y, size, (0, 200, 0))
        # Start with exactly one segment (head only)
        self.segments: list[tuple[int, int]] = [(x, y)]
        self.dx = size
        self.dy = 0
        self.pending_growth = 0

    def set_direction(self, dx: int, dy: int) -> None:
        if not self.segments:
            return
        if (dx, dy) == (-self.dx, -self.dy):
            return
        self.dx = dx
        self.dy = dy

    def move(self, width: int, height: int) -> None:
        if not self.segments:
            return

        head_x, head_y = self.segments[0]
        new_x = (head_x + self.dx) % width
        new_y = (head_y + self.dy) % height
        self.segments.insert(0, (new_x, new_y))

        if self.pending_growth > 0:
            self.pending_growth -= 1
        else:
            self.segments.pop()

        if self.segments:
            self.x, self.y = self.segments[0]

    def grow(self) -> None:
        self.pending_growth += 1

    def shorten(self) -> None:
        if self.segments:
            self.segments.pop()
        if self.segments:
            self.x, self.y = self.segments[0]

    def collides_with_self(self) -> bool:
        if len(self.segments) < 2:
            return False
        return self.segments[0] in self.segments[1:]

    def draw(self, surface: pygame.Surface) -> None:
        for i, (seg_x, seg_y) in enumerate(self.segments):
            color = (30, 230, 30) if i == 0 else self.color
            pygame.draw.rect(surface, color, pygame.Rect(seg_x, seg_y, self.size, self.size))


class Rock(GameObject):
    def __init__(self, x: int, y: int, size: int):
        super().__init__(x, y, size, (90, 90, 90))


class Apple(GameObject):
    def __init__(self, x: int, y: int, size: int):
        super().__init__(x, y, size, (220, 30, 30))


class SnakeGame:
    WIDTH = 640
    HEIGHT = 490
    CELL = 20
    ROCK_COUNT = 3
    MOVE_INTERVAL_MS = 120

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Snake")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 28, bold=True)
        self.small_font = pygame.font.SysFont("arial", 22)

        # Keep gameplay strictly on the 20x20 grid.
        self.play_height = (self.HEIGHT // self.CELL) * self.CELL
        self.grid_positions = [
            (x, y)
            for x in range(0, self.WIDTH, self.CELL)
            for y in range(0, self.play_height, self.CELL)
        ]

        self.running = True
        self.last_move = 0
        self.score = 0

        self.snake = self._create_snake()
        self.apple = Apple(0, 0, self.CELL)
        self.rocks: list[Rock] = []
        self._reset_objects()

    def _create_snake(self) -> Snake:
        # Center snapped to grid to avoid any visual shift.
        start_x = (self.WIDTH // 2 // self.CELL) * self.CELL
        start_y = (self.play_height // 2 // self.CELL) * self.CELL
        return Snake(start_x, start_y, self.CELL)

    def _blocked_positions(self) -> set[tuple[int, int]]:
        blocked = set(self.snake.segments)
        blocked.update((rock.x, rock.y) for rock in self.rocks)
        blocked.add((self.apple.x, self.apple.y))
        return blocked

    def _random_free_position(self, blocked: set[tuple[int, int]]) -> tuple[int, int]:
        free = [pos for pos in self.grid_positions if pos not in blocked]
        return random.choice(free)

    def _spawn_apple(self) -> Apple:
        blocked = set(self.snake.segments)
        blocked.update((rock.x, rock.y) for rock in self.rocks)
        x, y = self._random_free_position(blocked)
        return Apple(x, y, self.CELL)

    def _spawn_rocks(self) -> list[Rock]:
        rocks: list[Rock] = []
        blocked = set(self.snake.segments)
        blocked.add((self.apple.x, self.apple.y))

        while len(rocks) < self.ROCK_COUNT:
            x, y = self._random_free_position(blocked)
            blocked.add((x, y))
            rocks.append(Rock(x, y, self.CELL))

        return rocks

    def _ensure_rock_count(self) -> None:
        blocked = set(self.snake.segments)
        blocked.add((self.apple.x, self.apple.y))
        blocked.update((rock.x, rock.y) for rock in self.rocks)

        while len(self.rocks) < self.ROCK_COUNT:
            x, y = self._random_free_position(blocked)
            blocked.add((x, y))
            self.rocks.append(Rock(x, y, self.CELL))

        if len(self.rocks) > self.ROCK_COUNT:
            self.rocks = self.rocks[: self.ROCK_COUNT]

    def _reset_objects(self) -> None:
        self.snake = self._create_snake()
        self.rocks = []
        self.apple = self._spawn_apple()
        self.rocks = self._spawn_rocks()

    def _reset_round(self) -> None:
        self._show_game_over()
        self.score = 0
        self._reset_objects()
        self.last_move = pygame.time.get_ticks()

    def _show_game_over(self) -> None:
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        text = self.font.render("GAME OVER", True, (255, 255, 255))
        sub = self.small_font.render("Restarting...", True, (220, 220, 220))

        self.screen.blit(text, text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 16)))
        self.screen.blit(sub, sub.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 20)))
        pygame.display.flip()
        pygame.time.delay(1200)

    def _handle_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_UP:
                    self.snake.set_direction(0, -self.CELL)
                elif event.key == pygame.K_DOWN:
                    self.snake.set_direction(0, self.CELL)
                elif event.key == pygame.K_LEFT:
                    self.snake.set_direction(-self.CELL, 0)
                elif event.key == pygame.K_RIGHT:
                    self.snake.set_direction(self.CELL, 0)

    def _handle_rock_collision(self) -> None:
        if not self.snake.segments:
            return

        head = self.snake.segments[0]
        hit_index = next((i for i, rock in enumerate(self.rocks) if (rock.x, rock.y) == head), None)

        if hit_index is not None:
            self.snake.shorten()
            self.rocks.pop(hit_index)
            self._ensure_rock_count()

    def _update(self) -> None:
        now = pygame.time.get_ticks()
        if now - self.last_move < self.MOVE_INTERVAL_MS:
            return

        self.last_move = now
        self.snake.move(self.WIDTH, self.play_height)

        self._handle_rock_collision()
        if not self.snake.segments:
            self._reset_round()
            return

        if self.snake.collides_with_self():
            self._reset_round()
            return

        if self.snake.rect.colliderect(self.apple.rect):
            self.snake.grow()
            self.score += 1
            self.apple = self._spawn_apple()

        self._ensure_rock_count()

    def _draw(self) -> None:
        self.screen.fill((18, 18, 18))

        # Draw grid only in gameplay area.
        for x in range(0, self.WIDTH + 1, self.CELL):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, self.play_height))
        for y in range(0, self.play_height + 1, self.CELL):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (self.WIDTH, y))

        self.apple.draw(self.screen)
        for rock in self.rocks:
            rock.draw(self.screen)
        self.snake.draw(self.screen)

        hud = self.small_font.render(f"Score: {self.score}    Esc: Quit", True, (225, 225, 225))
        self.screen.blit(hud, (10, 8))

        pygame.display.flip()

    def run(self) -> None:
        self.last_move = pygame.time.get_ticks()
        while self.running:
            self._handle_input()
            self._update()
            self._draw()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    SnakeGame().run()
