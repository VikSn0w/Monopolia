import random
from logic.Player import Player
from logic.Property import Property


class Bot(Player):
    def __init__(self, name, difficulty=1, money=1500):
        super().__init__(name, money)
        self.difficulty = difficulty

    def make_decision(self, gm):
        match(gm.state):
            case "WAITING_FOR_ROLL":
                self._handle_building(gm)
                gm.execute_roll_action()

            case "WAITING_FOR_BUY":
                wants_to_buy = self._decide_to_buy(gm.pending_space)
                gm.execute_buy_decision(wants_to_buy)

            case "WAITING_FOR_AUCTION":
                bid, fold = self._decide_auction_bid(gm)
                gm.execute_auction_bid(self, bid, fold)

            case "WAITING_FOR_DEBT_RESOLUTION":
                self._handle_debt(gm)

            case  "WAITING_FOR_TRADE_RESPONSE":
                if gm.trade_recipient is self:
                    accepted = self._evaluate_trade(gm)
                    gm.execute_trade(accepted)

    def _evaluate_trade(self, gm) -> bool:
        """
        Decide whether to accept a trade proposal directed at this bot.

        Valuation
        ---------
        • Each property is valued at its face price, with a bonus if the
          property completes (or contributes to) a monopoly for the recipient.
        • Cash is face value.
        • A GOOJF card is worth $50 (roughly its auction value).
        • Difficulty 1 accepts randomly (30 % chance).
        • Difficulty 2+ accepts only when the deal is net-neutral or better.
        • Difficulty 3+ applies a 10 % discount tolerance and checks whether
          a monopoly bonus justifies an otherwise losing trade.
        """
        offer = gm.trade_offer
        GOOJF_VALUE = 50

        def _prop_value(prop, future_owner) -> int:
            """Base price + monopoly-completion bonus for future_owner."""
            val = prop.price
            group = prop.group
            total = gm.group_sizes.get(group, 0)
            if total == 0:
                return val
            # Count how many of this group future_owner will own after the trade.
            current_count = future_owner.get_owned_group_count(group)
            traded_in_deal = sum(
                1 for p in (offer['give_props'] if future_owner is self else offer['receive_props'])
                if p.group == group
            )
            after_count = current_count + traded_in_deal
            if after_count == total:
                val += 400  # completing a monopoly is highly valuable
            elif after_count == total - 1:
                val += 100  # one away — still useful
            return val

        # What I (recipient / self) gain
        gain = (
                sum(_prop_value(p, self) for p in offer['give_props'])
                + offer['give_cash']
                + offer['give_goojf'] * GOOJF_VALUE
        )
        # What I (recipient / self) give up
        cost = (
                sum(_prop_value(p, gm.trade_proposer) for p in offer['receive_props'])
                + offer['receive_cash']
                + offer['receive_goojf'] * GOOJF_VALUE
        )

        if self.difficulty == 1:
            return random.random() < 0.30

        elif self.difficulty == 2:
            return gain >= cost

        else:  # difficulty 3+
            # Accept if gain is within 10 % of cost (good-faith deals).
            return gain >= cost * 0.90

    def _decide_to_buy(self, prop: Property) -> bool:
        if self.money < prop.price:
            return False

        if self.difficulty == 1:
            return random.choice([True, False])

        elif self.difficulty == 2:
            return self.money >= prop.price + 200

        elif self.difficulty >= 3:

            return self.money >= prop.price + 50

    def _decide_auction_bid(self, gm) -> tuple[int, bool]:
        prop = gm.auction_property
        current_bid = gm.auction_highest_bid

        if self.money <= current_bid:
            return 0, True

        if self.difficulty == 1:
            if random.random() < 0.3:
                return current_bid + random.randint(1, 10), False
            return 0, True

        elif self.difficulty == 2:
            if current_bid < prop.price and self.money >= current_bid + 50:
                return current_bid + 10, False
            return 0, True

        elif self.difficulty >= 3:
            max_bid = prop.price + 50 if self.difficulty == 3 else prop.price + 150
            owned = self.get_owned_group_count(prop.group)
            if owned == gm.group_sizes.get(prop.group, 0) - 1:
                max_bid += 200

            if current_bid < max_bid and self.money >= current_bid + 10:
                return current_bid + 10, False
            return 0, True

    def _handle_building(self, gm):
        if self.difficulty == 1:
            return

        for prop in self.owned_properties:
            if prop.type != "street": continue
            total_in_group = gm.group_sizes.get(prop.group, 0)
            if self.get_owned_group_count(prop.group) == total_in_group:
                safe_money = 500 if self.difficulty == 2 else 300
                target_houses = 3 if self.difficulty >= 3 else 2

                if self.money > safe_money + prop.house_cost and self.get_effective_houses(prop) < target_houses:
                    if self.can_build_house(prop.location, total_in_group):
                        print(f"[BOT] {self.name} builds a house on {prop.name}!")
                        self.buy_house(prop.location)

    def _handle_debt(self, gm):
        if self.difficulty == 1:
            prev_money = self.money
            if len(self.owned_properties) > 0:
                valid_props = [p for p in self.owned_properties if
                               self.get_effective_houses(p) > 0 or not p.is_mortgaged]
                if len(valid_props) > 0:
                    prop = random.choice(valid_props)
                    if self.get_effective_houses(prop) > 0:
                        self.sell_house(prop.location)
                    elif not prop.is_mortgaged:
                        self.mortgage_property(prop.location)

            if self.money >= 0:
                gm.resolve_debt()
            elif self.money == prev_money:
                # No valid actions succeeded -> bankrupt
                gm.declare_bankruptcy(self)

        elif self.difficulty >= 2:
            prev_money = self.money - 1  # force loop to start
            while self.money < 0 and self.money > prev_money:
                prev_money = self.money

                # 1. Mortgage un-grouped properties
                for prop in self.owned_properties:
                    if not prop.is_mortgaged and self.get_owned_group_count(prop.group) < gm.group_sizes.get(prop.group,
                                                                                                             99):
                        self.mortgage_property(prop.location)
                        if self.money >= 0:
                            gm.resolve_debt()
                            return

                # 2. Sell houses evenly
                for prop in self.owned_properties:
                    if self.get_effective_houses(prop) > 0:
                        self.sell_house(prop.location)
                        if self.money >= 0:
                            gm.resolve_debt()
                            return

                # 3. Mortgage monopolies if they have no houses left
                for prop in self.owned_properties:
                    if not prop.is_mortgaged and self.get_effective_houses(prop) == 0:
                        self.mortgage_property(prop.location)
                        if self.money >= 0:
                            gm.resolve_debt()
                            return

            # If we exit the while loop and still owe money, we couldn't liquidate enough
            if self.money < 0:
                gm.declare_bankruptcy(self)
            else:
                gm.resolve_debt()