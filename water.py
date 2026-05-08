import math, time, sys, os, random

HIDE  = '\033[?25l'
SHOW  = '\033[?25h'

SPEED      = 9.0
WAVELENGTH = 7.5
DECAY_TIME = 0.22
DECAY_DIST = 0.045
CREST_T    = 0.80   # render only near sin-peak → thin rings
FADE_LOW   = 0.08   # below this: start dissolving
FADE_ZERO  = 0.004  # below this: nothing (wider fade zone)


class Drop:
    def __init__(self, x, y, t, strength=1.0):
        self.x, self.y, self.born = x, y, t
        self.life     = random.uniform(4.5, 6.0)
        self.strength = strength
        self.seed     = random.uniform(0, math.tau)


def wave_components(d, px, py, t):
    age = t - d.born
    if age < 0: return None
    dx   = px - d.x
    dy   = (py - d.y) * 2.0
    dist = math.sqrt(dx*dx + dy*dy)
    if dist < 0.5 or age < dist / SPEED: return None
    angle  = math.atan2(dy, dx)
    wobble = (math.sin(angle * 2.0 + d.seed) * 0.7 +
              math.sin(angle * 3.1 + d.seed * 1.5) * 0.4)
    dist_w = dist + wobble * math.exp(-dist * 0.05) * 2.2
    phase  = (dist_w - SPEED * age) * (2 * math.pi / WAVELENGTH)
    sin_v  = math.sin(phase)
    env_v  = math.exp(-age * DECAY_TIME) * math.exp(-dist * DECAY_DIST) * d.strength
    return sin_v, env_v, px - d.x, py - d.y


def ring_char(dx_raw, dy_raw, env):
    """
    Same logic for every ring. Chars degrade with amplitude.
    Horizontal segments: ~ or -
    Everything else: · or ˙  (no sticks)
    """
    # Tangent to visual circle at this pixel
    tang = math.degrees(math.atan2(-dy_raw, dx_raw)) % 180
    if tang > 90: tang = 180 - tang   # normalize 0-90°

    # Sparkle only on strong rings
    if env > 0.44 and random.random() < 0.02:
        return random.choice(['✦', '⋆', '∗'])

    # Amplitude-based degradation: same for all rings
    if env < 0.13: return '˙'         # very weak — barely there
    if env < 0.22: return '·'         # weak — light dot

    # Normal strength: horizontal → line chars, rest → dot
    if tang < 30:                      # horizontal ring segment
        return '~' if env > 0.38 else '-'
    else:                              # diagonal + vertical → dot, never sticks
        return '·'


class Stone:
    STONE_CHARS = '◆●◉'

    def __init__(self):
        self.active = False

    def launch(self, cols, rows, t):
        self.active  = True
        self.start_t = t
        self.cols    = cols
        self.rows    = rows
        self.char    = random.choice(self.STONE_CHARS)
        self.x0      = cols * random.uniform(0.03, 0.10)   # always from left
        self.y0      = random.uniform(rows * 0.30, rows * 0.70)

        # Throw type: bad luck / normal / lucky (flies off screen)
        throw = random.choices(
            ['short', 'normal', 'lucky'],
            weights=[0.35, 0.50, 0.15]
        )[0]
        self.fly_off   = (throw == 'lucky')
        self.throw_type = throw

        if throw == 'short':
            # Few skips, sinks early on screen
            self.vy = random.uniform(-1.5, 1.5)
            self.skip_t = []
            t_s, interval = 0.0, random.uniform(0.40, 0.62)
            while interval >= 0.13:
                self.skip_t.append(t_s)
                t_s += interval
                interval *= random.uniform(0.68, 0.76)
            burst_n = random.randint(2, 4)
            burst_i = interval
            for _ in range(burst_n):
                self.skip_t.append(t_s)
                t_s += burst_i
                burst_i *= random.uniform(0.78, 0.86)
            self.skip_t.append(t_s)
            self.created = set()
            available = cols * random.uniform(0.30, 0.55)
            self.vx   = available / self.skip_t[-1]

        elif throw == 'normal':
            # Fits to screen end
            self.vy = random.uniform(-1.5, 1.5)
            self.skip_t = []
            t_s, interval = 0.0, random.uniform(0.72, 0.92)
            while interval >= 0.13:
                self.skip_t.append(t_s)
                t_s += interval
                interval *= random.uniform(0.70, 0.78)
            burst_n = random.randint(5, 8)
            burst_i = interval
            for _ in range(burst_n):
                self.skip_t.append(t_s)
                t_s += burst_i
                burst_i *= random.uniform(0.78, 0.86)
            self.skip_t.append(t_s)
            self.created = set()
            margin    = cols * 0.08
            available = cols - 2 * margin
            self.vx   = available / self.skip_t[-1]

        else:  # lucky — many skips, fast, exits right edge
            self.vy = random.uniform(-0.8, 0.8)   # flat trajectory
            self.skip_t = []
            t_s, interval = 0.0, random.uniform(0.82, 1.10)
            while interval >= 0.10:
                self.skip_t.append(t_s)
                t_s += interval
                interval *= random.uniform(0.72, 0.80)
            burst_n = random.randint(6, 10)
            burst_i = interval
            for _ in range(burst_n):
                self.skip_t.append(t_s)
                t_s += burst_i
                burst_i *= random.uniform(0.78, 0.86)
            self.skip_t.append(t_s)
            self.created = set()
            self.vx = random.uniform(40, 58)    # fixed fast — exits screen

    def pos(self, t):
        age = t - self.start_t
        if self.fly_off:
            return self.x0 + self.vx * age, self.y0 + self.vy * age
        eff_age = min(age, self.skip_t[-1])
        return self.x0 + self.vx * eff_age, self.y0 + self.vy * eff_age

    def stone_char(self, t):
        if self.fly_off:
            return self.char   # no sinking, just flies off
        age    = t - self.start_t
        last_t = self.skip_t[-1]
        if age < last_t: return self.char
        sink = age - last_t
        if sink < 0.18: return '◆'
        if sink < 0.34: return '◇'
        if sink < 0.48: return '·'
        if sink < 0.58: return '˙'
        return None

    def done(self, t):
        age = t - self.start_t
        px, _ = self.pos(t)
        if self.fly_off:
            return px > self.cols + 4
        if age > self.skip_t[-1] + 0.75: return True
        return px > self.cols + 4   # safety: exited right

    def pending_splashes(self, t):
        age    = t - self.start_t
        result = []
        for i, st in enumerate(self.skip_t):
            if i not in self.created and age >= st:
                px       = self.x0 + self.vx * st
                py       = self.y0 + self.vy * st
                strength = max(0.55, 1.0 - i * 0.06)
                result.append((px, py, strength))
                self.created.add(i)
        return result

    def landing_flash(self, t):
        age = t - self.start_t
        for st in self.skip_t[:-1]:
            if abs(age - st) < 0.12:
                return True
        return False


