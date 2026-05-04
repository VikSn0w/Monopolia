import json
import random
from logic.Player import Player
from logic.Property import Property
from logic.Deck import Deck


class SpecialSpace:

    def __init__(self, data):
        self.location = data.get("location")
        self.name = data.get("name")
        self.type = data.get("type")
        self.amount = data.get("amount", 0)


def load_json(path):
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


class GameManager:
    def __init__(self, players: list[Player], properties_path: str, board_path: str, chance_path: str, chest_path: str):
        self.players = players
        self.house_count = 32
        self.hotel_count = 12

        self.chance_deck = Deck("Chance", load_json(chance_path))
        self.community_chest_deck = Deck("Community Chest", load_json(chest_path))

        properties_data = load_json(properties_path)
        special_spaces_data = load_json(board_path)

        self.board = [None] * 40
        self.group_sizes = {}

        for prop_data in properties_data:
            prop = Property(prop_data)
            self.board[prop.location] = prop
            if prop.type == "street":
                self.group_sizes[prop.group] = self.group_sizes.get(prop.group, 0) + 1

        for space_data in special_spaces_data:
            space = SpecialSpace(space_data)
            self.board[space.location] = space

        self.current_player_idx = 0
        self.state = "WAITING_FOR_ROLL"
        self.pending_player = None
        self.pending_space = None
        self.doubles_count = 0
        self.last_roll = None

        self.auction_property = None
        self.auction_highest_bid = 0
        self.auction_highest_bidder = None
        self.auction_active_players = []
        self.auction_current_player_idx = 0

        self.debtor = None
        self.creditor = None
        self.state_before_debt = None

        self.trade_proposer = None
        self.trade_recipient = None
        self.trade_offer = None  # dict: give_props, give_cash, give_goojf,
        #       receive_props, receive_cash, receive_goojf
        self.state_before_trade = None

    def get_current_player(self):
        return self.players[self.current_player_idx]

    def next_player(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.state = "WAITING_FOR_ROLL"
        self.doubles_count = 0

    def roll_dice(self):
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        return die1, die2, die1 + die2, die1 == die2

    def execute_roll_action(self):
        if self.state != "WAITING_FOR_ROLL":
            return

        player = self.get_current_player()
        print(f"\n--- {player.name}'s Turn ---")

        d1, d2, total, is_double = self.roll_dice()
        self.last_roll = (d1, d2)
        print(f"{player.name} rolled {d1} and {d2} (Total: {total}).")

        if player.is_in_jail:
            self.handle_jail_turn(player, is_double, total)
            if player.is_in_jail:
                self.next_player()
            return

        if is_double:
            self.doubles_count += 1
            print("Doubles!")
            if self.doubles_count == 3:
                print("Speeding! 3 doubles in a row. Go directly to Jail.")
                self.send_to_jail(player)
                self.next_player()
                return

        self.move_player(player, total)
        self.evaluate_current_space(player, total)

        if self.state == "WAITING_FOR_ROLL" and not is_double:
            self.next_player()

    def execute_buy_decision(self, wants_to_buy: bool):
        if self.state != "WAITING_FOR_BUY":
            return

        if wants_to_buy:
            if self.pending_player.money >= self.pending_space.price:
                self.pending_player.buy_property(self.pending_space)
                print(f"{self.pending_player.name} bought {self.pending_space.name}!")
            else:
                print("Not enough money!")
        else:
            print(f"{self.pending_player.name} passed on {self.pending_space.name}. Starting Auction.")
            self.start_auction(self.pending_space)
            return

        self.pending_player = None
        self.pending_space = None

        if self.doubles_count > 0 and self.doubles_count < 3:
            self.state = "WAITING_FOR_ROLL"
        else:
            self.next_player()

    def start_auction(self, property_to_auction):
        self.state = "WAITING_FOR_AUCTION"
        self.auction_property = property_to_auction
        self.auction_highest_bid = 0
        self.auction_highest_bidder = None
        self.auction_active_players = [p for p in self.players if p.money >= 0]
        self.auction_current_player_idx = 0
        print(f"\n--- Auction started for {property_to_auction.name} ---")
        self._prompt_auction_turn()

    def _prompt_auction_turn(self):
        if len(self.auction_active_players) == 0:
            print("Auction ended with no bids.")
            self._end_auction()
            return

        if len(self.auction_active_players) == 1 and self.auction_highest_bidder is not None:
            print(f"Auction won by {self.auction_highest_bidder.name} for ${self.auction_highest_bid}.")
            self._end_auction()
            return

        current_bidder = self.auction_active_players[self.auction_current_player_idx]
        print(
            f"Waiting for bid from {current_bidder.name}. Current highest: ${self.auction_highest_bid} by {self.auction_highest_bidder.name if self.auction_highest_bidder else 'None'}")

    def execute_auction_bid(self, player, bid_amount: int, fold: bool):
        if self.state != "WAITING_FOR_AUCTION":
            return

        current_bidder = self.auction_active_players[self.auction_current_player_idx]
        if player != current_bidder:
            print(f"It's not {player.name}'s turn to bid!")
            return

        if fold:
            print(f"{player.name} folded.")
            self.auction_active_players.remove(player)
            if self.auction_current_player_idx >= len(self.auction_active_players):
                self.auction_current_player_idx = 0
        else:
            if bid_amount <= self.auction_highest_bid:
                print(f"Bid must be higher than ${self.auction_highest_bid}! Forcing fold.")
                self.auction_active_players.remove(player)
                if self.auction_current_player_idx >= len(self.auction_active_players):
                    self.auction_current_player_idx = 0
                self._prompt_auction_turn()
                return
            elif player.money < bid_amount:
                print(f"{player.name} doesn't have enough money to bid ${bid_amount}! Forcing fold.")
                self.auction_active_players.remove(player)
                if self.auction_current_player_idx >= len(self.auction_active_players):
                    self.auction_current_player_idx = 0
                self._prompt_auction_turn()
                return

            print(f"{player.name} bid ${bid_amount}.")
            self.auction_highest_bid = bid_amount
            self.auction_highest_bidder = player
            self.auction_current_player_idx = (self.auction_current_player_idx + 1) % len(self.auction_active_players)

        self._prompt_auction_turn()

    def _end_auction(self):
        if self.auction_highest_bidder is not None:
            winner = self.auction_highest_bidder
            winner.money -= self.auction_highest_bid
            self.auction_property.owner = winner
            winner.owned_properties.append(self.auction_property)

        self.auction_property = None
        self.auction_highest_bid = 0
        self.auction_highest_bidder = None
        self.auction_active_players = []

        self.pending_player = None
        self.pending_space = None

        if self.doubles_count > 0 and self.doubles_count < 3:
            self.state = "WAITING_FOR_ROLL"
        else:
            self.next_player()


    def propose_trade(self, proposer, recipient,
                      give_props: list, give_cash: int, give_goojf: int,
                      receive_props: list, receive_cash: int, receive_goojf: int) -> bool:

        if self.state not in ("WAITING_FOR_ROLL", "WAITING_FOR_BUY"):
            print("[TRADE] Trades can only be proposed before rolling or before buying.")
            return False

        if give_cash < 0 or give_cash > proposer.money:
            print(f"[TRADE] {proposer.name} does not have ${give_cash}.")
            return False
        for prop in give_props:
            if prop not in proposer.owned_properties:
                print(f"[TRADE] {proposer.name} does not own {prop.name}.")
                return False
        if give_goojf < 0 or give_goojf > len(proposer.goojf_cards):
            print(f"[TRADE] {proposer.name} does not have {give_goojf} GOOJF card(s).")
            return False

        if receive_cash < 0 or receive_cash > recipient.money:
            print(f"[TRADE] {recipient.name} does not have ${receive_cash}.")
            return False
        for prop in receive_props:
            if prop not in recipient.owned_properties:
                print(f"[TRADE] {recipient.name} does not own {prop.name}.")
                return False
        if receive_goojf < 0 or receive_goojf > len(recipient.goojf_cards):
            print(f"[TRADE] {recipient.name} does not have {receive_goojf} GOOJF card(s).")
            return False

        self.trade_proposer = proposer
        self.trade_recipient = recipient
        self.trade_offer = {
            'give_props': give_props,
            'give_cash': give_cash,
            'give_goojf': give_goojf,
            'receive_props': receive_props,
            'receive_cash': receive_cash,
            'receive_goojf': receive_goojf,
        }
        self.state_before_trade = self.state
        self.state = "WAITING_FOR_TRADE_RESPONSE"

        give_names = [p.name for p in give_props]
        receive_names = [p.name for p in receive_props]
        print(
            f"[TRADE] {proposer.name} → {recipient.name} | "
            f"Offering: {give_names} + ${give_cash} + {give_goojf} GOOJF | "
            f"Requesting: {receive_names} + ${receive_cash} + {receive_goojf} GOOJF"
        )
        return True

    def execute_trade(self, accepted: bool):
        if self.state != "WAITING_FOR_TRADE_RESPONSE":
            return

        proposer = self.trade_proposer
        recipient = self.trade_recipient
        offer = self.trade_offer
        prev_state = self.state_before_trade

        self.trade_proposer = None
        self.trade_recipient = None
        self.trade_offer = None
        self.state_before_trade = None

        if not accepted:
            print(f"[TRADE] {recipient.name} declined {proposer.name}'s offer.")
            self.state = prev_state
            return

        print(f"[TRADE] {recipient.name} accepted {proposer.name}'s offer!")
        self.state = prev_state
        self._transfer_trade_assets(proposer, recipient, offer)

    def _transfer_trade_assets(self, proposer, recipient, offer: dict):
        for prop in list(offer['give_props']):
            prop.owner = recipient
            proposer.owned_properties.remove(prop)
            recipient.owned_properties.append(prop)
            if prop.is_mortgaged:
                fee = max(1, int(prop.mortgage * 0.10))
                print(f"[TRADE] {recipient.name} pays ${fee} interest on mortgaged {prop.name}.")
                self.charge_money(recipient, fee)

        for prop in list(offer['receive_props']):
            prop.owner = proposer
            recipient.owned_properties.remove(prop)
            proposer.owned_properties.append(prop)
            if prop.is_mortgaged:
                fee = max(1, int(prop.mortgage * 0.10))
                print(f"[TRADE] {proposer.name} pays ${fee} interest on mortgaged {prop.name}.")
                self.charge_money(proposer, fee)

        if offer['give_cash'] > 0:
            proposer.money -= offer['give_cash']
            recipient.money += offer['give_cash']
        if offer['receive_cash'] > 0:
            recipient.money -= offer['receive_cash']
            proposer.money += offer['receive_cash']

        for _ in range(offer['give_goojf']):
            card = proposer.goojf_cards.pop(0)
            recipient.goojf_cards.append(card)
        for _ in range(offer['receive_goojf']):
            card = recipient.goojf_cards.pop(0)
            proposer.goojf_cards.append(card)

        print(
            f"[TRADE] Complete. "
            f"{proposer.name}: ${proposer.money} | "
            f"{recipient.name}: ${recipient.money}"
        )

    def move_player(self, player, spaces_to_move):
        old_location = player.location
        player.location = (player.location + spaces_to_move) % 40

        if player.location < old_location and not player.is_in_jail:
            print(f"{player.name} passed GO! Collecting $200.")
            self.deposit_money(player, 200)

    def evaluate_current_space(self, player, dice_total, chance_multiplier=1):
        space = self.board[player.location]
        print(f"{player.name} landed on {space.name}.")

        if space.type in ["street", "railroad", "utility"]:
            self.handle_property_landing(player, space, dice_total, chance_multiplier)

        elif space.type in ["chance", "community_chest"]:
            self.handle_card_draw(player, space.type)

        elif space.type == "tax":
            print(f"{player.name} pays {space.amount} in taxes.")
            self.charge_money(player, space.amount)

        elif space.type == "go_to_jail":
            self.send_to_jail(player)

    def handle_property_landing(self, player, space, dice_total, chance_multiplier=1):
        if space.owner is None:

            self.state = "WAITING_FOR_BUY"
            self.pending_player = player
            self.pending_space = space
            print(f"Waiting for decision: Buy {space.name} for ${space.price}?")

        elif space.owner != player:
            if space.is_mortgaged:
                print(f"{space.name} is mortgaged. No rent is due.")
                return

            rent = 0
            match(space.type):
                case "street":
                    has_mono = space.owner.get_owned_group_count(space.group) == self.group_sizes[space.group]
                    rent = space.get_current_rent(has_monopoly=has_mono)

                case "railroad":
                    owned_rr = space.owner.get_owned_type_count("railroad")
                    rent = space.get_current_rent(group_owned_count=owned_rr, chance_multiplier=chance_multiplier)

                case "utility":
                    owned_util = space.owner.get_owned_type_count("utility")
                    rent = space.get_current_rent(dice_roll=dice_total, group_owned_count=owned_util,
                                                  chance_multiplier=chance_multiplier)

            print(f"{player.name} owes {space.owner.name} ${rent} for rent.")
            self.transfer_money(player, space.owner, rent)

    def send_to_jail(self, player):
        player.location = 10
        player.is_in_jail = True
        player.turns_in_jail = 0
        print(f"{player.name} has been sent to Jail!")

    def handle_jail_turn(self, player, is_double, dice_total):
        print(f"{player.name} is in Jail (Turn {player.turns_in_jail + 1}/3).")

        if len(player.goojf_cards) > 0:
            used_card = player.goojf_cards.pop(0)
            used_card.is_held = False
            player.is_in_jail = False
            print(f"{player.name} used a Get Out of Jail Free card!")
            self.move_player(player, dice_total)
            self.evaluate_current_space(player, dice_total)
            return

        if is_double:
            print("Rolled doubles! Escaping Jail.")
            player.is_in_jail = False
            self.move_player(player, dice_total)
            self.evaluate_current_space(player, dice_total)
        else:
            player.turns_in_jail += 1
            if player.turns_in_jail == 3:
                print("Failed to roll doubles in 3 turns. Paying $50 fine.")
                self.charge_money(player, 50)
                player.is_in_jail = False
                self.move_player(player, dice_total)
                self.evaluate_current_space(player, dice_total)

    def handle_card_draw(self, player, deck_type):
        if deck_type == "chance":
            card = self.chance_deck.draw()
            print(f"Chance: {card.description}")
            self.execute_chance_card(player, card)
        elif deck_type == "community_chest":
            card = self.community_chest_deck.draw()
            print(f"Community Chest: {card.description}")
            self.execute_community_chest_card(player, card)

    def execute_chance_card(self, player, card):
        match(card.id):
            case 0:
                self.advance_to(player, 39)
            case 1:
                self.advance_to(player, 0)
            case 2:
                self.advance_to(player, 24)
            case 3:
                self.advance_to(player, 11)
            case [4, 5]:
                self.advance_to_nearest(player, "railroad", multiplier=2)
            case 6:
                self.advance_to_nearest(player, "utility", is_chance_roll=True)
            case 7:
                self.deposit_money(player, 50)
            case 8:
                card.is_held = True
                player.goojf_cards.append(card)
                print(f"{player.name} kept the Get Out of Jail Free card!")
            case 9:
                player.location = (player.location - 3) % 40
                self.evaluate_current_space(player, 0)
            case 10:
                self.send_to_jail(player)
            case 11:
                self.assess_street_repairs(player, 25, 100)
            case 12:
                self.charge_money(player, 15)
            case 13:
                self.advance_to(player, 5)
            case 14:
                self.pay_all_players(player, 50)
            case 15:
                self.deposit_money(player, 150)

    def execute_community_chest_card(self, player, card):
        match(card.id):
            case 0:
                self.advance_to(player, 0)
            case 1:
                self.deposit_money(player, 200)
            case 2:
                self.charge_money(player, 50)
            case 3:
                self.deposit_money(player, 50)
            case 4:
                card.is_held = True
                player.goojf_cards.append(card)
                print(f"{player.name} kept the Get Out of Jail Free card!")
            case 5:
                self.send_to_jail(player)
            case 6:
                self.deposit_money(player, 100)
            case 7:
                self.deposit_money(player, 20)
            case 8:
                self.collect_from_all_players(player, 10)
            case 9:
                self.deposit_money(player, 100)
            case 10:
                self.charge_money(player, 100)
            case 11:
                self.charge_money(player, 50)
            case 12:
                self.deposit_money(player, 25)
            case 13:
                self.assess_street_repairs(player, 40, 115)
            case 14:
                self.deposit_money(player, 10)
            case 15:
                self.deposit_money(player, 100)

    def advance_to(self, player, target_location):
        if target_location < player.location:
            print(f"{player.name} passed GO! Collecting $200.")
            self.deposit_money(player, 200)
        player.location = target_location
        self.evaluate_current_space(player, dice_total=0)

    def advance_to_nearest(self, player, space_type, multiplier=1, is_chance_roll=False):
        current_loc = player.location
        target_loc = 0

        if space_type == "railroad":
            if current_loc < 5 or current_loc >= 35:
                target_loc = 5
            elif current_loc < 15:
                target_loc = 15
            elif current_loc < 25:
                target_loc = 25
            elif current_loc < 35:
                target_loc = 35
        elif space_type == "utility":
            if current_loc < 12 or current_loc >= 28:
                target_loc = 12
            elif current_loc < 28:
                target_loc = 28

        if target_loc < player.location:
            print(f"{player.name} passed GO! Collecting $200.")
            self.deposit_money(player, 200)

        player.location = target_loc

        dice_total = sum(self.roll_dice()[0:2]) if is_chance_roll else 0

        space = self.board[player.location]
        self.handle_property_landing(player, space, dice_total, chance_multiplier=multiplier)

    def assess_street_repairs(self, player, house_cost, hotel_cost):
        total_houses = sum(prop.house_count for prop in player.owned_properties)
        total_hotels = sum(prop.hotel_count for prop in player.owned_properties)
        fine = (total_houses * house_cost) + (total_hotels * hotel_cost)
        print(f"{player.name} pays ${fine} for property repairs.")
        self.charge_money(player, fine)

    def charge_money(self, player, amount, creditor=None):
        player.money -= amount
        if player.money < 0:
            print(f"🚨 ALERT: {player.name} is in debt! Balance: ${player.money}")
            if self.state != "WAITING_FOR_DEBT_RESOLUTION":
                self.state_before_debt = self.state
                self.state = "WAITING_FOR_DEBT_RESOLUTION"
                self.debtor = player
                self.creditor = creditor

    def deposit_money(self, player, amount):
        player.money += amount

    def transfer_money(self, payer, payee, amount):
        self.charge_money(payer, amount, creditor=payee)
        self.deposit_money(payee, amount)

    def resolve_debt(self):
        if self.debtor is None:
            return

        if self.debtor.money < 0:
            return

        print(f"{self.debtor.name} successfully resolved their debt.")

        self.debtor = None
        self.creditor = None

        if self.state_before_debt == "WAITING_FOR_ROLL":
            if self.last_roll is not None and self.last_roll[0] == self.last_roll[1]:
                self.state = "WAITING_FOR_ROLL"
            else:
                self.next_player()
                self.state = "WAITING_FOR_ROLL"

        else:
            self.state = self.state_before_debt

        self.state_before_debt = None

    def declare_bankruptcy(self, player):
        if self.state != "WAITING_FOR_DEBT_RESOLUTION" or player != self.debtor:
            return

        print(f"💀 {player.name} has declared bankruptcy!")

        if self.creditor:
            for prop in list(player.owned_properties):
                prop.owner = self.creditor
                self.creditor.owned_properties.append(prop)
        else:
            for prop in list(player.owned_properties):
                prop.owner = None
                prop.house_count = 0
                prop.hotel_count = 0
                prop.is_mortgaged = False

        player.owned_properties.clear()

        idx = self.players.index(player) if player in self.players else -1
        is_current = (idx == self.current_player_idx)
        if idx != -1:
            self.players.remove(player)
            if len(self.players) == 1:
                print(f"🎉 {self.players[0].name} wins the game!")
                self.state = "GAME_OVER"
            else:
                if idx < self.current_player_idx:
                    self.current_player_idx -= 1

        if self.state != "GAME_OVER":
            if is_current:
                self.current_player_idx %= len(self.players)
                self.state = "WAITING_FOR_ROLL"
                self.doubles_count = 0
            else:
                self.state = self.state_before_debt if self.state_before_debt else "WAITING_FOR_ROLL"

        self.debtor = None
        self.creditor = None
        self.state_before_debt = None

    def pay_all_players(self, paying_player, amount):
        for p in self.players:
            if p != paying_player:
                self.transfer_money(paying_player, p, amount)

    def collect_from_all_players(self, collecting_player, amount):
        for p in self.players:
            if p != collecting_player:
                self.transfer_money(p, collecting_player, amount)