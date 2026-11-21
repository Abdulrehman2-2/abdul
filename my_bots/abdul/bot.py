
import random
import time
import eval7

DEBUG = False


def dbg(msg=""):
    if DEBUG:
        print(msg)


RANK_ORDER = "23456789TJQKA"
RANK_VAL = {r: i for i, r in enumerate(RANK_ORDER)}
SIZE_SMALL = 0.40   # dry boards
SIZE_BIG = 0.67     # wet boards

HAND_TIERS = {}


def _init_hand_tiers():
    pairs = {'AA': 1, 'KK': 1, 'QQ': 1, 'JJ': 1, 'TT': 2, '99': 2, '88': 3, '77': 3,
             '66': 4, '55': 4, '44': 4, '33': 5, '22': 5}
    suited = {
        'AKs': 1, 'AQs': 1, 'AJs': 2, 'ATs': 2, 'A9s': 3, 'A8s': 3, 'A7s': 3, 'A6s': 4,
        'A5s': 3, 'A4s': 4, 'A3s': 4, 'A2s': 4, 'KQs': 2, 'KJs': 2, 'KTs': 2, 'K9s': 3,
        'K8s': 4, 'K7s': 4, 'K6s': 5, 'K5s': 5, 'K4s': 5, 'K3s': 5, 'K2s': 5,
        'QJs': 2, 'QTs': 3, 'Q9s': 4, 'Q8s': 5, 'Q7s': 5, 'JTs': 2, 'J9s': 3, 'J8s': 4,
        'J7s': 5, 'T9s': 3, 'T8s': 4, 'T7s': 5, '98s': 3, '97s': 4, '96s': 5,
        '87s': 3, '86s': 5, '76s': 4, '75s': 5, '65s': 4, '64s': 5, '54s': 4, '53s': 5, '43s': 5}
    offsuit = {
        'AKo': 1, 'AQo': 2, 'AJo': 2, 'ATo': 3, 'A9o': 4, 'A8o': 4, 'A7o': 5, 'A6o': 5,
        'A5o': 4, 'A4o': 5, 'A3o': 5, 'A2o': 5, 'KQo': 2, 'KJo': 3, 'KTo': 3, 'K9o': 4,
        'K8o': 5, 'QJo': 3, 'QTo': 4, 'Q9o': 5, 'JTo': 3, 'J9o': 5, 'T9o': 4, 'T8o': 5,
        '98o': 5, '97o': 5, '87o': 5, '76o': 5}
    for d in (pairs, suited, offsuit):
        HAND_TIERS.update(d)


_init_hand_tiers()

# Rough equity vs a random hand by tier (used for preflop pot-odds decisions)
TIER_EQ = {1: 0.72, 2: 0.62, 3: 0.56, 4: 0.52, 5: 0.48, 6: 0.42}

# Push/fold tables: max effective stack (in BB) at which the hand shoves / calls
PUSH_JAM = {
    'AA': 50, 'KK': 50, 'QQ': 50, 'JJ': 50, 'TT': 50, '99': 50, '88': 43, '77': 31,
    '66': 23, '55': 20, '44': 18, '33': 16, '22': 14,
    'AKs': 50, 'AQs': 50, 'AJs': 50, 'ATs': 50, 'A9s': 50, 'A8s': 50, 'A7s': 50,
    'A6s': 50, 'A5s': 50, 'A4s': 50, 'A3s': 50, 'A2s': 48,
    'KQs': 50, 'KJs': 50, 'KTs': 50, 'K9s': 36, 'K8s': 32, 'K7s': 29, 'K6s': 26,
    'K5s': 24, 'K4s': 22, 'K3s': 20, 'K2s': 19,
    'QJs': 50, 'QTs': 50, 'Q9s': 30, 'Q8s': 24, 'Q7s': 19,
    'JTs': 50, 'J9s': 33, 'J8s': 24, 'J7s': 18, 'T9s': 36, 'T8s': 25, 'T7s': 17,
    '98s': 29, '97s': 20, '96s': 16, '87s': 26, '86s': 16, '76s': 24, '75s': 14,
    '65s': 23, '64s': 11, '54s': 21, '53s': 10, '43s': 15,
    'AKo': 50, 'AQo': 50, 'AJo': 50, 'ATo': 50, 'A9o': 50, 'A8o': 41, 'A7o': 36,
    'A6o': 32, 'A5o': 50, 'A4o': 29, 'A3o': 25, 'A2o': 22,
    'KQo': 50, 'KJo': 36, 'KTo': 30, 'K9o': 19, 'K8o': 13,
    'QJo': 30, 'QTo': 24, 'Q9o': 14, 'JTo': 25, 'J9o': 14, 'J8o': 9,
    'T9o': 19, 'T8o': 10, '98o': 15, '97o': 8, '87o': 12, '86o': 6,
    '76o': 10, '75o': 5, '65o': 9, '54o': 7}
