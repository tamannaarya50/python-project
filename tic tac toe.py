import pygame
import sys
import math
import struct
import random

# Initialize Pygame Mixer with optimal sound settings
try:
    pygame.mixer.pre_init(22050, -16, 1, 512)
except Exception:
    pass

pygame.init()

# --- Game Window Configuration ---
WIDTH, HEIGHT = 600, 700
SCREEN_SIZE = (WIDTH, HEIGHT)
FPS = 60

# --- Color Theme ---
COLOR_BG_START = (15, 16, 26)       # Dark midnight blue
COLOR_BG_END = (30, 32, 54)         # Deep slate blue
COLOR_GRID = (45, 50, 80)           # Dark metallic blue-grey
COLOR_X = (255, 107, 107)           # Radiant coral red
COLOR_O = (77, 173, 247)            # Cool neon cyan
COLOR_TEXT = (248, 249, 250)        # Bright off-white
COLOR_MUTED = (130, 134, 155)       # Muted cool grey
COLOR_WIN_LINE = (255, 212, 59)     # Bright gold
COLOR_LOSE_LINE = (180, 50, 50)     # Dull crimson
COLOR_BUTTON = (42, 46, 74)         # Button face
COLOR_BUTTON_HOVER = (60, 65, 105)  # Highlighted button face

# --- Audio Synthesizer (Generates Sounds In-Memory) ---
def create_sound(duration=0.15, volume=0.25, freq_func=lambda t: 440):
    try:
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        buffer = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            freq = freq_func(t)
            # Add subtle fade in and fade out to avoid speaker pops
            envelope = 1.0
            if t < 0.01:
                envelope = t / 0.01
            elif t > duration - 0.02:
                envelope = (duration - t) / 0.02
                
            val = int(32767 * volume * envelope * math.sin(2 * math.pi * freq * t))
            buffer.extend(struct.pack('<h', val))
        return pygame.mixer.Sound(buffer=bytes(buffer))
    except Exception:
        class SilentSound:
            def play(self): pass
        return SilentSound()

# Dynamic audio assets
SOUND_CLICK = create_sound(duration=0.06, volume=0.12, freq_func=lambda t: 650)
SOUND_X = create_sound(duration=0.1, volume=0.18, freq_func=lambda t: 400 + t * 250)
SOUND_O = create_sound(duration=0.1, volume=0.18, freq_func=lambda t: 520 - t * 180)

# Celebratory Fanfare ("Congratulations!")
def make_congrats_sound():
    try:
        sample_rate = 22050
        notes = [523.25, 659.25, 783.99, 1046.50]  # C Major Arpeggio (C5 - E5 - G5 - C6)
        note_dur = 0.12
        buffer = bytearray()
        for note in notes:
            num_samples = int(sample_rate * note_dur)
            for i in range(num_samples):
                t = i / sample_rate
                # Envelope mapping
                env = 1.0
                if t < 0.01: env = t / 0.01
                elif t > note_dur - 0.03: env = (note_dur - t) / 0.03
                val = int(32767 * 0.2 * env * math.sin(2 * math.pi * note * t))
                buffer.extend(struct.pack('<h', val))
        return pygame.mixer.Sound(buffer=bytes(buffer))
    except Exception:
        return create_sound()

# Disappointment Slide ("Oops!")
def make_oops_sound():
    try:
        sample_rate = 22050
        duration = 0.55
        num_samples = int(sample_rate * duration)
        buffer = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            # Sliders frequency from 350Hz down to 140Hz with minor pitch vibrato
            freq = 320 - (180 * (t / duration)) + 12 * math.sin(2 * math.pi * 12 * t)
            env = 1.0
            if t > duration - 0.08: env = (duration - t) / 0.08
            val = int(32767 * 0.22 * env * math.sin(2 * math.pi * freq * t))
            buffer.extend(struct.pack('<h', val))
        return pygame.mixer.Sound(buffer=bytes(buffer))
    except Exception:
        return create_sound()

