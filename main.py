import pygame
import os
from logic.GameManager import GameManager
from logic.Player import Player
from logic.Bot import Bot
from logic.RLBot import RLBot
from logic.Renderer import MonopolyRenderer

pygame.init()
WIDTH, HEIGHT = 1100, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Monopolia")

folder_font_path = os.path.join('logic', 'assets', 'fonts')
regular_font = os.path.join(folder_font_path, 'Kabel-Regular.otf')
bold_font = os.path.join(folder_font_path, 'Kabel-Bold.otf')
light_font = os.path.join(folder_font_path, 'Kabel-Light.otf')

font = pygame.font.Font(bold_font, 20)
small_font = pygame.font.Font(light_font, 16)
large_font = pygame.font.Font(bold_font, 48)

def draw_button(rect, text, color, text_color=(0,0,0)):
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (0,0,0), rect, 2)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


app_state = "MENU"


loc_path = os.path.join('loc')
available_locs = [d for d in os.listdir(loc_path) if os.path.isdir(os.path.join(loc_path, d))] if os.path.exists(loc_path) else ['en-us']
if len(available_locs) == 0:
    available_locs = ['en-us']
selected_loc_idx = 0

menu_players = [
    {"type": "Human", "name": "Player 1", "diff": 1},
    {"type": "Bot", "name": "Bot Easy", "diff": 1},
    {"type": "Bot", "name": "Bot Hard", "diff": 3}
]


gm = None
renderer = None


board_center_x = 400
board_center_y = 400

roll_btn = pygame.Rect(board_center_x - 60, board_center_y - 25, 120, 50)
buy_btn = pygame.Rect(board_center_x - 110, board_center_y + 20, 100, 50)
pass_btn = pygame.Rect(board_center_x + 10, board_center_y + 20, 100, 50)
trade_btn = pygame.Rect(board_center_x + 130, board_center_y - 25, 100, 50)
accept_btn = pygame.Rect(board_center_x - 110, board_center_y + 40, 100, 50)
decline_btn = pygame.Rect(board_center_x + 10, board_center_y + 40, 100, 50)

bid_1_btn = pygame.Rect(board_center_x - 130, board_center_y + 30, 60, 40)
bid_10_btn = pygame.Rect(board_center_x - 60, board_center_y + 30, 60, 40)
bid_100_btn = pygame.Rect(board_center_x + 10, board_center_y + 30, 60, 40)
fold_btn = pygame.Rect(board_center_x + 80, board_center_y + 30, 60, 40)

bankruptcy_btn = pygame.Rect(board_center_x - 80, board_center_y + 50, 160, 40)