PUSH_CALL = {
    'AA': 50, 'KK': 50, 'QQ': 50, 'JJ': 50, 'TT': 48, '99': 45, '88': 40, '77': 35,
    '66': 31, '55': 26, '44': 24, '33': 22, '22': 15,
    'AKs': 50, 'AQs': 50, 'AJs': 50, 'ATs': 48, 'A9s': 40, 'A8s': 36, 'A7s': 31,
    'A6s': 26, 'A5s': 26, 'A4s': 25, 'A3s': 24, 'A2s': 23,
    'KQs': 50, 'KJs': 45, 'KTs': 42, 'K9s': 15, 'K8s': 13, 'K7s': 12, 'K6s': 11,
    'K5s': 10, 'K4s': 9, 'K3s': 8, 'K2s': 7,
    'QJs': 42, 'QTs': 15, 'Q9s': 10, 'Q8s': 9, 'JTs': 15, 'J9s': 14, 'J8s': 5,
    'T9s': 14, 'T8s': 6, '98s': 8, '97s': 5, '87s': 7, '86s': 5, '76s': 6, '65s': 5, '54s': 5,
    'AKo': 50, 'AQo': 50, 'AJo': 50, 'ATo': 40, 'A9o': 36, 'A8o': 31, 'A7o': 26,
    'A6o': 20, 'A5o': 19, 'A4o': 17, 'A3o': 15, 'A2o': 11,
    'KQo': 45, 'KJo': 15, 'KTo': 14, 'K9o': 11, 'K8o': 8,
    'QJo': 13, 'QTo': 10, 'Q9o': 8, 'JTo': 13, 'J9o': 5, 'T9o': 6}

def _norm_rank(r):
    return 'T' if r == '10' else r


def card_str_to_eval7(c):
    if len(c) == 3 and c[0:2] == '10':
        c = 'T' + c[2]
    return eval7.Card(c)


def canonicalize(cards):
    r1, s1 = _norm_rank(cards[0][:-1]), cards[0][-1]
    r2, s2 = _norm_rank(cards[1][:-1]), cards[1][-1]
    if RANK_VAL.get(r1, 0) < RANK_VAL.get(r2, 0):
        r1, r2 = r2, r1
        s1, s2 = s2, s1
    if r1 == r2:
        return r1 + r2
    return r1 + r2 + ('s' if s1 == s2 else 'o')


def get_tier(cards):
    return HAND_TIERS.get(canonicalize(cards), 6)


def get_street(community):
    n = len(community)
    if n == 0:
        return 'preflop'
    if n == 3:
        return 'flop'
    if n == 4:
        return 'turn'
    return 'river'


def _is_seven_two(cards):
    return {_norm_rank(c[:-1]) for c in cards} == {'7', '2'}