SOUND_CONGRATS = make_congrats_sound()
SOUND_OOPS = make_oops_sound()
SOUND_DRAW = create_sound(duration=0.35, volume=0.2, freq_func=lambda t: 300 - t * 80)

# --- Fonts ---
FONT_LARGE = pygame.font.SysFont("Segoe UI", 52, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Segoe UI", 30, bold=True)
FONT_SMALL = pygame.font.SysFont("Segoe UI", 20, bold=True)
FONT_TINY = pygame.font.SysFont("Segoe UI", 15, bold=True)

# --- State Definitions ---
STATE_MENU = "menu"
STATE_DIFFICULTY = "difficulty"
STATE_GAME = "game"
STATE_PAUSE = "pause"
STATE_GAME_OVER = "game_over"

class AdvancedTicTacToe:
    def __init__(self):
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Tic Tac Toe - Neon Edition")
        self.clock = pygame.time.Clock()
        self.state = STATE_MENU
        
        self.bg_cache = self.generate_gradient_surface(WIDTH, HEIGHT, COLOR_BG_START, COLOR_BG_END)
        
        # Core Game Variables
        self.board = [None] * 9
        self.current_player = "X"
        self.game_mode = "vs_ai"  # "vs_ai" or "vs_player"
        self.difficulty = "medium"  # "easy", "medium", "impossible"
        
        self.winner = None
        self.winning_line = None
        self.scores = {"X": 0, "O": 0, "Draws": 0}
        
        # AI Delay Variables (Simulated Decision Making)
        self.ai_timer = 0
        self.ai_delay_ms = 600  # AI pauses briefly to feel "real"
        self.ai_thinking = False
        
        # Animation & Special Effects
        self.cell_anim_progress = [0.0] * 9
        self.win_line_progress = 0.0
        self.particles = []
        self.shake_intensity = 0
        
    def generate_gradient_surface(self, width, height, color1, color2):
        surf = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
        return surf

    def reset_board(self, keep_scores=True):
        self.board = [None] * 9
        self.cell_anim_progress = [0.0] * 9
        self.win_line_progress = 0.0
        self.winner = None
        self.winning_line = None
        self.current_player = "X"
        self.ai_thinking = False
        self.particles.clear()
        if not keep_scores:
            self.scores = {"X": 0, "O": 0, "Draws": 0}

    # --- Particle FX Engine ---
    def spawn_particles(self, x, y, color, count=15):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'color': color,
                'size': random.uniform(4, 7),
                'alpha': 255
            })

    def update_particles(self):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.15  # Add weak gravity
            p['alpha'] -= 5  # Slowly fade out
            p['size'] = max(0, p['size'] - 0.08)
            if p['alpha'] <= 0 or p['size'] <= 0:
                self.particles.remove(p)

    def draw_particles(self):
        for p in self.particles:
            temp_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
            color_with_alpha = (p['color'][0], p['color'][1], p['color'][2], p['alpha'])
            pygame.draw.circle(temp_surf, color_with_alpha, (int(p['size']), int(p['size'])), int(p['size']))
            self.screen.blit(temp_surf, (p['x'] - p['size'], p['y'] - p['size']))

    # --- Game Logic & AI Algorithms ---
    def check_winner(self, test_board=None):
        target_board = test_board if test_board is not None else self.board
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for a, b, c in win_conditions:
            if target_board[a] and target_board[a] == target_board[b] == target_board[c]:
                return target_board[a], (a, b, c)
        if None not in target_board:
            return "Draw", None
        return None, None

    def trigger_win_sequence(self, winner, win_line):
        self.winner = winner
        self.winning_line = win_line
        self.shake_intensity = 12  # Generate a quick shake
        
        if winner == "Draw":
            self.scores["Draws"] += 1
            SOUND_DRAW.play()
            self.state = STATE_GAME_OVER
        else:
            self.scores[winner] += 1
            # Check context of victory for sound playback (if VS Computer, play Congrats/Oops)
            if self.game_mode == "vs_ai":
                if winner == "X":
                    SOUND_CONGRATS.play()
                else:
                    SOUND_OOPS.play()
            else:
                # PvP victory sound
                SOUND_CONGRATS.play()

    def get_available_moves(self, b):
        return [i for i, val in enumerate(b) if val is None]

    def minimax(self, test_board, is_maximizing):
        # AI plays as "O" (maximizing), Human plays as "X" (minimizing)
        winner, _ = self.check_winner(test_board)
        if winner == "O":
            return 10
        elif winner == "X":
            return -10
        elif winner == "Draw":
            return 0

        if is_maximizing:
            best_score = -1000
            for move in self.get_available_moves(test_board):
                test_board[move] = "O"
                score = self.minimax(test_board, False)
                test_board[move] = None
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = 1000
            for move in self.get_available_moves(test_board):
                test_board[move] = "X"
                score = self.minimax(test_board, True)
                test_board[move] = None
                best_score = min(score, best_score)
            return best_score

    def find_best_move(self):
        best_score = -1000
        best_move = -1
        for move in self.get_available_moves(self.board):
            self.board[move] = "O"
            score = self.minimax(self.board, False)
            self.board[move] = None
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def execute_ai_move(self):
        moves = self.get_available_moves(self.board)
        if not moves:
            return

        selected_move = -1

        if self.difficulty == "easy":
            # Purely random moves
            selected_move = random.choice(moves)
            
        elif self.difficulty == "medium":
            # 50% chance to execute a perfect Minimax move, otherwise pick random
            if random.random() < 0.5:
                selected_move = self.find_best_move()
            else:
                # Fallback rule: win immediately or block opponent if visible, otherwise pick random
                selected_move = self.find_tactical_move(moves)
                
        elif self.difficulty == "impossible":
            # Always choose the optimal route
            selected_move = self.find_best_move()

        if selected_move != -1:
            self.board[selected_move] = "O"
            self.cell_anim_progress[selected_move] = 0.0
            col = selected_move % 3
            row = selected_move // 3
            self.spawn_particles(col * 200 + 100, 100 + row * 200 + 100, COLOR_O, count=20)
            SOUND_O.play()
            
            winner, win_line = self.check_winner()
            if winner:
                self.trigger_win_sequence(winner, win_line)
            else:
                self.current_player = "X"
        
        self.ai_thinking = False

    def find_tactical_move(self, moves):
        # Helper to check for immediate wins/blocks
        for val in ["O", "X"]:
            for m in moves:
                self.board[m] = val
                winner, _ = self.check_winner()
                self.board[m] = None
                if winner == val:
                    return m
        return random.choice(moves)

    # --- UI Drawing Utilities ---
    def draw_button(self, text, x, y, w, h, base_color, hover_color):
        mouse_pos = pygame.mouse.get_pos()
        rect = pygame.Rect(x, y, w, h)
        is_hovered = rect.collidepoint(mouse_pos)
        
        color = hover_color if is_hovered else base_color
        pygame.draw.rect(self.screen, color, rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_MUTED, rect, width=2, border_radius=12)
        
        text_surf = FONT_SMALL.render(text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
        
        return is_hovered

    def draw_menu(self):
        self.screen.blit(self.bg_cache, (0, 0))
        
        # Subtle floating animation for title
        time_offset = math.sin(pygame.time.get_ticks() * 0.003) * 8
        
        title_text = "NEON TIC-TAC-TOE"
        glow_surf = FONT_LARGE.render(title_text, True, COLOR_X)
        text_surf = FONT_LARGE.render(title_text, True, COLOR_TEXT)
        title_rect = text_surf.get_rect(center=(WIDTH // 2, 180 + time_offset))
        
        self.screen.blit(glow_surf, title_rect.move(2, 2))
        self.screen.blit(text_surf, title_rect)
        
        sub_surf = FONT_TINY.render("SELECT GAME MODE TO BEGIN", True, COLOR_MUTED)
        sub_rect = sub_surf.get_rect(center=(WIDTH // 2, 240 + time_offset))
        self.screen.blit(sub_surf, sub_rect)
        
        self.draw_button("PLAYER vs AI (SOLO)", 150, 360, 300, 50, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("PLAYER vs PLAYER", 150, 430, 300, 50, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("EXIT GAME", 150, 500, 300, 50, COLOR_BUTTON, COLOR_BUTTON_HOVER)

    def draw_difficulty_screen(self):
        self.screen.blit(self.bg_cache, (0, 0))
        
        title_surf = FONT_LARGE.render("SELECT DIFFICULTY", True, COLOR_O)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 180))
        self.screen.blit(title_surf, title_rect)
        
        self.draw_button("EASY", 150, 290, 300, 50, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("MEDIUM", 150, 360, 300, 50, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("IMPOSSIBLE", 150, 430, 300, 50, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("BACK", 150, 510, 300, 50, (30, 33, 48), (45, 50, 70))

    def draw_gameplay(self):
        self.screen.blit(self.bg_cache, (0, 0))
        
        # --- HEADER DISPLAY ---
        score_x_surf = FONT_SMALL.render(f"X (Player): {self.scores['X']}", True, COLOR_X)
        self.screen.blit(score_x_surf, (30, 25))
        
        o_label = "AI" if self.game_mode == "vs_ai" else "Player 2"
        score_o_surf = FONT_SMALL.render(f"O ({o_label}): {self.scores['O']}", True, COLOR_O)
        self.screen.blit(score_o_surf, (30, 55))
        
        # Mode & Difficulty Label
        info_text = f"Mode: PvP"
        if self.game_mode == "vs_ai":
            info_text = f"VS AI ({self.difficulty.upper()})"
        info_surf = FONT_TINY.render(info_text, True, COLOR_MUTED)
        self.screen.blit(info_surf, (30, 80))
        
        # Turn / Action Status
        if self.winner is None:
            if self.ai_thinking:
                turn_text = "AI is thinking..."
                turn_color = COLOR_MUTED
            else:
                turn_text = f"{self.current_player}'s Turn"
                turn_color = COLOR_X if self.current_player == "X" else COLOR_O
        else:
            if self.winner == "Draw":
                turn_text = "TIE MATCH!"
                turn_color = COLOR_MUTED
            else:
                turn_text = f"{self.winner} wins!"
                turn_color = COLOR_WIN_LINE if self.winner == "X" else COLOR_O
                
        turn_surf = FONT_MEDIUM.render(turn_text, True, turn_color)
        turn_rect = turn_surf.get_rect(center=(WIDTH // 2 + 10, 50))
        self.screen.blit(turn_surf, turn_rect)
        
        # On-screen Pause Button
        self.draw_button("PAUSE", 480, 25, 90, 50, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        
        # --- THE PLAYING BOARD ---
        grid_y_offset = 100
        line_thickness = 8
        
        # Grid layout lines
        pygame.draw.line(self.screen, COLOR_GRID, (15, grid_y_offset + 200), (WIDTH - 15, grid_y_offset + 200), line_thickness)
        pygame.draw.line(self.screen, COLOR_GRID, (15, grid_y_offset + 400), (WIDTH - 15, grid_y_offset + 400), line_thickness)
        pygame.draw.line(self.screen, COLOR_GRID, (200, grid_y_offset + 15), (200, HEIGHT - 15), line_thickness)
        pygame.draw.line(self.screen, COLOR_GRID, (400, grid_y_offset + 15), (400, HEIGHT - 15), line_thickness)
        
        # Render cell elements
        for i in range(9):
            marker = self.board[i]
            if marker is not None:
                row = i // 3
                col = i % 3
                cell_left = col * 200
                cell_top = grid_y_offset + row * 200
                
                padding = 45
                x1 = cell_left + padding
                y1 = cell_top + padding
                x2 = cell_left + 200 - padding
                y2 = cell_top + 200 - padding
                
                p = self.cell_anim_progress[i]
                
                if marker == "X":
                    # Draw animated cross lines
                    if p <= 0.5:
                        seg_p = p / 0.5
                        curr_x = x1 + (x2 - x1) * seg_p
                        curr_y = y1 + (y2 - y1) * seg_p
                        pygame.draw.line(self.screen, COLOR_X, (x1, y1), (curr_x, curr_y), 12)
                    else:
                        pygame.draw.line(self.screen, COLOR_X, (x1, y1), (x2, y2), 12)
                        seg_p = (p - 0.5) / 0.5
                        curr_x = x2 - (x2 - x1) * seg_p
                        curr_y = y1 + (y2 - y1) * seg_p
                        pygame.draw.line(self.screen, COLOR_X, (x2, y1), (curr_x, curr_y), 12)
                        
                elif marker == "O":
                    # Draw animated circular arcs
                    center_x = cell_left + 100
                    center_y = cell_top + 100
                    radius = 100 - padding
                    rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
                    
                    stop_angle = p * 2 * math.pi
                    if stop_angle > 0:
                        pygame.draw.arc(self.screen, COLOR_O, rect, 0, stop_angle, 10)

        # Draw winning line animation
        if self.winning_line is not None:
            a, b, c = self.winning_line
            
            def get_center(idx):
                r = idx // 3
                cl = idx % 3
                return cl * 200 + 100, grid_y_offset + r * 200 + 100
            
            start_x, start_y = get_center(a)
            end_x, end_y = get_center(c)
            
            curr_end_x = start_x + (end_x - start_x) * self.win_line_progress
            curr_end_y = start_y + (end_y - start_y) * self.win_line_progress
            
            line_color = COLOR_WIN_LINE if self.winner == "X" else COLOR_LOSE_LINE
            pygame.draw.line(self.screen, line_color, (start_x, start_y), (curr_end_x, curr_end_y), 14)

    def draw_pause_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 11, 20, 215))
        self.screen.blit(overlay, (0, 0))
        
        card_w, card_h = 360, 360
        card_x = (WIDTH - card_w) // 2
        card_y = (HEIGHT - card_h) // 2
        pygame.draw.rect(self.screen, COLOR_BG_START, (card_x, card_y, card_w, card_h), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_MUTED, (card_x, card_y, card_w, card_h), width=3, border_radius=20)
        
        title_surf = FONT_MEDIUM.render("GAME PAUSED", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, card_y + 50))
        self.screen.blit(title_surf, title_rect)
        
        self.draw_button("RESUME PLAY", card_x + 55, card_y + 110, 250, 48, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("PLAY NEXT ROUND", card_x + 55, card_y + 180, 250, 48, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("EXIT TO MENU", card_x + 55, card_y + 250, 250, 48, COLOR_BUTTON, COLOR_BUTTON_HOVER)

    def draw_game_over_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 11, 20, 215))
        self.screen.blit(overlay, (0, 0))
        
        card_w, card_h = 380, 320
        card_x = (WIDTH - card_w) // 2
        card_y = (HEIGHT - card_h) // 2
        pygame.draw.rect(self.screen, COLOR_BG_START, (card_x, card_y, card_w, card_h), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_MUTED, (card_x, card_y, card_w, card_h), width=3, border_radius=20)
        
        # Setup specific messaging contextualized around Win/Lose/PvP conditions
        if self.winner == "Draw":
            result_title = "TIE MATCH!"
            result_subtitle = "No winners this time."
            result_color = COLOR_MUTED
        elif self.game_mode == "vs_ai":
            if self.winner == "X":
                result_title = "CONGRATULATIONS!"
                result_subtitle = "You defeated the computer!"
                result_color = COLOR_WIN_LINE
            else:
                result_title = "OOPS! YOU LOST"
                result_subtitle = "The machine wins this round."
                result_color = COLOR_LOSE_LINE
        else:
            result_title = f"'{self.winner}' VICTORIOUS!"
            result_subtitle = f"Congratulations on the win!"
            result_color = COLOR_WIN_LINE
            
        res_surf = FONT_MEDIUM.render(result_title, True, result_color)
        res_rect = res_surf.get_rect(center=(WIDTH // 2, card_y + 55))
        self.screen.blit(res_surf, res_rect)
        
        sub_surf = FONT_TINY.render(result_subtitle, True, COLOR_TEXT)
        sub_rect = sub_surf.get_rect(center=(WIDTH // 2, card_y + 90))
        self.screen.blit(sub_surf, sub_rect)
        
        self.draw_button("PLAY NEXT", card_x + 65, card_y + 140, 250, 48, COLOR_BUTTON, COLOR_BUTTON_HOVER)
        self.draw_button("EXIT NOW", card_x + 65, card_y + 210, 250, 48, COLOR_BUTTON, COLOR_BUTTON_HOVER)

    def handle_mouse_clicks(self, pos):
        x, y = pos
        
        # Menu Screen Selection Transitions
        if self.state == STATE_MENU:
            if 150 <= x <= 450:
                if 360 <= y <= 410:
                    SOUND_CLICK.play()
                    self.game_mode = "vs_ai"
                    self.state = STATE_DIFFICULTY
                elif 430 <= y <= 480:
                    SOUND_CLICK.play()
                    self.game_mode = "vs_player"
                    self.reset_board(keep_scores=False)
                    self.state = STATE_GAME
                elif 500 <= y <= 550:
                    SOUND_CLICK.play()
                    pygame.time.wait(150)
                    pygame.quit()
                    sys.exit()

        # Difficulty Menu Choice Selection
        elif self.state == STATE_DIFFICULTY:
            if 150 <= x <= 450:
                if 290 <= y <= 340:
                    SOUND_CLICK.play()
                    self.difficulty = "easy"
                    self.reset_board(keep_scores=False)
                    self.state = STATE_GAME
                elif 360 <= y <= 410:
                    SOUND_CLICK.play()
                    self.difficulty = "medium"
                    self.reset_board(keep_scores=False)
                    self.state = STATE_GAME
                elif 430 <= y <= 480:
                    SOUND_CLICK.play()
                    self.difficulty = "impossible"
                    self.reset_board(keep_scores=False)
                    self.state = STATE_GAME
                elif 510 <= y <= 560:
                    SOUND_CLICK.play()
                    self.state = STATE_MENU

        # Main Gameplay Interactive Coordinates
        elif self.state == STATE_GAME:
            if y <= 100:
                # Top Bar Area (Clicking Pause)
                if 480 <= x <= 570 and 25 <= y <= 75:
                    SOUND_CLICK.play()
                    self.state = STATE_PAUSE
            else:
                # Active 3x3 Board Intersect Calculations
                if self.winner is not None or self.ai_thinking:
                    return
                    
                col = x // 200
                row = (y - 100) // 200
                idx = row * 3 + col
                
                if self.board[idx] is None:
                    self.board[idx] = self.current_player
                    self.cell_anim_progress[idx] = 0.0
                    self.spawn_particles(x, y, COLOR_X if self.current_player == "X" else COLOR_O, count=22)
                    
                    if self.current_player == "X":
                        SOUND_X.play()
                    else:
                        SOUND_O.play()
                        
                    winner, win_line = self.check_winner()
                    if winner:
                        self.trigger_win_sequence(winner, win_line)
                    else:
                        # Toggle active players
                        if self.game_mode == "vs_ai":
                            self.current_player = "O"
                            self.ai_thinking = True
                            self.ai_timer = pygame.time.get_ticks()
                        else:
                            self.current_player = "O" if self.current_player == "X" else "X"

        # Game Paused Option Selection
        elif self.state == STATE_PAUSE:
            card_x = (WIDTH - 360) // 2
            card_y = (HEIGHT - 360) // 2
            if card_x + 55 <= x <= card_x + 305:
                if card_y + 110 <= y <= card_y + 158:
                    SOUND_CLICK.play()
                    self.state = STATE_GAME
                elif card_y + 180 <= y <= card_y + 228:
                    SOUND_CLICK.play()
                    self.reset_board(keep_scores=True)
                    self.state = STATE_GAME
                elif card_y + 250 <= y <= card_y + 298:
                    SOUND_CLICK.play()
                    self.state = STATE_MENU

        # Game Over Resolution Options
        elif self.state == STATE_GAME_OVER:
            card_x = (WIDTH - 380) // 2
            card_y = (HEIGHT - 320) // 2
            if card_x + 65 <= x <= card_x + 315:
                if card_y + 140 <= y <= card_y + 188:
                    SOUND_CLICK.play()
                    self.reset_board(keep_scores=True)
                    self.state = STATE_GAME
                elif card_y + 210 <= y <= card_y + 258:
                    SOUND_CLICK.play()
                    self.state = STATE_MENU

    # --- Core Runtime Execution ---
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # --- Input Handler ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == STATE_GAME:
                            SOUND_CLICK.play()
                            self.state = STATE_PAUSE
                        elif self.state == STATE_PAUSE:
                            SOUND_CLICK.play()
                            self.state = STATE_GAME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_clicks(event.pos)

            # --- Timed Events & AI Execution ---
            if self.state == STATE_GAME and self.ai_thinking and self.winner is None:
                current_time = pygame.time.get_ticks()
                if current_time - self.ai_timer >= self.ai_delay_ms:
                    self.execute_ai_move()

            # --- Animations & Environmental Update Cycles ---
            self.update_particles()
            
            # Shake effect decay step
            if self.shake_intensity > 0:
                self.shake_intensity = int(self.shake_intensity * 0.9)
                
            if self.state in (STATE_GAME, STATE_GAME_OVER):
                # Update cell animations
                for i in range(9):
                    if self.board[i] is not None and self.cell_anim_progress[i] < 1.0:
                        self.cell_anim_progress[i] = min(1.0, self.cell_anim_progress[i] + dt * 5.0)
                        
                # Update winning trace line
                if self.winning_line is not None:
                    if self.win_line_progress < 1.0:
                        self.win_line_progress = min(1.0, self.win_line_progress + dt * 3.5)
                        # Continuously emit bright sparks on the trace path while winning
                        a, _, c = self.winning_line
                        r_a, col_a = a // 3, a % 3
                        r_c, col_c = c // 3, c % 3
                        sx = col_a * 200 + 100 + (col_c - col_a) * 200 * self.win_line_progress
                        sy = 100 + r_a * 200 + 100 + (r_c - r_a) * 200 * self.win_line_progress
                        self.spawn_particles(sx, sy, COLOR_WIN_LINE if self.winner == "X" else COLOR_LOSE_LINE, count=2)
                    elif self.state == STATE_GAME:
                        self.state = STATE_GAME_OVER

            # --- Graphics Pipeline (Includes Render Translate Camera shake) ---
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity) if self.shake_intensity > 0 else 0
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity) if self.shake_intensity > 0 else 0
            
            # Clear drawing board or apply visual shifts if screen shake is active
            display_surf = pygame.Surface(SCREEN_SIZE)
            
            if self.state == STATE_MENU:
                self.draw_menu()
            elif self.state == STATE_DIFFICULTY:
                self.draw_difficulty_screen()
            elif self.state == STATE_GAME:
                self.draw_gameplay()
            elif self.state == STATE_PAUSE:
                self.draw_gameplay()
                self.draw_pause_overlay()
            elif self.state == STATE_GAME_OVER:
                self.draw_gameplay()
                self.draw_game_over_overlay()
            
            # Draw particle layers above base layouts
            if self.particles:
                self.draw_particles()

            # Apply camera translation offsets if necessary
            if shake_x != 0 or shake_y != 0:
                self.screen.blit(self.screen.copy(), (shake_x, shake_y))
            
            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = AdvancedTicTacToe()
    game.run()