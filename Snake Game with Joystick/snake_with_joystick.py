#!/usr/bin/env python3
"""
Snake Game with Arduino Joystick Support
"""

import pygame
import random
import sys
import time
from joystick_controller import ArduinoJoystickController

class SnakeGame:
    def __init__(self):
        pygame.init()
        self.setup_display()
        self.setup_joystick()
        self.reset_game()
    
    def setup_display(self):
        """Initialize the game display"""
        self.WINDOW_WIDTH = 800
        self.WINDOW_HEIGHT = 600
        self.GRID_SIZE = 20
        self.GRID_WIDTH = self.WINDOW_WIDTH // self.GRID_SIZE
        self.GRID_HEIGHT = self.WINDOW_HEIGHT // self.GRID_SIZE
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.GRAY = (128, 128, 128)
        
        # Create display
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Snake Game - Arduino Joystick")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def setup_joystick(self):
        """Initialize Arduino joystick controller"""
        try:
            self.joystick = ArduinoJoystickController()
            self.joystick.calibrate()
            print("Arduino joystick ready!")
            self.joystick_connected = True
        except Exception as e:
            print(f"Joystick error: {e}")
            print("Falling back to keyboard controls")
            self.joystick = None
            self.joystick_connected = False
    
    def reset_game(self):
        """Reset the game to initial state"""
        # Snake starting position (center of screen)
        start_x = self.GRID_WIDTH // 2
        start_y = self.GRID_HEIGHT // 2
        self.snake = [(start_x, start_y)]
        
        # Game state
        self.direction = 'RIGHT'
        self.next_direction = 'RIGHT'
        self.game_over = False
        self.paused = False
        self.score = 0
        
        # Create first food
        self.create_food()
        
        # Game timing
        self.last_move_time = time.time()
        self.move_delay = 0.15  # Seconds between moves
    
    def create_food(self):
        """Create food at random position"""
        while True:
            food_x = random.randint(0, self.GRID_WIDTH - 1)
            food_y = random.randint(0, self.GRID_HEIGHT - 1)
            if (food_x, food_y) not in self.snake:
                self.food = (food_x, food_y)
                break
    
    def handle_input(self):
        """Handle both joystick and keyboard input"""
        # Pygame events (window close, keyboard backup)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.toggle_pause()
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                # Keyboard backup controls
                elif not self.game_over and not self.paused:
                    if event.key == pygame.K_UP and self.direction != 'DOWN':
                        self.next_direction = 'UP'
                    elif event.key == pygame.K_DOWN and self.direction != 'UP':
                        self.next_direction = 'DOWN'
                    elif event.key == pygame.K_LEFT and self.direction != 'RIGHT':
                        self.next_direction = 'LEFT'
                    elif event.key == pygame.K_RIGHT and self.direction != 'LEFT':
                        self.next_direction = 'RIGHT'
        
        # Joystick input
        if self.joystick:
            try:
                # Direction control
                direction = self.joystick.get_direction()
                if direction and not self.game_over and not self.paused:
                    # Prevent snake from reversing into itself
                    if ((direction == 'UP' and self.direction != 'DOWN') or
                        (direction == 'DOWN' and self.direction != 'UP') or
                        (direction == 'LEFT' and self.direction != 'RIGHT') or
                        (direction == 'RIGHT' and self.direction != 'LEFT')):
                        self.next_direction = direction
                
                # Button control (pause/restart)
                if self.joystick.is_button_pressed():
                    if self.game_over:
                        self.reset_game()
                    else:
                        self.toggle_pause()
            except Exception as e:
                print(f"Joystick input error: {e}")
        
        return True
    
    def toggle_pause(self):
        """Toggle game pause state"""
        if not self.game_over:
            self.paused = not self.paused
    
    def update_game(self):
        """Update game logic"""
        if self.game_over or self.paused:
            return
        
        current_time = time.time()
        if current_time - self.last_move_time < self.move_delay:
            return
        
        # Update direction
        self.direction = self.next_direction
        
        # Move snake
        head_x, head_y = self.snake[0]
        
        if self.direction == 'UP':
            head_y -= 1
        elif self.direction == 'DOWN':
            head_y += 1
        elif self.direction == 'LEFT':
            head_x -= 1
        elif self.direction == 'RIGHT':
            head_x += 1
        
        # Check wall collision
        if (head_x < 0 or head_x >= self.GRID_WIDTH or 
            head_y < 0 or head_y >= self.GRID_HEIGHT):
            self.game_over = True
            return
        
        # Check self collision
        if (head_x, head_y) in self.snake:
            self.game_over = True
            return
        
        # Add new head
        self.snake.insert(0, (head_x, head_y))
        
        # Check food collision
        if (head_x, head_y) == self.food:
            self.score += 10
            self.create_food()
            # Increase speed slightly
            self.move_delay = max(0.08, self.move_delay * 0.98)
        else:
            # Remove tail if no food eaten
            self.snake.pop()
        
        self.last_move_time = current_time
    
    def draw(self):
        """Draw the game"""
        self.screen.fill(self.BLACK)
        
        # Draw snake
        for segment in self.snake:
            x = segment[0] * self.GRID_SIZE
            y = segment[1] * self.GRID_SIZE
            pygame.draw.rect(self.screen, self.GREEN, 
                           (x, y, self.GRID_SIZE, self.GRID_SIZE))
            pygame.draw.rect(self.screen, self.WHITE, 
                           (x, y, self.GRID_SIZE, self.GRID_SIZE), 1)
        
        # Draw food
        food_x = self.food[0] * self.GRID_SIZE
        food_y = self.food[1] * self.GRID_SIZE
        pygame.draw.rect(self.screen, self.RED, 
                        (food_x, food_y, self.GRID_SIZE, self.GRID_SIZE))
        
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Draw joystick status
        status_color = self.GREEN if self.joystick_connected else self.RED
        status_text = "Joystick: Connected" if self.joystick_connected else "Joystick: Disconnected"
        joystick_text = self.small_font.render(status_text, True, status_color)
        self.screen.blit(joystick_text, (10, 50))
        
        # Draw joystick values for debugging
        if self.joystick:
            try:
                values = self.joystick.get_raw_values()
                debug_text = f"X: {values['x']:.2f} Y: {values['y']:.2f} Btn: {values['button']}"
                debug_surface = self.small_font.render(debug_text, True, self.GRAY)
                self.screen.blit(debug_surface, (10, 75))
            except:
                pass
        
        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(self.BLACK)
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("GAME OVER", True, self.RED)
            final_score_text = self.font.render(f"Final Score: {self.score}", True, self.WHITE)
            restart_text = self.small_font.render("Press Joystick Button or R to Restart", True, self.WHITE)
            
            # Center the text
            game_over_rect = game_over_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2 - 50))
            score_rect = final_score_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
            restart_rect = restart_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2 + 50))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(final_score_text, score_rect)
            self.screen.blit(restart_text, restart_rect)
        
        # Draw pause screen
        elif self.paused:
            overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(self.BLACK)
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.font.render("PAUSED", True, self.BLUE)
            continue_text = self.small_font.render("Press Joystick Button or Space to Continue", True, self.WHITE)
            
            pause_rect = pause_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2 - 25))
            continue_rect = continue_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2 + 25))
            
            self.screen.blit(pause_text, pause_rect)
            self.screen.blit(continue_text, continue_rect)
        
        # Draw controls
        controls_text = [
            "Controls:",
            "Joystick: Move to control snake, press button to pause/restart",
            "Keyboard: Arrow keys to move, Space to pause, R to restart, Esc to quit"
        ]
        
        for i, text in enumerate(controls_text):
            color = self.WHITE if i == 0 else self.GRAY
            text_surface = self.small_font.render(text, True, color)
            self.screen.blit(text_surface, (10, self.WINDOW_HEIGHT - 80 + i * 20))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            running = self.handle_input()
            self.update_game()
            self.draw()
            self.clock.tick(60)  # 60 FPS
    
    def cleanup(self):
        """Clean up resources"""
        if self.joystick:
            self.joystick.close()
        pygame.quit()

def main():
    try:
        game = SnakeGame()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted")
    except Exception as e:
        print(f"Game error: {e}")
    finally:
        if 'game' in locals():
            game.cleanup()

if __name__ == "__main__":
    main()
