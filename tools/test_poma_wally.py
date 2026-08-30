import math

# Wally base stats at lv 200:
# [hp, atk, def, spa, spd, spe]
base_stats = [825, 388, 259, 648, 262, 314]
# Role of Wally: Tech (role 3 in PMEX)
# In PoMaTools: role bitmask?
# Let's check PoMaTools role representation

def test_poma(move_level, role, ex_role, promo_used, promo_base, potential, ex_unlock):
    # s = [[100,0], ...]
    s = [[100,0] for _ in range(6)]
    
    # if moveLevel > 5:
    if move_level > 5:
        for f in range(6):
            s[f][0] += 10
        if (2 & role) and move_level > 6:
            s[0][1] += 50
            if move_level > 7:
                s[2][1] += 20
                s[4][1] += 20
                if move_level > 8:
                    s[0][1] += 100

    def o(f_val, m):
        if s[m][0] > 100:
            v = math.ceil(f_val * s[m][0] / 100) + (-1 if (f_val % 10 != 0) else 0)
        else:
            v = f_val
        return v + s[m][1]

    # calculatePotentialStats:
    # 5-star base:
    # statsPotential[0] = 100 * n + 5 * potential
    # statsPotential[1..5] = 40 * n + 2 * potential
    # For 6-star EX (promo_used = 6, promo_base = 5, potential = 0):
    # n = 6 - 5 = 1
    # statsPotential[0] = 100 * 1 + 0 = 100
    # statsPotential[1..5] = 40 * 1 + 0 = 40
    n = promo_used - promo_base
    stats_potential = [100 * n + 5 * potential] + [40 * n + 2 * potential] * 5

    # EX Role Sprint: statsEx = [60, 20, 0, 20, 0, 40]
    # statsEx for Sprint (case 8): [60, 20, 0, 20, 0, 40]
    stats_ex = [60, 20, 0, 20, 0, 40] if ex_unlock else [0, 0, 0, 0, 0, 0]

    # Mega Multipliers:
    # SpA: 120 (1.2), SpD: 120 (1.2), others 100
    mega_mult = [100, 100, 100, 120, 120, 100]

    results = []
    for f in range(6):
        p = o(base_stats[f], f)
        pot = stats_potential[f]
        ex = stats_ex[f]
        y = mega_mult[f]
        P = y
        C = p
        T = pot + ex
        M = 0 # gear
        D = 0 # affinity
        if y == 100:
            val = C + T + M + D
        else:
            # y/100 == 1.2
            # Math.fround(1.2) != 1.2
            # In JS: Math.fround(1.2) is 1.2000000476837158 != 1.2
            # So it uses: Math.ceil((C+T+M+D)*P/100) - 1
            # Wait! Or Math.floor((C+T+M+D)*P/100)?
            val = math.floor((C + T + M + D) * P / 100)
            val_ceil_minus_1 = math.ceil((C + T + M + D) * P / 100) - 1
            print(f"Stat {f}: p={p}, C+T={C+T}, floor={val}, ceil-1={val_ceil_minus_1}")
        results.append((p, val))
    return results

print("=== MOVE LEVEL 10 (SUPER AWAKENING 5) ===")
res = test_poma(10, 4, 8, 6, 5, 0, True)
print("PoMaTools Row 1 expected: [1067, 486, 324, 926, 393, 425]")
print("Computed:", [r[1] for r in res])