def has_draw(my_cards, community):
    all_cards = my_cards + community
    suits = {}
    for c in all_cards:
        suits[c[-1]] = suits.get(c[-1], 0) + 1
    has_fd = any(suits[s] >= 4 and any(c[-1] == s for c in my_cards) for s in suits)
    my_rv = {RANK_VAL.get(_norm_rank(c[:-1]), 0) for c in my_cards}
    all_rv = {RANK_VAL.get(_norm_rank(c[:-1]), 0) for c in all_cards}
    sr = sorted(all_rv)
    has_oesd = has_gs = False
    for i in range(len(sr) - 3):
        w = sr[i:i + 4]
        if w[-1] - w[0] == 3 and my_rv & set(w):
            has_oesd = True
    if not has_oesd:
        for i in range(len(sr) - 3):
            w = sr[i:i + 4]
            if w[-1] - w[0] == 4 and my_rv & set(w):
                has_gs = True
    if has_fd and (has_oesd or has_gs):
        return 'combo'
    if has_fd:
        return 'flush'
    if has_oesd:
        return 'oesd'
    if has_gs:
        return 'gutshot'
    return None


def size_bet(desired, mn, mx, stk=None):
    """Clamp a desired TOTAL bet to [min raise, max (all-in) total]."""
    if mx <= 0:
        return 0
    return int(min(mx, max(mn, desired)))


# =====================================================================
# BOARD ANALYSIS
# =====================================================================
def analyze_board(community):
    if not community:
        return {'wet': False, 'paired': False, 'monotone': False, 'two_tone': False,
                'connected': False, 'high': False, 'raiser_favored': True,
                'caller_favored': False, 'highest_rank': 0}
    suits = {}
    ranks = []
    for c in community:
        suits[c[-1]] = suits.get(c[-1], 0) + 1
        ranks.append(RANK_VAL.get(_norm_rank(c[:-1]), 0))
    sr = sorted(ranks)
    ms = max(suits.values())
    rc = {}
    for r in ranks:
        rc[r] = rc.get(r, 0) + 1
    paired = any(v >= 2 for v in rc.values())
    monotone = ms >= 3
    two_tone = ms == 2
    gaps = sum(1 for i in range(len(sr) - 1) if sr[i + 1] - sr[i] <= 2)
    connected = gaps >= 2
    high = sr[-1] >= RANK_VAL['J']
    ace_hi = sr[-1] == RANK_VAL['A']
    king_hi = sr[-1] == RANK_VAL['K']
    low = sr[-1] <= RANK_VAL['9']
    wet = (connected and two_tone) or (connected and not paired) or monotone
    raiser_fav = False
    caller_fav = False
    if (ace_hi or king_hi) and not connected and not monotone:
        raiser_fav = True
    elif paired and high:
        raiser_fav = True
    elif low and connected:
        caller_fav = True
    elif connected and two_tone and not high:
        caller_fav = True
    else:
        raiser_fav = True
    return {'wet': wet, 'paired': paired, 'monotone': monotone, 'two_tone': two_tone,
            'connected': connected, 'high': high, 'raiser_favored': raiser_fav,
            'caller_favored': caller_fav, 'highest_rank': sr[-1]}

def calc_equity(my_cards, community, n_sim=1500, opp_vpip=None, max_seconds=0.6):
    my_hand = [card_str_to_eval7(c) for c in my_cards]
    board = [card_str_to_eval7(c) for c in community]
    known = set(my_hand + board)
    remaining = [c for c in eval7.Deck().cards if c not in known]
    max_tier = 6
    if opp_vpip is not None and opp_vpip < 0.65:
        if opp_vpip < 0.25:
            max_tier = 2
        elif opp_vpip < 0.35:
            max_tier = 3
        elif opp_vpip < 0.48:
            max_tier = 4
        elif opp_vpip < 0.60:
            max_tier = 5
    wins = ties = total = attempts = 0
    need = 5 - len(board)
    t0 = time.time()
    while total < n_sim and attempts < n_sim * 4:
        attempts += 1
        if (attempts & 31) == 0 and time.time() - t0 > max_seconds:
            break
        draw = random.sample(remaining, 2 + need)
        opp = draw[:2]
        if max_tier < 6 and get_tier([str(opp[0]), str(opp[1])]) > max_tier:
            continue
        full = board + draw[2:]
        ms = eval7.evaluate(my_hand + full)
        os_ = eval7.evaluate(opp + full)
        if ms > os_:
            wins += 1
        elif ms == os_:
            ties += 1
        total += 1
    if total == 0:
        return 0.5
    return (wins + ties * 0.5) / total


