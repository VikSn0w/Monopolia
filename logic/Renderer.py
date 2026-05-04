import os

import pygame
from pygments.styles import default

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BOARD_GREEN = (175, 225, 175)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

GROUP_COLORS = {
    "Brown": (139, 69, 19),
    "Light Blue": (173, 216, 230),
    "Pink": (255, 105, 180),
    "Orange": (255, 140, 0),
    "Red": (255, 0, 0),
    "Yellow": (220, 220, 0),
    "Green": (0, 128, 0),
    "Dark Blue": (0, 0, 139),
    "Railroad": (169, 169, 169),
    "Utility": (200, 200, 200)
}

CORNER_COLORS = {
    0: (255, 102, 102),             
    10: (255, 204, 153),               
    20: (173, 216, 230),             
    30: (211, 211, 211)              
}

CORNER_TEXTS = {
    0: "Go",
    10: "Jail",
    20: "Parking",
    30: "Go to jail"
}

PLAYER_COLORS = [
    (255, 0, 0),     # 1. Red
    (0, 0, 255),     # 2. Blue
    (0, 255, 0),     # 3. Green
    (255, 255, 0),   # 4. Yellow
    (128, 0, 128),   # 5. Purple
    (0, 255, 255),   # 6. Cyan
    (255, 165, 0),   # 7. Orange
    (255, 105, 180)  # 8. Pink
]

