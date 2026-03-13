import pygame
import random
import json
import os

# Initialize Pygame modules
pygame.init()
pygame.mixer.init()  # Initialize the mixer for sounds

# ----- GAME SETTINGS -----
WIDTH = 500           # Window width
HEIGHT = 650          # Window height
BLOCK = 30            # Size of each block
GRID_W = 10           # Number of columns
GRID_H = 20           # Number of rows

# Setup game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Tetris")

clock = pygame.time.Clock()  # For controlling FPS

# ----- SOUND EFFECTS -----
line_sound = pygame.mixer.Sound("clear.ogg")     # Sound when a line is cleared
rotate_sound = pygame.mixer.Sound("rotate.ogg")  # Sound when a piece rotates
drop_sound = pygame.mixer.Sound("click.wav")     # Sound for hard drop
gameover_sound = pygame.mixer.Sound("gameover.wav")  # Sound for game over

# Background music loop
pygame.mixer.music.load("music.ogg")
pygame.mixer.music.play(-1)

# ----- COLORS -----
colors = [
    (0, 255, 255),   # Cyan
    (0, 0, 255),     # Blue
    (255, 165, 0),   # Orange
    (255, 255, 0),   # Yellow
    (0, 255, 0),     # Green
    (160, 32, 240),  # Purple
    (255, 0, 0)      # Red
]

# ----- SHAPES (Tetrominoes) -----
shapes = [
    [[1, 1, 1, 1]],             # I
    [[1, 1], [1, 1]],           # O
    [[0, 1, 0], [1, 1, 1]],       # T
    [[1, 0, 0], [1, 1, 1]],       # J
    [[0, 0, 1], [1, 1, 1]],       # L
    [[1, 1, 0], [0, 1, 1]],       # S
    [[0, 1, 1], [1, 1, 0]]        # Z
]

# ----- HIGH SCORE HANDLING -----


def load_highscore():
    """Load highscore from JSON file"""
    if os.path.exists("highscore.json"):
        with open("highscore.json") as f:
            return json.load(f)["score"]
    return 0


def save_highscore(score):
    """Save highscore to JSON file"""
    with open("highscore.json", "w") as f:
        json.dump({"score": score}, f)

# ----- PIECE CLASS -----


class Piece:
    """Represents a single Tetromino piece"""

    def __init__(self):
        self.shape = random.choice(shapes)  # Random shape
        self.color = random.choice(colors)  # Random color
        self.x = GRID_W // 2 - 2             # Start horizontally near middle
        self.y = 0                            # Start at top

    def blocks(self):
        """Yield coordinates of each block of the piece"""
        for r, row in enumerate(self.shape):
            for c, val in enumerate(row):
                if val:
                    yield (self.x+c, self.y+r)

# ----- TETRIS GAME CLASS -----