def shade_equity(eq, owed, pot, stack, om):
    """Opponent's betting range is stronger than random: shade equity down."""
    if owed <= 0:
        return eq
    pot_before = max(pot - owed, 1)
    frac = owed / pot_before
    f = 1.0
    if frac > 0.75:
        f *= 0.88
    elif frac > 0.30:
        f *= 0.94
    if owed >= 0.4 * stack:
        f *= 0.92
    if om.hands_seen >= 10 and om.is_aggressive:
        f = 1 - (1 - f) * 0.4      # maniacs bet wide: trust equity more
    return eq * f

class OpponentModel:
    def __init__(self):
        self.reset()

    def reset(self):
        self.hands_seen = 0
        self.vpip_count = 0
        self.pfr_count = 0
        self.bets = 0
        self.calls = 0
        self.checks = 0
        self.folds = 0
        self.fold_to_bet = {'preflop': [0, 0], 'flop': [0, 0], 'turn': [0, 0], 'river': [0, 0]}
        self.cr_count = 0
        self.cr_opps = 0
        self.last_hand = -1

    def update(self, log, my_seat, current_hand):
        """Process every COMPLETED hand in the log that we haven't seen yet."""
        by_hand = {}
        for e in log:
            hn = e.get('hand_num')
            if hn is None or hn >= current_hand or hn <= self.last_hand:
                continue
            by_hand.setdefault(hn, []).append(e)
        for hn in sorted(by_hand):
            self._process(by_hand[hn], my_seat)
            self.last_hand = hn

    def _process(self, entries, my_seat):
        opp_vpip = False
        opp_pfr = False
        street = None
        facing = False
        opp_checked = False
        cr_pending = False
        for e in entries:
            act = e.get('action', '')
            seat = e.get('seat', -1)
            st = e.get('street', 'preflop')
            if act in ('small_blind', 'big_blind', 'ante', 'show', 'win', 'muck'):
                continue
            if st != street:
                street = st
                facing = False
                opp_checked = False
                cr_pending = False
            if seat == my_seat:
                if act in ('raise', 'all_in'):
                    facing = True
                    if opp_checked and st != 'preflop':
                        cr_pending = True
                continue
            # ---- opponent action ----
            if st == 'preflop':
                if act in ('call', 'raise', 'all_in'):
                    opp_vpip = True
                if act in ('raise', 'all_in'):
                    opp_pfr = True
            else:
                if act == 'check':
                    self.checks += 1
                    opp_checked = True
                elif act == 'call':
                    self.calls += 1
                elif act in ('raise', 'all_in'):
                    self.bets += 1
                if cr_pending:
                    self.cr_opps += 1
                    if act in ('raise', 'all_in'):
                        self.cr_count += 1
                    cr_pending = False
            if facing and st in self.fold_to_bet:
                rec = self.fold_to_bet[st]
                rec[1] += 1
                if act == 'fold':
                    rec[0] += 1
                facing = False
            if act == 'fold':
                self.folds += 1
            if act in ('raise', 'all_in'):
                facing = False
        self.hands_seen += 1
        if opp_vpip:
            self.vpip_count += 1
        if opp_pfr:
            self.pfr_count += 1

    @property
    def vpip(self):
        return 0.5 if self.hands_seen < 3 else self.vpip_count / self.hands_seen

    @property
    def pfr(self):
        return 0.3 if self.hands_seen < 3 else self.pfr_count / self.hands_seen

    @property
    def aggression_factor(self):
        if self.calls == 0:
            return 2.0 if self.bets > 0 else 1.0
        return self.bets / self.calls

    def get_fold_to_bet(self, street='flop'):
        f, o = self.fold_to_bet.get(street, [0, 0])
        return 0.30 if o < 3 else f / o

    @property
    def check_raise_freq(self):
        if self.cr_opps < 5:
            return 0.08
        return self.cr_count / self.cr_opps

    @property
    def is_passive(self):
        return self.vpip > 0.6 and self.aggression_factor < 1.0

    @property
    def is_tight(self):
        return self.hands_seen >= 8 and self.vpip < 0.35

    @property
    def is_aggressive(self):
        return self.aggression_factor > 2.0

    @property
    def is_calling_station(self):
        return self.hands_seen >= 8 and self.vpip > 0.55 and self.aggression_factor < 0.8

    @property
    def is_check_raise_heavy(self):
        return self.cr_opps >= 10 and self.check_raise_freq > 0.15