def render(drops, stone, t, cols, rows):
    lines = []
    sx = sy = -999
    stone_ch = None
    flash = False
    if stone.active:
        fx, fy = stone.pos(t)
        sx, sy = int(round(fx)), int(round(fy))
        stone_ch = stone.stone_char(t)
        flash    = stone.landing_flash(t)

    for y in range(rows):
        row = []
        for x in range(cols):

            if stone.active and x == sx and y == sy and stone_ch is not None:
                row.append('✦' if flash else stone_ch)
                continue

            best_w  = 0.0
            best_dx = best_dy = 0.0
            for d in drops:
                comp = wave_components(d, x, y, t)
                if comp is None: continue
                sin_v, env_v, dxr, dyr = comp
                if sin_v > CREST_T:
                    w = sin_v * env_v
                    if w > best_w:
                        best_w  = w
                        best_dx = dxr
                        best_dy = dyr

            if best_w >= FADE_LOW:
                row.append(ring_char(best_dx, best_dy, best_w))
            elif best_w >= FADE_ZERO:
                # Dissolve: cubic curve = quick drop to sparse, then very slow tail
                # Better hash avoids grid patterns
                p_raw = (best_w - FADE_ZERO) / (FADE_LOW - FADE_ZERO)
                p  = p_raw ** 3
                ph = ((x * 374761393 + y * 668265263) & 0x7FFFFFFF) % 1000
                if ph < int(p * 1000):
                    row.append('˙')
                else:
                    row.append(' ')
            else:
                ch = ' '
                for d in drops:
                    age2  = t - d.born
                    if age2 < 0 or age2 > 0.35: continue
                    dx2   = x - d.x
                    dy2   = (y - d.y) * 2.0
                    dist2 = math.sqrt(dx2*dx2 + dy2*dy2)
                    if   dist2 < 0.9 and age2 < 0.10: ch = '✦'; break
                    elif dist2 < 2.0 and age2 < 0.22: ch = '∗'; break
                    elif dist2 < 3.0 and age2 < 0.35: ch = '·'; break
                row.append(ch)

        lines.append(''.join(row))
    return '\033[H' + '\n'.join(lines)


def main():
    try:
        cols, rows = os.get_terminal_size()
    except:
        cols, rows = 120, 40
    rows -= 1

    drops      = []
    stone      = Stone()
    t          = 0.0
    next_stone = 1.0

    sys.stdout.write('\033[2J' + HIDE)
    try:
        while True:
            if t >= next_stone and not stone.active:
                stone.launch(cols, rows, t)

            if stone.active:
                for px, py, strength in stone.pending_splashes(t):
                    drops.append(Drop(px, py, t, strength))
                if stone.done(t):
                    stone.active = False
                    wait = {'short': (2.5, 5.0), 'normal': (4.0, 7.0), 'lucky': (5.0, 9.0)}
                    lo, hi = wait[stone.throw_type]
                    next_stone = t + random.uniform(lo, hi)

            drops = [d for d in drops if t - d.born < d.life]

            sys.stdout.write(render(drops, stone, t, cols, rows))
            sys.stdout.flush()
            t += 0.05
            time.sleep(0.033)
    finally:
        sys.stdout.write(SHOW + '\033[0m\n')

main()