class Tetris:
    """Handles all game logic"""

    def __init__(self):
        self.grid = [[0]*GRID_W for _ in range(GRID_H)]  # Grid to track blocks
        self.piece = Piece()                              # Current piece
        self.next = Piece()                               # Next piece
        self.score = 0
        self.level = 1
        self.lines = 0
        self.highscore = load_highscore()
        self.speed = 40    # Counter speed for automatic falling
        self.counter = 0
        self.game_over = False

    def valid(self, blocks):
        """Check if a move or rotation is valid (inside grid and no collision)"""
        for x, y in blocks:
            if x < 0 or x >= GRID_W or y >= GRID_H:
                return False
            if y >= 0 and self.grid[y][x]:
                return False
        return True

    def lock(self):
        """Lock piece into the grid and spawn a new piece"""
        for x, y in self.piece.blocks():
            if y >= 0:
                self.grid[y][x] = self.piece.color
        self.clear_lines()
        self.piece = self.next
        self.next = Piece()
        # Check if game over
        if not self.valid(self.piece.blocks()):
            self.game_over = True
            gameover_sound.play()

    def clear_lines(self):
        """Clear completed rows and update score, lines, level"""
        full = [i for i, row in enumerate(self.grid) if all(row)]
        if full:
            line_sound.play()
        for i in full:
            del self.grid[i]
            self.grid.insert(0, [0]*GRID_W)
        n = len(full)
        self.lines += n
        self.score += n*n*100  # Score grows faster for multiple lines
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.score)
        self.level = 1 + self.lines // 10
        self.speed = max(10, 40 - self.level*2)  # Increase falling speed

    def rotate(self):
        """Rotate current piece"""
        rotate_sound.play()
        new = list(zip(*self.piece.shape[::-1]))  # Rotate matrix
        old = self.piece.shape
        self.piece.shape = new
        # Undo if invalid
        if not self.valid(self.piece.blocks()):
            self.piece.shape = old

    def move(self, dx):
        """Move piece left or right"""
        self.piece.x += dx
        if not self.valid(self.piece.blocks()):
            self.piece.x -= dx

    def hard_drop(self):
        """Drop piece to the bottom instantly"""
        drop_sound.play()
        while self.valid(self.piece.blocks()):
            self.piece.y += 1
        self.piece.y -= 1
        self.lock()

    def update(self):
        """Update piece position automatically each frame"""
        if self.game_over:
            return
        self.counter += 1
        if self.counter >= self.speed:
            self.counter = 0
            self.piece.y += 1
            if not self.valid(self.piece.blocks()):
                self.piece.y -= 1
                self.lock()

    def ghost(self):
        """Return ghost piece position (where piece would land)"""
        old_y = self.piece.y
        while True:
            self.piece.y += 1
            if not self.valid(self.piece.blocks()):
                self.piece.y -= 1
                ghost = list(self.piece.blocks())
                self.piece.y = old_y
                return ghost

    def draw(self):
        """Draw the entire game screen"""
        screen.fill((0, 0, 0))  # Background

        # Draw grid
        for y, row in enumerate(self.grid):
            for x, val in enumerate(row):
                rect = pygame.Rect(x*BLOCK+50, y*BLOCK+50, BLOCK, BLOCK)
                pygame.draw.rect(screen, (40, 40, 40), rect, 1)
                if val:
                    pygame.draw.rect(screen, val, rect)

        # Draw ghost piece
        for x, y in self.ghost():
            rect = pygame.Rect(x*BLOCK+50, y*BLOCK+50, BLOCK, BLOCK)
            pygame.draw.rect(screen, (80, 80, 80), rect)

        # Draw current piece
        for x, y in self.piece.blocks():
            rect = pygame.Rect(x*BLOCK+50, y*BLOCK+50, BLOCK, BLOCK)
            pygame.draw.rect(screen, self.piece.color, rect)

        # Draw score, level, lines, highscore
        font = pygame.font.Font(None, 36)
        screen.blit(font.render(
            f"Score: {self.score}", True, (255, 255, 255)), (350, 120))
        screen.blit(font.render(
            f"Level: {self.level}", True, (255, 255, 255)), (350, 160))
        screen.blit(font.render(
            f"Lines: {self.lines}", True, (255, 255, 255)), (350, 200))
        screen.blit(font.render(
            f"Best: {self.highscore}", True, (255, 255, 0)), (350, 240))

        # Game over message
        if self.game_over:
            big = pygame.font.Font(None, 60)
            screen.blit(big.render("GAME OVER", True, (255, 0, 0)), (120, 300))
            screen.blit(font.render("Press R to Restart",
                        True, (255, 255, 255)), (160, 360))


# ----- MAIN GAME LOOP -----
game = Tetris()
paused = False
running = True

while running:
    clock.tick(60)  # 60 FPS

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Movement
            if event.key == pygame.K_LEFT:
                game.move(-1)
            if event.key == pygame.K_RIGHT:
                game.move(1)
            if event.key == pygame.K_DOWN:
                game.piece.y += 1  # Soft drop

            # Rotation
            if event.key == pygame.K_UP:
                game.rotate()

            # Hard drop
            if event.key == pygame.K_SPACE:
                game.hard_drop()

            # Pause
            if event.key == pygame.K_p:
                paused = not paused

            # Restart
            if event.key == pygame.K_r:
                game = Tetris()

    if not paused:
        game.update()

    game.draw()
    pygame.display.update()

pygame.quit()