# =====================================================================
# GLOBAL STATE (lasts for exactly one match)
# =====================================================================
opp_model = OpponentModel()
we_raised_preflop = False


def _act(action_dict, reason=""):
    dbg(f"  >>> {action_dict} ({reason})")
    return action_dict


# =====================================================================
# PREFLOP
# =====================================================================
def preflop_decision(tier, is_dealer, seven_two, pot, owed, can_check, can_raise,
                     min_r, max_r, stack, bb, action_log, om, cur_bet):
    n_raises = sum(1 for e in action_log
                   if e.get('street') == 'preflop' and e.get('action') in ('raise', 'all_in'))
    facing_raise = owed > 0 and n_raises >= 1
    facing_3bet = owed > 0 and n_raises >= 2
    need = owed / (pot + owed) if owed > 0 else 0.0
    big = owed >= 0.5 * stack          # facing a bet that commits half our stack
    call_or_check = {"action": "call"} if owed > 0 else {"action": "check"}
    fold_or_check = {"action": "fold"} if owed > 0 else {"action": "check"}

    def raise_to(x, reason):
        return _act({"action": "raise", "amount": size_bet(int(x), min_r, max_r)}, reason)

    # ---- 7-2: raise always, give up to resistance ----
    if seven_two:
        if not facing_raise and can_raise:
            return raise_to(3 * bb, "7-2 raise")
        if facing_raise:
            return _act(fold_or_check, "7-2 fold to raise")
        return _act(call_or_check, "7-2")

    # ---- Button / small blind opening ----
    if is_dealer and not facing_raise:
        if tier <= 2:
            x = 3.0 * bb
        elif tier <= 4:
            x = 2.5 * bb
        elif tier == 5:
            x = 2.3 * bb
        else:
            steal = 0.5 if (om.get_fold_to_bet('preflop') > 0.5 or om.is_tight) else 0.25
            if random.random() < steal:
                x = 2.2 * bb
            else:
                return _act(fold_or_check, "trash fold")
        if can_raise:
            return raise_to(x, f"open tier {tier}")
        return _act(call_or_check, "open (can't raise)")

    # ---- Facing a 3-bet or bigger ----
    if facing_3bet:
        if big:
            if tier <= 1 or (tier <= 2 and om.is_aggressive):
                return _act({"action": "call"}, "call big 3bet")
            return _act({"action": "fold"}, "fold to big 3bet")
        if tier <= 1:
            if random.random() < 0.5 and can_raise:
                return raise_to(cur_bet * 2.3, "4-bet premium")
            return _act({"action": "call"}, "call 3bet premium")
        if tier == 2:
            return _act({"action": "call"}, "call 3bet strong")
        if tier == 3 and need < 0.30:
            return _act({"action": "call"}, "call small 3bet")
        return _act({"action": "fold"}, "fold to 3bet")

    # ---- Facing a single raise ----
    if facing_raise:
        if big:
            if tier <= 1 or (tier <= 2 and om.is_aggressive):
                return _act({"action": "call"}, "call big raise")
            return _act({"action": "fold"}, "fold to big raise")
        if tier <= 1 and can_raise:
            return raise_to(cur_bet * 3.0, "3-bet premium")
        if tier == 2 and can_raise and random.random() < 0.35:
            return raise_to(cur_bet * 3.0, "3-bet strong")
        if TIER_EQ.get(tier, 0.4) - 0.08 > need:
            return _act({"action": "call"}, f"call raise tier {tier}")
        return _act({"action": "fold"}, "fold to raise")

    # ---- Big blind, no raise in front ----
    if not is_dealer:
        if can_raise:
            if tier <= 2:
                return raise_to(3.5 * bb, "BB raise strong")
            if tier <= 4 and random.random() < 0.5:
                return raise_to(3.0 * bb, "BB raise mix")
        return _act(call_or_check, "BB check/call")

    return _act({"action": "check"} if can_check else {"action": "fold"}, "default")