class MonopolyRenderer:
    def __init__(self, game_manager, screen):
        self.gm = game_manager
        self.screen = screen
        self.width, self.height = screen.get_size()
        folder_font_path = os.path.join('logic', 'assets', 'fonts')
        regular_font = os.path.join(folder_font_path, 'Kabel-Regular.otf')
        bold_font = os.path.join(folder_font_path, 'Kabel-Bold.otf')
        light_font = os.path.join(folder_font_path, 'Kabel-Light.otf')

        self.font = pygame.font.Font(regular_font, 14)
        self.large_font = pygame.font.Font(bold_font, 18)
        self.med_font = pygame.font.Font(light_font, 20)
        
                              
        self.board_size = self.height                               
        self.corner_size = self.board_size // 7
        self.space_size = (self.board_size - (2 * self.corner_size)) // 9

    def get_space_rect(self, index):
        if 0 <= index <= 10:              
            if index == 0:
                x = self.board_size - self.corner_size
            elif index == 10:
                x = 0
            else:
                x = self.board_size - self.corner_size - (index * self.space_size)
            y = self.board_size - self.corner_size
            w = self.corner_size if index in [0, 10] else self.space_size
            h = self.corner_size
        elif 11 <= index <= 19:            
            x = 0
            y = self.board_size - self.corner_size - ((index - 10) * self.space_size)
            w = self.corner_size
            h = self.space_size
        elif 20 <= index <= 30:           
            if index == 20:
                x = 0
            elif index == 30:
                x = self.board_size - self.corner_size
            else:
                x = self.corner_size + ((index - 21) * self.space_size)
            y = 0
            w = self.corner_size if index in [20, 30] else self.space_size
            h = self.corner_size
        elif 31 <= index <= 39:             
            x = self.board_size - self.corner_size
            y = self.corner_size + ((index - 31) * self.space_size)
            w = self.corner_size
            h = self.space_size
        return pygame.Rect(x, y, w, h)

    def draw_board(self):
                                             
        board_rect = pygame.Rect(0, 0, self.board_size, self.board_size)
        pygame.draw.rect(self.screen, BOARD_GREEN, board_rect)

        for i, space in enumerate(self.gm.board):
            if space is None: continue
            rect = self.get_space_rect(i)
            
                                  
            color = WHITE
            if hasattr(space, 'group') and space.group in GROUP_COLORS:
                color = GROUP_COLORS[space.group]
            if i in CORNER_COLORS:
                color = CORNER_COLORS[i]
            
                         
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)

            if hasattr(space, 'owner') and space.owner is not None:
                if space.owner in self.gm.players:
                    owner_idx = self.gm.players.index(space.owner)
                    owner_color = PLAYER_COLORS[owner_idx % len(PLAYER_COLORS)]
                else:
                    owner_color = (100, 100, 100)

                pygame.draw.rect(self.screen, owner_color, rect, 4)
                                             
            if hasattr(space, 'is_mortgaged') and space.is_mortgaged:
                s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                s.fill((0, 0, 0, 160))
                self.screen.blit(s, (rect.x, rect.y))
                
                  
            if i in CORNER_TEXTS:
                words = CORNER_TEXTS[i].split()
            else:
                words = space.name.split()
                
            for j, word in enumerate(words):
                                                              
                text_color = WHITE if hasattr(space, 'is_mortgaged') and space.is_mortgaged else BLACK
                text_surface = self.font.render(word, True, text_color)
                self.screen.blit(text_surface, (rect.x + 2, rect.y + 2 + (j * 11)))
                
                            
            if hasattr(space, 'hotel_count') and space.hotel_count > 0:
                pygame.draw.rect(self.screen, RED, (rect.x + rect.w//2 - 10, rect.y + rect.h - 15, 20, 10))
                pygame.draw.rect(self.screen, BLACK, (rect.x + rect.w//2 - 10, rect.y + rect.h - 15, 20, 10), 1)
            elif hasattr(space, 'house_count') and space.house_count > 0:
                for h in range(space.house_count):
                    pygame.draw.rect(self.screen, GREEN, (rect.x + 2 + (h * 12), rect.y + rect.h - 10, 10, 8))
                    pygame.draw.rect(self.screen, BLACK, (rect.x + 2 + (h * 12), rect.y + rect.h - 10, 10, 8), 1)

    def draw_player_token(self, color, x, y, size, shape_idx):
        match shape_idx:
            case 0:
                pygame.draw.circle(self.screen, color, (x, y), size)
                pygame.draw.circle(self.screen, BLACK, (x, y), size, 1)

            case 1:
                rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)

            case 2:
                points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, BLACK, points, 1)

            case 3:
                points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, BLACK, points, 1)

            case 4:
                points = [(x - size * 0.6, y - size), (x + size * 0.6, y - size),
                          (x + size, y + size), (x - size, y + size)]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, BLACK, points, 1)

            case 5:
                points = [(x - size * 0.5, y - size), (x + size * 0.5, y - size),
                          (x + size, y),
                          (x + size * 0.5, y + size), (x - size * 0.5, y + size),
                          (x - size, y)]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, BLACK, points, 1)

            case 6:
                points = [(x, y - size), (x + size, y - size * 0.2),
                          (x + size * 0.6, y + size), (x - size * 0.6, y + size),
                          (x - size, y - size * 0.2)]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, BLACK, points, 1)

            case 7:
                rect = pygame.Rect(x - size * 0.6, y - size, size * 1.2, size * 2)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)

            case _:
                pygame.draw.circle(self.screen, color, (x, y), size)
                pygame.draw.circle(self.screen, BLACK, (x, y), size, 1)

    def draw_players(self):
        for i, player in enumerate(self.gm.players):
            rect = self.get_space_rect(player.location)
            row = i // 4
            col = i % 4
            offset_x = rect.x + 15 + (col * 15)
            offset_y = rect.y + rect.h - 30 + (row * 15)
            color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            self.draw_player_token(color, offset_x, offset_y, 8, i % 8)

    def draw_side_panel(self):
        panel_rect = pygame.Rect(self.board_size, 0, self.width - self.board_size, self.height)
        pygame.draw.rect(self.screen, (240, 240, 240), panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)

        y_offset = 20
        for i, player in enumerate(self.gm.players):
            color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            name_text = self.large_font.render(f"{player.name} (${player.money})", True, color)
            self.screen.blit(name_text, (self.board_size + 20, y_offset))
            y_offset += 25
            
            for prop in player.owned_properties:
                prop_color = GROUP_COLORS.get(prop.group, BLACK)
                prop_str = f"- {prop.name}"
                if prop.is_mortgaged:
                    prop_str += " (M)"
                if prop.hotel_count > 0:
                    prop_str += " [Hotel]"
                elif prop.house_count > 0:
                    prop_str += f" [{prop.house_count} houses]"
                    
                text_surface = self.med_font.render(prop_str, True, prop_color)
                                                                    
                shadow = self.med_font.render(prop_str, True, BLACK)
                self.screen.blit(shadow, (self.board_size + 21, y_offset + 1))
                self.screen.blit(text_surface, (self.board_size + 20, y_offset))
                
                y_offset += 18
            
            y_offset += 20