loc_prev_btn = pygame.Rect(WIDTH//2 - 150, 150, 40, 40)
loc_next_btn = pygame.Rect(WIDTH//2 + 110, 150, 40, 40)
add_human_btn = pygame.Rect(WIDTH//2 - 200, 600, 120, 50)
add_bot_btn = pygame.Rect(WIDTH//2 - 60, 600, 120, 50)
# add_rlbot_btn = pygame.Rect(WIDTH//2 + 80, 600, 120, 50)
start_btn = pygame.Rect(WIDTH//2 - 100, 700, 200, 60)

def start_game():
    global gm, renderer, app_state

    players = []
    for i, p in enumerate(menu_players):
        if p["type"] == "Human":
            players.append(Player(p["name"]))
        elif p["type"] == "Bot":
            players.append(Bot(p["name"], difficulty=p["diff"]))
        elif p["type"] == "RLBot":
            players.append(RLBot(p["name"], difficulty=p["diff"]))

    if len(players) < 2:
        return

    loc = available_locs[selected_loc_idx]
    base_p = os.path.join('loc', loc)

    prop_path = os.path.join(base_p, 'properties.json')
    board_path = os.path.join(base_p, 'board.json')
    chance_path = os.path.join(base_p, 'chance.json')
    chest_path = os.path.join(base_p, 'community-chest.json')

    gm = GameManager(players, prop_path, board_path, chance_path, chest_path)
    renderer = MonopolyRenderer(gm, screen)
    app_state = "GAME"

last_bot_action_time = 0
BOT_DELAY_MS = 1500

running = True
while running:
    current_time = pygame.time.get_ticks()
    pygame.time.delay(16)

    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if app_state == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if loc_prev_btn.collidepoint(mouse_pos):
                    selected_loc_idx = (selected_loc_idx - 1) % len(available_locs)
                elif loc_next_btn.collidepoint(mouse_pos):
                    selected_loc_idx = (selected_loc_idx + 1) % len(available_locs)
                elif add_human_btn.collidepoint(mouse_pos):
                    if len(menu_players) < 8:
                        menu_players.append({"type": "Human", "name": f"Human {len(menu_players)+1}", "diff": 1})
                elif add_bot_btn.collidepoint(mouse_pos):
                    if len(menu_players) < 8:
                        menu_players.append({"type": "Bot", "name": f"Bot {len(menu_players)+1}", "diff": 2})
                # elif add_rlbot_btn.collidepoint(mouse_pos):
                   # if len(menu_players) < 8:
                       # menu_players.append({"type": "RLBot", "name": f"RLBot {len(menu_players)+1}", "diff": 1})
                elif start_btn.collidepoint(mouse_pos):
                    start_game()
                else:
                    start_y = 250
                    for i, p in enumerate(menu_players):
                        row_rect = pygame.Rect(WIDTH//2 - 250, start_y + i*40, 500, 35)

                        del_btn = pygame.Rect(WIDTH//2 + 210, start_y + i*40 + 2, 30, 30)
                        if del_btn.collidepoint(mouse_pos):
                            menu_players.pop(i)
                            break

                        if p["type"] in ["Bot", "RLBot"]:
                            diff_down = pygame.Rect(WIDTH//2 + 50, start_y + i*40 + 2, 30, 30)
                            diff_up = pygame.Rect(WIDTH//2 + 130, start_y + i*40 + 2, 30, 30)
                            if diff_down.collidepoint(mouse_pos) and p["diff"] > 1:
                                p["diff"] -= 1
                            elif diff_up.collidepoint(mouse_pos) and p["diff"] < 4:
                                p["diff"] += 1

        elif app_state == "GAME":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and gm.state == "WAITING_FOR_ROLL":
                    if not isinstance(gm.get_current_player(), Bot):
                        gm.execute_roll_action()

            if event.type == pygame.MOUSEBUTTONDOWN:
                match(gm.state):
                    case "WAITING_FOR_ROLL":
                        if not isinstance(gm.get_current_player(), (Bot, RLBot)) and roll_btn.collidepoint(mouse_pos):
                            gm.execute_roll_action()

                    case "WAITING_FOR_BUY":
                        if not isinstance(gm.pending_player, (Bot, RLBot)):
                            if buy_btn.collidepoint(mouse_pos):
                                gm.execute_buy_decision(True)
                            elif pass_btn.collidepoint(mouse_pos):
                                gm.execute_buy_decision(False)

                    case "WAITING_FOR_AUCTION":
                        current_bidder = gm.auction_active_players[gm.auction_current_player_idx]
                        if not isinstance(current_bidder, (Bot, RLBot)):
                            if fold_btn.collidepoint(mouse_pos):
                                gm.execute_auction_bid(current_bidder, 0, True)
                            elif bid_1_btn.collidepoint(mouse_pos):
                                gm.execute_auction_bid(current_bidder, gm.auction_highest_bid + 1, False)
                            elif bid_10_btn.collidepoint(mouse_pos):
                                gm.execute_auction_bid(current_bidder, gm.auction_highest_bid + 10, False)
                            elif bid_100_btn.collidepoint(mouse_pos):
                                gm.execute_auction_bid(current_bidder, gm.auction_highest_bid + 100, False)

                    case "WAITING_FOR_DEBT_RESOLUTION":
                        if not isinstance(gm.debtor, (Bot, RLBot)):
                            if bankruptcy_btn.collidepoint(mouse_pos):
                                gm.declare_bankruptcy(gm.debtor)

                    case "WAITING_FOR_TRADE_RESPONSE":
                        if not isinstance(gm.trade_recipient, (Bot, RLBot)):
                            if accept_btn.collidepoint(mouse_pos):
                                gm.execute_trade(True)
                            elif decline_btn.collidepoint(mouse_pos):
                                gm.execute_trade(False)

    if app_state == "MENU":
        screen.fill((175, 225, 175))


        title_surf = large_font.render("MONOPOLIA", True, (0,0,0))
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, 80)))


        draw_button(loc_prev_btn, "<", (200,200,200))
        draw_button(loc_next_btn, ">", (200,200,200))
        loc_text = font.render(f"Localization: {available_locs[selected_loc_idx]}", True, (0,0,0))
        screen.blit(loc_text, loc_text.get_rect(center=(WIDTH//2, 170)))


        start_y = 250
        for i, p in enumerate(menu_players):
            row_rect = pygame.Rect(WIDTH//2 - 250, start_y + i*40, 500, 35)
            pygame.draw.rect(screen, (240,240,240), row_rect)
            pygame.draw.rect(screen, (0,0,0), row_rect, 1)

            p_text = font.render(f"{p['name']} ({p['type']})", True, (0,0,0))
            screen.blit(p_text, (WIDTH//2 - 240, start_y + i*40 + 5))

            if p["type"] in ["Bot", "RLBot"]:
                diff_down = pygame.Rect(WIDTH//2 + 50, start_y + i*40 + 2, 30, 30)
                diff_up = pygame.Rect(WIDTH//2 + 130, start_y + i*40 + 2, 30, 30)
                draw_button(diff_down, "-", (200,200,200))
                draw_button(diff_up, "+", (200,200,200))
                diff_text = font.render(f"Lv {p['diff']}", True, (0,0,0))
                screen.blit(diff_text, diff_text.get_rect(center=(WIDTH//2 + 105, start_y + i*40 + 17)))

            del_btn = pygame.Rect(WIDTH//2 + 210, start_y + i*40 + 2, 30, 30)
            draw_button(del_btn, "X", (255,100,100))


        draw_button(add_human_btn, "+ Human", (200, 255, 200))
        draw_button(add_bot_btn, "+ Bot", (200, 200, 255))
        # draw_button(add_rlbot_btn, "+ RL Bot", (255, 200, 255))


        if len(menu_players) >= 2:
            draw_button(start_btn, "START GAME", (100, 255, 100))
        else:
            draw_button(start_btn, "Need 2 Players", (150, 150, 150))

        pygame.display.flip()

    elif app_state == "GAME":

        bot_needs_to_act = False
        active_bot = None

        match(gm.state):
            case "WAITING_FOR_ROLL":
                if isinstance(gm.get_current_player(), (Bot, RLBot)):
                    bot_needs_to_act = True
                    active_bot = gm.get_current_player()
            case "WAITING_FOR_BUY":
                if isinstance(gm.pending_player, (Bot, RLBot)):
                    bot_needs_to_act = True
                    active_bot = gm.pending_player
            case "WAITING_FOR_AUCTION":
                if len(gm.auction_active_players) > 0:
                    current_bidder = gm.auction_active_players[gm.auction_current_player_idx]
                    if isinstance(current_bidder, (Bot, RLBot)):
                        bot_needs_to_act = True
                        active_bot = current_bidder
            case "WAITING_FOR_DEBT_RESOLUTION":
                if isinstance(gm.debtor, (Bot, RLBot)):
                    bot_needs_to_act = True
                    active_bot = gm.debtor

        if bot_needs_to_act and current_time - last_bot_action_time > BOT_DELAY_MS:
            active_bot.make_decision(gm)
            last_bot_action_time = current_time


        renderer.draw_board()
        renderer.draw_players()
        renderer.draw_side_panel()

        if gm.last_roll is not None:
            roll_text = font.render(f"Last Roll: {gm.last_roll[0]} and {gm.last_roll[1]}", True, (0, 0, 0))
            screen.blit(roll_text, roll_text.get_rect(center=(board_center_x, board_center_y - 120)))


        match(gm.state):
            case "WAITING_FOR_ROLL":
                if not isinstance(gm.get_current_player(), (Bot, RLBot)):
                    draw_button(roll_btn, "Roll Dice", (200, 200, 200))

            case "WAITING_FOR_BUY":
                prop = gm.pending_space
                panel = pygame.Rect(board_center_x - 150, board_center_y - 80, 300, 180)
                pygame.draw.rect(screen, (255, 255, 255), panel)
                pygame.draw.rect(screen, (0, 0, 0), panel, 3)

                text1 = font.render(f"Buy {prop.name}?", True, (0, 0, 0))
                text2 = font.render(f"Price: ${prop.price}", True, (0, 0, 0))
                screen.blit(text1, text1.get_rect(center=(board_center_x, board_center_y - 40)))
                screen.blit(text2, text2.get_rect(center=(board_center_x, board_center_y - 10)))

                if not isinstance(gm.pending_player, (Bot, RLBot)):
                    draw_button(buy_btn, "Buy", (100, 255, 100))
                    draw_button(pass_btn, "Pass", (255, 100, 100))

            case "WAITING_FOR_AUCTION":
                prop = gm.auction_property
                panel = pygame.Rect(board_center_x - 180, board_center_y - 100, 360, 200)
                pygame.draw.rect(screen, (255, 255, 255), panel)
                pygame.draw.rect(screen, (0, 0, 0), panel, 3)

                curr_bidder = gm.auction_active_players[gm.auction_current_player_idx].name

                text1 = font.render(f"Auction: {prop.name}", True, (0, 0, 0))
                text2 = small_font.render(f"Highest Bid: ${gm.auction_highest_bid} ({gm.auction_highest_bidder.name if gm.auction_highest_bidder else 'None'})", True, (0, 0, 0))
                text3 = font.render(f"{curr_bidder}'s turn to bid:", True, (0, 0, 255))

                screen.blit(text1, text1.get_rect(center=(board_center_x, board_center_y - 70)))
                screen.blit(text2, text2.get_rect(center=(board_center_x, board_center_y - 40)))
                screen.blit(text3, text3.get_rect(center=(board_center_x, board_center_y - 10)))

                current_bidder_obj = gm.auction_active_players[gm.auction_current_player_idx]
                if not isinstance(current_bidder_obj, (Bot, RLBot)):
                    draw_button(bid_1_btn, "+ $1", (200, 200, 255))
                    draw_button(bid_10_btn, "+ $10", (200, 200, 255))
                    draw_button(bid_100_btn, "+ $100", (200, 200, 255))
                    draw_button(fold_btn, "Fold", (255, 100, 100))

            case "WAITING_FOR_DEBT_RESOLUTION":
                panel = pygame.Rect(board_center_x - 150, board_center_y - 80, 300, 180)
                pygame.draw.rect(screen, (255, 200, 200), panel)
                pygame.draw.rect(screen, (255, 0, 0), panel, 3)

                text1 = font.render(f"{gm.debtor.name} is in DEBT! 🚨", True, (255, 0, 0))
                text2 = small_font.render(f"Owes {-gm.debtor.money} to {gm.creditor.name if gm.creditor else 'Bank'}", True, (0, 0, 0))

                screen.blit(text1, text1.get_rect(center=(board_center_x, board_center_y - 40)))
                screen.blit(text2, text2.get_rect(center=(board_center_x, board_center_y - 10)))

                if not isinstance(gm.debtor, (Bot, RLBot)):
                    draw_button(bankruptcy_btn, "Declare Bankruptcy", (255, 100, 100))

            case "WAITING_FOR_TRADE_RESPONSE":
                panel = pygame.Rect(board_center_x - 180, board_center_y - 100, 360, 200)
                pygame.draw.rect(screen, (255, 255, 255), panel)
                pygame.draw.rect(screen, (0, 0, 0), panel, 3)

                offer = gm.trade_offer
                text1 = font.render(f"Trade from {gm.trade_proposer.name}!", True, (0, 0, 0))

                give_str = f"Offering: {offer['give_cash']} + {len(offer['give_props'])} Props"
                req_str = f"Wants: {offer['receive_cash']} + {len(offer['receive_props'])} Props"

                text2 = small_font.render(give_str, True, (0, 100, 0))
                text3 = small_font.render(req_str, True, (100, 0, 0))
                text4 = small_font.render("(Check console for exact properties)", True, (100, 100, 100))

                screen.blit(text1, text1.get_rect(center=(board_center_x, board_center_y - 70)))
                screen.blit(text2, text2.get_rect(center=(board_center_x, board_center_y - 35)))
                screen.blit(text3, text3.get_rect(center=(board_center_x, board_center_y - 15)))
                screen.blit(text4, text4.get_rect(center=(board_center_x, board_center_y + 10)))

                if not isinstance(gm.trade_recipient, (Bot, RLBot)):
                    draw_button(accept_btn, "Accept", (100, 255, 100))
                    draw_button(decline_btn, "Decline", (255, 100, 100))

            case "GAME_OVER":
                panel = pygame.Rect(board_center_x - 150, board_center_y - 60, 300, 120)
                pygame.draw.rect(screen, (200, 255, 200), panel)
                pygame.draw.rect(screen, (0, 255, 0), panel, 3)
                text1 = font.render(f"🎉 {gm.players[0].name} WINS! 🎉", True, (0, 100, 0))
                screen.blit(text1, text1.get_rect(center=(board_center_x, board_center_y)))

        pygame.display.flip()

pygame.quit()