# =====================================================================
# PUSH / FOLD (effective stack <= 12 BB)
# =====================================================================
def push_fold_decision(tier, is_dealer, stack_bb, stack, can_raise, can_check,
                       owed, s2, my_cards, om):
    canon = canonicalize(my_cards)
    shove = {"action": "all_in"}
    call_or_check = {"action": "call"} if owed > 0 else {"action": "check"}
    fold_or_check = {"action": "fold"} if owed > 0 else {"action": "check"}
    facing_jam = owed > 0 and owed >= stack * 0.4

    if is_dealer and not facing_jam:
        t = PUSH_JAM.get(canon, 0)
        if s2 and can_raise:
            return _act(shove, "7-2 jam")
        if stack_bb <= 2:
            return _act(shove if can_raise else call_or_check, "tiny stack shove")
        if stack_bb <= 3 and tier <= 5:
            return _act(shove if can_raise else call_or_check, "3BB push")
        if t > 0 and stack_bb <= t:
            return _act(shove if can_raise else call_or_check, f"push {canon}")
        if stack_bb <= 10:
            return _act(fold_or_check, f"don't push {canon}")
        return None

    if facing_jam:
        ct = PUSH_CALL.get(canon, 0)
        if stack_bb <= 2:
            return _act(call_or_check, "pot committed")
        if ct > 0 and stack_bb <= ct:
            return _act(call_or_check, f"call jam {canon}")
        if om.vpip > 0.70 and tier <= 4:
            return _act(call_or_check, "call wide shover")
        return _act({"action": "fold"}, f"fold vs jam {canon}")

    if not is_dealer:
        t = PUSH_JAM.get(canon, 0) * 0.75
        if s2 and can_raise:
            return _act(shove, "7-2 jam")
        if stack_bb <= 2:
            return _act(shove if can_raise else call_or_check, "BB tiny")
        if t > 0 and stack_bb <= t:
            return _act(shove if can_raise else call_or_check, f"BB shove {canon}")
        if stack_bb <= 10:
            return _act(fold_or_check, f"BB fold {canon}")
        return None
    return None


# =====================================================================
# POSTFLOP
# =====================================================================
def _pick_size(c):
    return SIZE_BIG if c['bi'].get('wet') else SIZE_SMALL


def _open_bet(c, frac):
    return size_bet(int(c['pot'] * frac), c['mn'], c['mx'])


def _raise_over(c, frac):
    return size_bet(c['cur'] + int((c['pot'] + c['owed']) * frac), c['mn'], c['mx'])


def _can_raise(c):
    return c['cr'] and c['mx'] > 0


def _play_monster(c):
    om = c['om']
    if c['owed'] > 0:
        if _can_raise(c):
            return _act({"action": "raise", "amount": _raise_over(c, 1.0)}, "monster reraise")
        return _act({"action": "call"}, "monster call")
    sf = 0.08 if c['bi'].get('wet') else 0.22
    if c['street'] == 'flop' and c['spr'] > 3 and random.random() < sf:
        return _act({"action": "check"}, "monster slowplay")
    if _can_raise(c):
        if c['street'] == 'river':
            frac = 0.80 if om.is_calling_station else SIZE_BIG
        else:
            frac = _pick_size(c)
        return _act({"action": "raise", "amount": _open_bet(c, frac)}, "monster value bet")
    return _act({"action": "check"}, "monster check")


def _play_strong(c):
    if c['owed'] > 0:
        if c['eq'] > 0.78 and _can_raise(c) and random.random() < 0.35:
            return _act({"action": "raise", "amount": _raise_over(c, SIZE_BIG)}, "strong raise")
        return _act({"action": "call"}, "strong call")
    if _can_raise(c):
        return _act({"action": "raise", "amount": _open_bet(c, _pick_size(c))}, "strong value bet")
    return _act({"action": "check"}, "strong check")


