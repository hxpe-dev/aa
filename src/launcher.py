import pygame
import sys
import socket
from settings import *
from network.network_manager import NetworkMode
from core.game import MultiplayerGame


def get_local_ip():
    # Obtenir l'adresse IP locale de la machine
    
    # (SOLUTION PAR stackoverflow.com)
    try:
        # Connect to a public DNS to determine route 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            # Fallback: get hostname and resolve it
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"


class Launcher:
    def __init__(self, screen):
        self.screen = screen
        self.background = pygame.image.load("assets/background.jpg").convert()
        self.background = pygame.transform.scale(
            self.background, (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.running = True
        self.selected = 0  # 0=Offline, 1=Server, 2=Client, 3=Settings
        self.settings_selected = 0
        self.music_volume = 0.5
        self.settings_res_selected = 3 #1920x960 par defaut
        self.show_res_in_settings = False
        self.RESOLUTIONS = [(960, 480), (1280, 640), (1600, 800), (1920, 960), None]
        self.client_ip_input = ""
        self.mode = None
        self.local_ip = get_local_ip()

        pygame.mixer.music.load("assets/main_theme.mp3")
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1)  # -1 = infinite loop
    
    def handle_events(self):
        # Gère les événements du launcher
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return None
            
            elif event.type == pygame.KEYDOWN:
                # Main menu navigation
                if self.mode is None:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % 4
                    
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % 4
                    
                    elif event.key == pygame.K_RETURN:
                        if self.selected == 0:  # Offline
                            return NetworkMode.OFFLINE
                        elif self.selected == 1:  # Server
                            return NetworkMode.SERVER
                        elif self.selected == 2:  # Client
                            self.mode = "input_ip"
                            pygame.key.set_text_input_rect(pygame.Rect(300, 350, 600, 50))
                        elif self.selected == 3:  # Settings
                            self.mode = "settings"
                    
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                        return None
                
                # IP input screen
                elif self.mode == "input_ip":
                    if event.key == pygame.K_RETURN:
                        if self.client_ip_input and len(self.client_ip_input.split('.')) == 4:
                            return ('client', self.client_ip_input)
                        # Otherwise keep the input screen
                    
                    elif event.key == pygame.K_BACKSPACE:
                        self.client_ip_input = self.client_ip_input[:-1]
                    
                    elif event.key == pygame.K_ESCAPE:
                        self.mode = None
                        self.client_ip_input = ""

                elif self.mode == "settings":
                    if not self.show_res_in_settings:
                        if event.key == pygame.K_ESCAPE:
                            self.mode = None
                        elif event.key == pygame.K_UP:
                            self.settings_selected = (self.settings_selected - 1) % 3
                        elif event.key == pygame.K_DOWN:
                            self.settings_selected = (self.settings_selected + 1) % 3
                        elif event.key == pygame.K_LEFT:
                            if self.settings_selected == 1:
                                self.music_volume = round(max(0.0, self.music_volume - 0.1), 1)
                                pygame.mixer.music.set_volume(self.music_volume)
                        elif event.key == pygame.K_RIGHT:
                            if self.settings_selected == 1:
                                self.music_volume = round(min(1.0, self.music_volume + 0.1), 1)
                                pygame.mixer.music.set_volume(self.music_volume)
                        elif event.key == pygame.K_RETURN:
                            if self.settings_selected == 0:
                                self.show_res_in_settings = True
                            elif self.settings_selected == 2:
                                self.mode = None
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.show_res_in_settings = False
                        elif event.key == pygame.K_UP:
                            self.settings_res_selected = (self.settings_res_selected - 1) % len(self.RESOLUTIONS)
                        elif event.key == pygame.K_DOWN:
                            self.settings_res_selected = (self.settings_res_selected + 1) % len(self.RESOLUTIONS)
                        elif event.key == pygame.K_RETURN:
                            self.show_res_in_settings = False
                            res = self.RESOLUTIONS[self.settings_res_selected]
                            if res is None:
                                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            else:
                                self.screen = pygame.display.set_mode(res)
                                self.background = pygame.transform.scale(
                                    pygame.image.load("assets/background.jpg").convert(),
                                    res
                                )
            
            elif event.type == pygame.TEXTINPUT and self.mode == "input_ip":
                # Handle text input for IP
                if event.text.isdigit() or event.text == '.':
                    if len(self.client_ip_input) < 15:
                        self.client_ip_input += event.text
        
        return None
    
    def draw_main_menu(self):
        # Dessine le menu principal

        sw = self.screen.get_width()
        sh = self.screen.get_height()
        scale = min(sw / WINDOW_WIDTH, sh / WINDOW_HEIGHT)
        font_large = pygame.font.Font(None, max(16, int(48 * scale)))
        font_medium = pygame.font.Font(None, max(12, int(36 * scale)))
        font_small = pygame.font.Font(None, max(10, int(24 * scale)))
        cx = sw // 2

        self.screen.blit(self.background, (0, 0))
        
        # Title
        title = font_large.render("ABYSSAL ASCENSION", True, WHITE)
        title_rect = title.get_rect(center=(cx, int(80 * scale)))
        self.screen.blit(title, title_rect)
        
        # Your IP Address (helpful for server)
        ip_info = font_small.render(f"Your IP: {self.local_ip}", True, GREEN)
        ip_rect = ip_info.get_rect(center=(cx, int(140 * scale)))
        self.screen.blit(ip_info, ip_rect)
        
        # Menu options
        options = [
            ("OFFLINE", "Play alone (no network)"),
            ("HOST SERVER", f"Share this IP with others: {self.local_ip}"),
            ("JOIN SERVER", "Enter another player's IP address"),
            ("PARAMETRES",   "Resolution, volume..."),
        ]
        
        start_y = int(280 * scale)
        for i, (option, description) in enumerate(options):
            color = WHITE if i == self.selected else GRAY
            
            # Option text
            option_text = font_medium.render(option, True, color)
            option_rect = option_text.get_rect(center=(cx, start_y + int(i * 110 * scale)))
            self.screen.blit(option_text, option_rect)
            
            # Description
            desc_text = font_small.render(description, True, color)
            desc_rect = desc_text.get_rect(center=(cx, start_y + int(i * 110 * scale) + int(45 * scale)))
            self.screen.blit(desc_text, desc_rect)

        pygame.display.flip()
    
    def draw_ip_input(self):
        # Dessine l'écran de saisie IP

        sw = self.screen.get_width()
        sh = self.screen.get_height()
        scale = min(sw / WINDOW_WIDTH, sh / WINDOW_HEIGHT)
        font_large = pygame.font.Font(None, max(16, int(48 * scale)))
        font_medium = pygame.font.Font(None, max(12, int(36 * scale)))
        font_small = pygame.font.Font(None, max(10, int(24 * scale)))
        cx = sw // 2

        self.screen.blit(self.background, (0, 0))

        # Title
        title = font_large.render("Enter Server IP", True, WHITE)
        title_rect = title.get_rect(center=(cx, int(150 * scale)))
        self.screen.blit(title, title_rect)
        
        # Help text
        help_text = font_small.render("Find your server IP using: ipconfig", True, GRAY)
        help_rect = help_text.get_rect(center=(cx, int(220 * scale)))
        self.screen.blit(help_text, help_rect)
        
        # Input box
        input_box_width = int(500 * scale)
        input_box_height = int(60 * scale)
        input_box = pygame.Rect(
            cx - input_box_width // 2,
            int(320 * scale),
            input_box_width,
            input_box_height
        )
        
        # Draw box with thicker border to show it's active
        pygame.draw.rect(self.screen, WHITE, input_box, 3)
        pygame.draw.rect(self.screen, (int(50 * scale), int(50 * scale), int(50 * scale)), input_box)
        
        # Display input text
        if self.client_ip_input:
            display_text = self.client_ip_input
            text_color = WHITE
        else:
            display_text = "Type IP (e.g., 192.168.1.100)"
            text_color = DARK_GRAY
        
        input_text = font_medium.render(display_text, True, text_color)
        text_rect = input_text.get_rect(center=input_box.center)
        self.screen.blit(input_text, text_rect)
        
        # Cursor
        if self.client_ip_input:
            cursor_x = text_rect.x + input_text.get_width() + int(5 * scale)
            pygame.draw.line(self.screen, WHITE, (cursor_x, input_box.top + int(10 * scale)), (cursor_x, input_box.bottom - int(10 * scale)), int(2 * scale))
        
        # Status/Instructions
        status_y = int(450 * scale)
        status_lines = [
            "Type the IP address of the server computer",
            "Example: 192.168.1.100 or 192.168.0.50",
            "",
            "Current input: " + (self.client_ip_input if self.client_ip_input else "(empty)")
        ]
        
        if self.client_ip_input and len(self.client_ip_input.split('.')) == 4:
            try:
                # Check if it looks like a valid IP
                parts = self.client_ip_input.split('.')
                if all(0 <= int(p) <= 255 for p in parts):
                    status_lines.append("Valid IP format - Press RETURN to connect")
                else:
                    status_lines.append("Invalid IP range - Press RETURN anyway to try :)")
            except:
                status_lines.append("Invalid IP format - adjust and try again")
        
        for i, line in enumerate(status_lines):
            color = WHITE 
            if not "connect" in line and "Invalid" in line:
                color = YELLOW
            elif not "connect" in line:
                color = GRAY
            status_text = font_small.render(line, True, color)
            status_rect = status_text.get_rect(center=(cx, status_y + int(i * 35 * scale)))
            self.screen.blit(status_text, status_rect)
        
        pygame.display.flip()

    def draw_settings(self):
        self.screen.blit(self.background, (0, 0))
        sw = self.screen.get_width()
        sh = self.screen.get_height()
        cx = sw // 2
        cy = sh // 2

        title = self.font_large.render("PARAMETRES", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(cx, 150)))

        if not self.show_res_in_settings:
            res_txt = "Resolution : Plein ecran"
            if self.RESOLUTIONS[self.settings_res_selected]:
                res_txt = f"Resolution : {self.RESOLUTIONS[self.settings_res_selected][0]}x{self.RESOLUTIONS[self.settings_res_selected][1]}"
            items = [
                res_txt,
                f"Volume musique : {int(self.music_volume * 100)}%",
                "Retour",
            ]
            for i, label in enumerate(items):
                color = YELLOW
                if i != self.settings_selected:
                    color = WHITE
                text = self.font_medium.render(label, True, color)
                self.screen.blit(text, text.get_rect(center=(cx, cy + i * 80)))
        else:
            sub = self.font_medium.render("Choisir une resolution :", True, WHITE)
            self.screen.blit(sub, sub.get_rect(center=(cx, cy - 100)))
            for i, res in enumerate(self.RESOLUTIONS):
                color = YELLOW
                if i != self.settings_res_selected:
                    color = WHITE
                label = "Plein ecran"
                if res:
                    label = f"{res[0]}x{res[1]}"
                text = self.font_medium.render(label, True, color)
                self.screen.blit(text, text.get_rect(center=(cx, cy - 30 + i * 55)))

        pygame.display.flip()
    
    def run(self):
        # Run le launcher
        while self.running:
            if self.mode == "input_ip":
                self.draw_ip_input()
                result = self.handle_events()
            elif self.mode == "settings":
                self.draw_settings()
                result = self.handle_events()
            else:
                self.draw_main_menu()
                result = self.handle_events()
            
            if result is not None:
                return result
            
            self.clock.tick(60)
        
        return None


def launch_game():
    # Lance le launcher et démarre le jeu en fonction du choix de l'utilisateur
    pygame.init()
    icon = pygame.image.load('assets/icon.png')
    pygame.display.set_icon(icon)
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Abyssal Ascension - Multiplayer")
    
    launcher = Launcher(screen)
    result = launcher.run()
    # pygame.mixer.music.stop() # <- stop la musique du menu TUDUTUUTU
    
    if result is None:
        pygame.quit()
        sys.exit()
    
    # Handle different result types
    if isinstance(result, NetworkMode):
        game = MultiplayerGame(screen, network_mode=result)
        game.run()
    elif isinstance(result, tuple) and result[0] == 'client':
        mode, server_ip = result
        game = MultiplayerGame(screen, network_mode=NetworkMode.CLIENT)
        if not game.connect_as_client(server_ip):
            print(f"Failed to connect to {server_ip}")
        else:
            game.run()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    launch_game()