def _play_good(c):
    eq, po, draw, om = c['eq'], c['po'], c['draw'], c['om']
    bi = c['bi']
    if c['owed'] > 0:
        if eq > po + 0.05:
            return _act({"action": "call"}, "good call")
        if draw in ('combo', 'flush', 'oesd') and eq > po - 0.08:
            return _act({"action": "call"}, "good + draw call")
        return _act({"action": "fold"}, "good fold")
    if om.is_check_raise_heavy and eq < 0.75:
        return _act({"action": "check"}, "check vs check-raiser")
    if bi.get('caller_favored') and not draw:
        return _act({"action": "check"}, "caller's board, pot control")
    if bi.get('wet') and not c['is_dealer'] and not we_raised_preflop:
        return _act({"action": "check"}, "wet OOP, no aggression")
    if not we_raised_preflop and eq < 0.65:
        return _act({"action": "check"}, "no c-bet rights")
    if _can_raise(c) and (c['street'] != 'river' or eq > 0.63):
        frac = SIZE_BIG if om.is_calling_station else _pick_size(c)
        return _act({"action": "raise", "amount": _open_bet(c, frac)}, "good value bet")
    return _act({"action": "check"}, "good check")


def _play_marginal(c):
    eq, po, draw = c['eq'], c['po'], c['draw']
    sd = draw in ('combo', 'flush', 'oesd')
    st = c['street']
    if c['owed'] > 0:
        if eq > po + 0.03:
            return _act({"action": "call"}, "marginal call")
        if sd and st != 'river' and eq > po - 0.10:
            return _act({"action": "call"}, "draw call")
        if draw == 'combo' and st == 'flop' and _can_raise(c) and random.random() < 0.50:
            return _act({"action": "raise", "amount": _raise_over(c, SIZE_BIG)}, "semi-bluff raise")
        return _act({"action": "fold"}, "marginal fold")
    if draw and st != 'river' and _can_raise(c):
        if not (we_raised_preflop or c['is_dealer']):
            return _act({"action": "check"}, "draw, no c-bet rights")
        if draw == 'combo' and random.random() < 0.65:
            return _act({"action": "raise", "amount": _open_bet(c, SIZE_BIG)}, "semi-bluff combo")
        if sd and random.random() < 0.45:
            return _act({"action": "raise", "amount": _open_bet(c, SIZE_BIG)}, "semi-bluff draw")
    return _act({"action": "check"}, "marginal check")


def _play_weak(c):
    eq, po, om, bi, st = c['eq'], c['po'], c['om'], c['bi'], c['street']
    if c['owed'] > 0:
        if po < 0.15 and eq > 0.25:
            return _act({"action": "call"}, "super cheap call")
        return _act({"action": "fold"}, "weak fold")
    if not _can_raise(c):
        return _act({"action": "check"}, "weak check")
    if not we_raised_preflop:
        return _act({"action": "check"}, "no c-bet rights")
    if bi.get('caller_favored'):
        return _act({"action": "check"}, "caller's board, no bluff")
    wet = bi.get('wet')
    fr = om.get_fold_to_bet(st)
    bluff_frac = SIZE_BIG if wet else SIZE_SMALL
    be_threshold = bluff_frac / (1 + bluff_frac)     # break-even fold frequency
    if fr < be_threshold + 0.05:
        return _act({"action": "check"}, "bluff -EV")
    freq = 0.25 if wet else 0.40
    if st == 'turn' and bi.get('raiser_favored'):
        freq += 0.10
    elif st == 'river':
        freq -= 0.10
    if random.random() < freq:
        return _act({"action": "raise", "amount": _open_bet(c, bluff_frac)}, "c-bet bluff")
    return _act({"action": "check"}, "bluff randomized out")


def postflop_decision(my_cards, community, street, pot, owed, can_check, can_raise,
                      min_r, max_r, stack, opp_stack, seven_two, om, is_dealer, cur_bet):
    opp_vpip = om.vpip if (owed > 0 and om.hands_seen >= 10) else None
    equity = calc_equity(my_cards, community, 1500, opp_vpip=opp_vpip)
    equity = shade_equity(equity, owed, pot, stack, om)
    bi = analyze_board(community)
    wet = bi['wet']
    draw = has_draw(my_cards, community) if street != 'river' else None
    spr = min(stack, opp_stack) / max(pot, 1)
    po = owed / (pot + owed) if owed > 0 else 0.0

    dbg(f"  [{street}] eq={equity:.0%} wet={wet} draw={draw} owed={owed} pot={pot}")

    c = {'pot': pot, 'owed': owed, 'cc': can_check, 'cr': can_raise, 'mn': min_r,
         'mx': max_r, 'cur': cur_bet, 'street': street, 'bi': bi, 'om': om,
         'is_dealer': is_dealer, 'eq': equity, 'draw': draw, 'spr': spr, 'po': po}

    # 7-2: barrel when nobody has bet; fold to resistance via normal logic
    if seven_two and owed == 0 and can_raise and max_r > 0 and equity < 0.55 \
            and not om.is_calling_station:
        if (we_raised_preflop or random.random() < 0.5) and random.random() < 0.85:
            return _act({"action": "raise", "amount": _open_bet(c, 0.75)}, "7-2 barrel")

    bump = 0.03 if wet else 0.0
    if equity > 0.85 + bump:
        return _play_monster(c)
    if equity > 0.70 + bump:
        return _play_strong(c)
    if equity > 0.55 + bump:
        return _play_good(c)
    if equity > 0.40 or draw:
        return _play_marginal(c)
    return _play_weak(c)


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
def _decide_inner(gs):
    global opp_model, we_raised_preflop

    if gs.get("type") == "warmup":
        opp_model = OpponentModel()
        we_raised_preflop = False
        return {"action": "check"}

    my_cards = gs["your_cards"]
    community = gs.get("community_cards", [])
    street = gs.get("street") or get_street(community)
    pot = gs["pot"]
    stack = gs["your_stack"]
    owed = gs["amount_owed"]
    can_check = gs["can_check"]
    min_r = gs.get("min_raise_to", 0)
    my_seat = gs.get("seat_to_act", 0)
    button = gs.get("button_seat", 0)
    action_log = gs.get("action_log", [])
    match_log = gs.get("match_action_log", [])
    my_bet_st = gs.get("your_bet_this_street", 0)
    bb = max(gs.get("blinds", {}).get("bb", 100), 1)
    hand_num = gs.get("hand_num", 0)

    opp_stack = stack
    for pl in gs.get("players", []):
        if pl["seat"] != my_seat:
            opp_stack = pl["stack"]
            break

    can_raise = min_r > 0 and stack > owed
    max_r = stack + my_bet_st if can_raise else 0
    is_dealer = (my_seat == button)
    stack_bb = min(stack, opp_stack) / bb
    cur_bet = my_bet_st + owed

    we_raised_preflop = any(
        e.get('seat') == my_seat and e.get('street') == 'preflop'
        and e.get('action') in ('raise', 'all_in') for e in action_log)

    opp_model.update(match_log, my_seat, hand_num)

    tier = get_tier(my_cards)
    seven_two = _is_seven_two(my_cards)

    if street == 'preflop':
        if stack_bb <= 12:
            r = push_fold_decision(tier, is_dealer, stack_bb, stack, can_raise, can_check,
                                   owed, seven_two, my_cards, opp_model)
            if r is not None:
                return r
        return preflop_decision(tier, is_dealer, seven_two, pot, owed, can_check, can_raise,
                                min_r, max_r, stack, bb, action_log, opp_model, cur_bet)

    return postflop_decision(my_cards, community, street, pot, owed, can_check, can_raise,
                             min_r, max_r, stack, opp_stack, seven_two, opp_model,
                             is_dealer, cur_bet)


def decide(game_state: dict) -> dict:
    try:
        return _decide_inner(game_state)
    except Exception as e:
        dbg(f"  !!! ERROR: {e}")
        if game_state.get("type") == "warmup":
            return {"action": "check"}
        if game_state.get("can_check"):
            return {"action": "check"}
        owed = game_state.get("amount_owed", 0)
        if 0 < owed <= game_state.get("pot", 1) * 0.2:
            return {"action": "call"}
        return {"action": "fold"}
