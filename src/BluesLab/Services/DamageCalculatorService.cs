using BluesLab.Models;

namespace BluesLab.Services;

public class DamageCalculatorService
{
    // Exact 32-bit single-precision rolls matching PoMaTools / PMEX Game Engine
    private static readonly float[][] DamageRolls =
    [
        // Non-Critical rolls (0.90 to 1.00)
        [
            0.899999976158142f,
            0.910000026226043f,
            0.9200000166893f,
            0.930000007152557f,
            0.939999997615814f,
            0.949999988079071f,
            0.959999978542327f,
            0.970000028610229f,
            0.980000019073486f,
            0.990000009536743f,
            1.0f
        ],
        // Critical rolls (1.35 to 1.50)
        [
            1.3499999046325684f,
            1.3650000095367432f,
            1.3799999952316284f,
            1.3949999809265137f,
            1.409999966621399f,
            1.4249999523162842f,
            1.4399999380111694f,
            1.4550000429153442f,
            1.4700000286102295f,
            1.4850000143051147f,
            1.5f
        ]
    ];

    private static readonly Dictionary<int, double> AtkDefVariation = new()
    {
        [-6] = 0.55, [-5] = 0.58, [-4] = 0.62, [-3] = 0.66, [-2] = 0.71, [-1] = 0.80,
        [0] = 1.00,
        [1] = 1.25, [2] = 1.40, [3] = 1.50, [4] = 1.60, [5] = 1.70, [6] = 1.80
    };

    private static readonly Dictionary<int, double> SpeedVariation = new()
    {
        [-6] = 0.38, [-5] = 0.41, [-4] = 0.45, [-3] = 0.50, [-2] = 0.55, [-1] = 0.66,
        [0] = 1.00,
        [1] = 1.50, [2] = 1.80, [3] = 2.00, [4] = 2.20, [5] = 2.40, [6] = 2.60
    };

    private static readonly Dictionary<string, Dictionary<string, int>> ExRoleBonusMap = new()
    {
        ["Strike"] = new() { ["hp"] = 60, ["atk"] = 40, ["spa"] = 40 },
        ["Strike (Physical)"] = new() { ["hp"] = 60, ["atk"] = 40, ["spa"] = 40 },
        ["Strike (Special)"] = new() { ["hp"] = 60, ["atk"] = 40, ["spa"] = 40 },
        ["Tech"] = new() { ["hp"] = 60, ["def"] = 20, ["spa"] = 20, ["spd"] = 20 },
        ["Support"] = new() { ["hp"] = 60, ["def"] = 40, ["spd"] = 40 },
        ["Sprint"] = new() { ["hp"] = 60, ["atk"] = 20, ["spa"] = 20, ["spe"] = 40 },
        ["Field"] = new() { ["hp"] = 60, ["def"] = 20, ["spd"] = 20, ["spe"] = 40 },
        ["Multi"] = new() { ["hp"] = 60, ["atk"] = 20, ["def"] = 20, ["spa"] = 20, ["spd"] = 20, ["spe"] = 20 }
    };

    public double GetStatVariation(int stage, bool isSpeed = false)
    {
        int clamped = Math.Clamp(stage, -6, 6);
        return isSpeed
            ? (SpeedVariation.TryGetValue(clamped, out var sv) ? sv : 1.0)
            : (AtkDefVariation.TryGetValue(clamped, out var av) ? av : 1.0);
    }

    public Dictionary<string, int> CalcPotentialBonus(int baseRarity, string targetStars)
    {
        if (baseRarity >= 5)
        {
            if (targetStars == "5★")
                return new() { ["hp"] = 0, ["atk"] = 0, ["def"] = 0, ["spa"] = 0, ["spd"] = 0, ["spe"] = 0 };
            return new() { ["hp"] = 100, ["atk"] = 40, ["def"] = 40, ["spa"] = 40, ["spd"] = 40, ["spe"] = 40 };
        }

        int starsGained = 0;
        if (targetStars.Contains("EX") || targetStars.Contains("20/20"))
        {
            starsGained = 5 - baseRarity + 1;
        }
        else
        {
            int target = int.TryParse(new string(targetStars.Where(char.IsDigit).ToArray()), out int parsed) ? parsed : baseRarity;
            starsGained = target - baseRarity;
        }

        if (starsGained <= 0)
            return new() { ["hp"] = 0, ["atk"] = 0, ["def"] = 0, ["spa"] = 0, ["spd"] = 0, ["spe"] = 0 };

        int potentials = starsGained * 20;
        return new()
        {
            ["hp"] = potentials * 2,
            ["atk"] = potentials * 1,
            ["def"] = potentials * 1,
            ["spa"] = potentials * 1,
            ["spd"] = potentials * 1,
            ["spe"] = potentials * 1
        };
    }

    public Dictionary<string, int> GetExRoleBonus(string rawRole)
    {
        if (string.IsNullOrWhiteSpace(rawRole))
            return new();

        string norm = rawRole.Contains(" (") ? rawRole[..rawRole.IndexOf(" (")] : rawRole;
        if (ExRoleBonusMap.TryGetValue(norm, out var b1)) return b1;
        if (ExRoleBonusMap.TryGetValue(rawRole, out var b2)) return b2;
        return new();
    }

    public Dictionary<string, int> GetSaSupportFlatBonus(int saLevel)
    {
        int hp = 0, def = 0, spd = 0;
        if (saLevel >= 2) hp += 50;
        if (saLevel >= 3) { def += 20; spd += 20; }
        if (saLevel >= 4) hp += 100;
        return new() { ["hp"] = hp, ["def"] = def, ["spd"] = spd };
    }

    public int GetSaMovePowerBonus(int saLevel, string role, bool isSync)
    {
        string r = role.ToLowerInvariant().Trim();
        bool isStrikeSprint = r.StartsWith("strike") || r.StartsWith("sprint");
        bool isTechField = r.StartsWith("tech") || r.StartsWith("field");

        if (isStrikeSprint)
        {
            if (!isSync)
            {
                if (saLevel >= 4) return 30;
                if (saLevel >= 2) return 10;
            }
            else
            {
                if (saLevel >= 3) return 20;
            }
        }
        else if (isTechField)
        {
            if (isSync)
            {
                if (saLevel >= 4) return 40;
                if (saLevel >= 2) return 10;
            }
            else
            {
                if (saLevel >= 3) return 20;
            }
        }
        return 0;
    }

    public int CalcPower(int basePower, int moveLevel, int saBonus = 0, double increment = 1.0)
    {
        int scaled = (int)Math.Floor(basePower * (100.0 + (moveLevel - 1) * 5 + saBonus) / 100.0);
        return (int)Math.Floor(scaled * increment);
    }

    public int CalcTotalStat(
        string stat,
        int jsonStat,
        int stage,
        int potential = 0,
        int exBonus = 0,
        double formMult = 1.0,
        bool hasSa = false,
        int saLevel = 0,
        string role = "",
        int gear = 0,
        int gridStat = 0,
        bool isBurned = false,
        int mitigation = 0,
        bool critOffense = false,
        bool critDefense = false)
    {
        int baseVal = jsonStat;
        if (hasSa && saLevel >= 1)
        {
            baseVal = (int)Math.Ceiling(baseVal * 1.1) + (baseVal % 10 != 0 ? -1 : 0);
        }
        if (hasSa && role.Trim().Equals("Support", StringComparison.OrdinalIgnoreCase))
        {
            var saFlat = GetSaSupportFlatBonus(saLevel);
            if (saFlat.TryGetValue(stat, out int fb))
                baseVal += fb;
        }

        int rawBase = baseVal + potential + exBonus;
        int afterMult;
        if (Math.Abs(formMult - 1.0) < 0.0001)
        {
            afterMult = rawBase + gear;
        }
        else
        {
            double scaledVal = (rawBase + gear) * formMult;
            afterMult = (int)Math.Floor(scaledVal);
        }

        int beforeStage = afterMult + gridStat;

        // When critical defense, defender ignores positive defense buffs
        if (critDefense && stage > 0)
        {
            stage = 0;
        }

        double variation = GetStatVariation(stage, stat == "spe");
        if (stage < 0 && mitigation > 0)
        {
            double mit = mitigation * 0.1;
            variation = 1.0 - (1.0 - variation) * (1.0 - mit);
        }

        if (isBurned && stat == "atk")
        {
            variation *= 0.8;
        }

        int calculated = (int)Math.Floor(beforeStage * variation);

        // When critical offense, attacker ignores negative stat stages
        if (critOffense)
        {
            int basePlusGrid = beforeStage;
            return Math.Max(calculated, basePlusGrid);
        }

        return Math.Max(1, calculated);
    }

    public DamageResult CalculateDamage(
        MoveItem move,
        CombatantState ally,
        CombatantState enemy,
        FieldState field,
        DamageRulesDocument rules,
        HashSet<long> activeGridCells)
    {
        var pills = new List<MultiplierPill>();
        var pair = ally.Pair;
        if (pair == null) return new DamageResult { MoveName = move.Name };

        bool isPhysical = string.Equals(move.Category, "Physical", StringComparison.OrdinalIgnoreCase);
        bool isSpecial = string.Equals(move.Category, "Special", StringComparison.OrdinalIgnoreCase);

        // 1. Move Base Power & SA
        int rawPower = int.TryParse(move.Power, out int parsedPwr) ? parsedPwr : 0;
        int saBonus = pair.HasSuperAwakening ? GetSaMovePowerBonus(ally.SuperAwakeningLevel, pair.Role, move.IsSync) : 0;
        bool isTechExSync = move.IsSync && (pair.Role.StartsWith("Tech", StringComparison.OrdinalIgnoreCase) ||
            (ally.HasExRole && pair.ExRole.StartsWith("Tech", StringComparison.OrdinalIgnoreCase)));
        double syncIncrement = isTechExSync ? 1.5 : 1.0;

        int power = CalcPower(rawPower, ally.MoveLevel, saBonus, syncIncrement);

        // Grid Power
        int gridPower = 0;
        foreach (var cell in pair.Grid)
        {
            if (activeGridCells.Contains(cell.CellId))
            {
                foreach (var (pbMove, pbVal) in cell.PowerBonus)
                {
                    if (MatchesMoveName(move.Name, pbMove, move.IsSync))
                    {
                        gridPower += pbVal;
                    }
                }
            }
        }

        int baseMovePower = power + gridPower;

        // Passive skill power ups + Master Skills + PMUN/SMUN stacks
        int passivePercentage = (int)Math.Round(EvalPassivePowerUps(move, ally, enemy, field, rules, activeGridCells, pills) * 100);
        int masterPercentage = (int)Math.Round(EvalMasterPassives(move, ally, rules) * 100);
        if (masterPercentage > 0)
        {
            pills.Add(new MultiplierPill { Label = "Master Passive", Value = $"+{masterPercentage}%", Color = "#9b59b6" });
        }

        int boostNextPercentage = 0;
        if (isPhysical) boostNextPercentage += ally.PhysicalBoostNext * 40;
        if (isSpecial) boostNextPercentage += ally.SpecialBoostNext * 40;
        if (move.IsSync) boostNextPercentage += ally.SyncMoveBoostNext * 40;

        int totalPowerupPercent = 100 + passivePercentage + masterPercentage + boostNextPercentage;

        // Innate Move Scaling (move_scaling.json, base 1000)
        int innateModifier1000 = (int)Math.Round(EvalMoveScaling(move, ally, enemy, field, rules, pills) * 1000);

        int battlePower = (int)Math.Floor(Math.Floor((double)baseMovePower * totalPowerupPercent / 100.0) * innateModifier1000 / 1000.0);

        pills.Insert(0, new MultiplierPill { Label = "Move Power", Value = $"{battlePower}", Color = "#2ecc71" });

        // 2. Attacker Stat (Offense) with Form Scale
        string atkStatKey = isPhysical ? "atk" : "spa";
        int jsonAtkStat = pair.Stats.GetStatAtLevel(atkStatKey, int.TryParse(ally.CharLevel, out int cl) ? cl : 140);
        var potBonus = CalcPotentialBonus(pair.Rarity, ally.StarLevel);
        int exAtkBonus = ally.HasExRole ? GetExRoleBonus(pair.ExRole).GetValueOrDefault(atkStatKey, 0) : 0;
        
        double formStatMult = 1.0;
        if (ally.FormIndex > 0 && ally.FormIndex <= pair.Variations.Count)
        {
            var variation = pair.Variations[ally.FormIndex - 1];
            formStatMult = variation.StatMultiplier.GetValueOrDefault(atkStatKey, 1.0);
            if (formStatMult > 1.0)
            {
                pills.Add(new MultiplierPill { Label = $"{variation.FormName} Stat", Value = $"×{formStatMult:0.#}", Color = "#f39c12" });
            }
        }

        int gridAtkStat = 0;
        foreach (var cell in pair.Grid)
        {
            if (activeGridCells.Contains(cell.CellId) && cell.StatBonus.TryGetValue(atkStatKey, out int sb))
            {
                gridAtkStat += sb;
            }
        }

        int attackerStat = CalcTotalStat(
            atkStatKey,
            jsonAtkStat,
            ally.Stages.GetValueOrDefault(atkStatKey, 0),
            potential: potBonus.GetValueOrDefault(atkStatKey, 0),
            exBonus: exAtkBonus,
            formMult: formStatMult,
            hasSa: pair.HasSuperAwakening,
            saLevel: ally.SuperAwakeningLevel,
            role: pair.Role,
            gear: ally.Gear.GetValueOrDefault(atkStatKey, 0),
            gridStat: gridAtkStat,
            isBurned: ally.StatusCondition == "burned",
            critOffense: ally.IsCriticalMove
        );

        pills.Add(new MultiplierPill { Label = "Atk Stat", Value = $"{attackerStat}", Color = "#3498db" });

        // 3. Defender Stat (Defense)
        string defStatKey = isPhysical ? "def" : "spd";
        int jsonDefStat = enemy.ManualStats.GetValueOrDefault(defStatKey, 95);
        int defenderStat = CalcTotalStat(
            defStatKey,
            jsonDefStat,
            enemy.Stages.GetValueOrDefault(defStatKey, 0),
            mitigation: enemy.Mitigations.GetValueOrDefault(defStatKey, 0),
            critDefense: ally.IsCriticalMove
        );

        // 4. Exact Fractional Multipliers Product (Numerator `ne` & Denominator `he`)
        double ne = 1.0;
        double he = 1.0;

        // Weather, Terrain, Zone
        if (!string.IsNullOrEmpty(field.Weather))
        {
            ne *= 3.0;
            he *= field.WeatherEx ? 1.0 : 2.0;
            pills.Add(new MultiplierPill { Label = field.Weather, Value = field.WeatherEx ? "×3.0" : "×1.5", Color = "#d35400" });
        }
        if (!string.IsNullOrEmpty(field.Terrain))
        {
            ne *= 3.0;
            he *= field.TerrainEx ? 1.0 : 2.0;
            pills.Add(new MultiplierPill { Label = field.Terrain, Value = field.TerrainEx ? "×3.0" : "×1.5", Color = "#27ae60" });
        }
        if (!string.IsNullOrEmpty(field.Zone))
        {
            ne *= 3.0;
            he *= field.ZoneEx ? 1.0 : 2.0;
            pills.Add(new MultiplierPill { Label = field.Zone, Value = field.ZoneEx ? "×3.0" : "×1.5", Color = "#8e44ad" });
        }

        // Type Effectiveness
        bool isSuperEffective = !string.IsNullOrEmpty(enemy.Weakness) &&
            string.Equals(move.Type, enemy.Weakness, StringComparison.OrdinalIgnoreCase);

        if (isSuperEffective)
        {
            if (ally.SuperEffectiveNext)
            {
                ne *= 3.0;
                pills.Add(new MultiplierPill { Label = "SE Next", Value = "×3.0", Color = "#e74c3c" });
            }
            else
            {
                ne *= 2.0;
                pills.Add(new MultiplierPill { Label = "Super Effective", Value = "×2.0", Color = "#e74c3c" });
            }
        }

        // Sync Buffs: (2 + syncBoosts) / 2
        if (ally.SyncBoosts > 0)
        {
            ne *= (2 + ally.SyncBoosts);
            he *= 2.0;
            pills.Add(new MultiplierPill { Label = "Sync Buffs", Value = $"×{1.0 + ally.SyncBoosts * 0.5:0.#}", Color = "#e67e22" });
        }

        // Target count (AoE scaling)
        if (field.TargetCount > 1 && !move.IsSync)
        {
            if (field.TargetCount == 3)
            {
                he *= 2.0;
                pills.Add(new MultiplierPill { Label = "3 Targets", Value = "×0.5", Color = "#95a5a6" });
            }
            else if (field.TargetCount == 2)
            {
                ne *= 3333.0;
                he *= 5000.0;
                pills.Add(new MultiplierPill { Label = "2 Targets", Value = "×0.66", Color = "#95a5a6" });
            }
        }

        // Type Rebuffs
        int rebuff = enemy.EnemyTypeRebuffs.GetValueOrDefault(move.Type, 0);
        if (rebuff != 0)
        {
            switch (rebuff)
            {
                case -3: ne *= 8.0; he *= 5.0; pills.Add(new MultiplierPill { Label = "Rebuff -3", Value = "×1.6", Color = "#6c5ce7" }); break;
                case -2: ne *= 3.0; he *= 2.0; pills.Add(new MultiplierPill { Label = "Rebuff -2", Value = "×1.5", Color = "#6c5ce7" }); break;
                case -1: ne *= 13.0; he *= 10.0; pills.Add(new MultiplierPill { Label = "Rebuff -1", Value = "×1.3", Color = "#6c5ce7" }); break;
                case 1: ne *= 10.0; he *= 13.0; break;
                case 2: ne *= 3333.0; he *= 5000.0; break;
                case 3: ne *= 5.0; he *= 8.0; break;
            }
        }

        // Circles
        foreach (var region in CombatantState.CircleRegions)
        {
            int allies = Math.Clamp(ally.CircleAllyCount.GetValueOrDefault(region, 0), 0, 3);
            var active = ally.CircleActive.GetValueOrDefault(region);
            if (active != null)
            {
                if (active.GetValueOrDefault("physical") && isPhysical)
                {
                    ne *= 110.0 + 10.0 * allies;
                    he *= 100.0;
                    pills.Add(new MultiplierPill { Label = $"{region} Circle (Phys)", Value = $"×{(110.0 + 10.0 * allies) / 100.0:0.##}", Color = "#00cec9" });
                }
                if (active.GetValueOrDefault("special") && !isPhysical)
                {
                    ne *= 110.0 + 10.0 * allies;
                    he *= 100.0;
                    pills.Add(new MultiplierPill { Label = $"{region} Circle (Spec)", Value = $"×{(110.0 + 10.0 * allies) / 100.0:0.##}", Color = "#00cec9" });
                }
                if (active.GetValueOrDefault("defensive"))
                {
                    ne *= 105.0 + 5.0 * allies;
                    he *= 100.0;
                }
            }
        }

        // Breaks
        if (isPhysical && ally.PhysicalBreak) { ne *= 3.0; he *= 2.0; pills.Add(new MultiplierPill { Label = "Phys Break", Value = "×1.5", Color = "#e84393" }); }
        if (isSpecial && ally.SpecialBreak) { ne *= 3.0; he *= 2.0; pills.Add(new MultiplierPill { Label = "Spec Break", Value = "×1.5", Color = "#e84393" }); }

        // 5. Final Roll Computation (Math.fround matching PMEX engine)
        ne *= attackerStat;
        he *= defenderStat * 2.0;

        float baseFactor = (float)((double)battlePower * ne / he);
        int rollIndex = ally.IsCriticalMove ? 1 : 0;
        var rolls = new List<int>();

        for (int l = 0; l < 10; l++)
        {
            float rollVal = DamageRolls[rollIndex][l] * baseFactor;
            rolls.Add((int)Math.Floor(rollVal));
        }

        // Last 100% roll
        double lastRollVal = DamageRolls[rollIndex][10] * (double)battlePower * ne / he;
        rolls.Add((int)Math.Floor(lastRollVal));

        if (ally.IsCriticalMove)
        {
            pills.Add(new MultiplierPill { Label = "Crit", Value = "×1.5", Color = "#f1c40f" });
        }

        return new DamageResult
        {
            MoveName = move.Name,
            BasePower = rawPower,
            ScaledMovePower = battlePower,
            AttackerStat = attackerStat,
            DefenderStat = defenderStat,
            StatRatio = (double)attackerStat / (defenderStat * 2.0),
            BattleMultiplier = (ne / attackerStat) / (he / (defenderStat * 2.0)),
            Rolls = rolls,
            Breakdown = pills
        };
    }

    private double EvalMasterPassives(MoveItem move, CombatantState ally, DamageRulesDocument rules)
    {
        double total = 0.0;
        if (ally.Pair == null) return total;

        foreach (var mp in rules.MasterPassives.Where(m => string.Equals(m.SyncPair, ally.Pair.DisplayName, StringComparison.OrdinalIgnoreCase)))
        {
            if (mp.AppliesToMove(move))
            {
                int allies = ally.MasterPassiveAllyCount.GetValueOrDefault(mp.PassiveName, 0);
                total += mp.PowerUpForAdditionalAllies(allies);
            }
        }
        return total;
    }

    private double EvalPassivePowerUps(
        MoveItem move,
        CombatantState ally,
        CombatantState enemy,
        FieldState field,
        DamageRulesDocument rules,
        HashSet<long> activeGridCells,
        List<MultiplierPill> pills)
    {
        double total = 0.0;

        // Lucky Skill
        if (!string.IsNullOrEmpty(ally.LuckySkillName))
        {
            var lucky = rules.DamagePassives.FirstOrDefault(dp => string.Equals(dp.Name, ally.LuckySkillName, StringComparison.OrdinalIgnoreCase));
            if (lucky != null)
            {
                double v = EvalSingleDamagePassive(lucky, move, ally, enemy, field);
                if (v > 0)
                {
                    total += v;
                    pills.Add(new MultiplierPill { Label = $"Lucky: {lucky.Name}", Value = $"+{v * 100:0.#}%", Color = "#f39c12" });
                }
            }
        }

        // Innate / Variation Passives
        if (ally.Pair != null)
        {
            var passivesList = (ally.FormIndex > 0 && ally.FormIndex <= ally.Pair.Variations.Count && ally.Pair.Variations[ally.FormIndex - 1].Passives.Count > 0)
                ? ally.Pair.Variations[ally.FormIndex - 1].Passives
                : ally.Pair.Passives;

            foreach (var p in passivesList)
            {
                var rule = rules.DamagePassives.FirstOrDefault(dp => string.Equals(dp.Name, p.Name, StringComparison.OrdinalIgnoreCase));
                if (rule != null)
                {
                    double v = EvalSingleDamagePassive(rule, move, ally, enemy, field);
                    if (v > 0)
                    {
                        total += v;
                        pills.Add(new MultiplierPill { Label = rule.Name, Value = $"+{v * 100:0.#}%", Color = "#16a085" });
                    }
                }
            }

            // Grid Passives
            foreach (var cell in ally.Pair.Grid)
            {
                if (!activeGridCells.Contains(cell.CellId) || string.IsNullOrEmpty(cell.Title)) continue;
                string cleanTitle = cell.Title.Contains(":") ? cell.Title.Substring(cell.Title.IndexOf(":") + 1).Trim() : cell.Title.Trim();
                var rule = rules.DamagePassives.FirstOrDefault(dp =>
                    string.Equals(dp.Name, cell.Title.Trim(), StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(dp.Name, cleanTitle, StringComparison.OrdinalIgnoreCase));
                if (rule != null)
                {
                    double v = EvalSingleDamagePassive(rule, move, ally, enemy, field);
                    if (v > 0)
                    {
                        total += v;
                        pills.Add(new MultiplierPill { Label = $"Grid: {rule.Name}", Value = $"+{v * 100:0.#}%", Color = "#16a085" });
                    }
                }
            }
        }

        return total;
    }

    private double EvalSingleDamagePassive(
        DamagePassiveRule dp,
        MoveItem move,
        CombatantState ally,
        CombatantState enemy,
        FieldState field)
    {
        if (move.IsSync && string.Equals(dp.AppliesTo, "moves", StringComparison.OrdinalIgnoreCase)) return 0;
        if (!move.IsSync && string.Equals(dp.AppliesTo, "sync_move", StringComparison.OrdinalIgnoreCase)) return 0;

        return dp.Mechanism switch
        {
            "user_stat_raised" => CalcStatScaling(dp.Stat, ally.Stages, true, move.IsSync),
            "target_stat_lowered" => CalcStatScaling(dp.Stat, enemy.Stages, false, move.IsSync),
            "stat_is_raised" => (ally.Stages.GetValueOrDefault(dp.Stat, 0) > 0 ? dp.Value * 0.1 : 0),
            "stat_is_lowered" => (enemy.Stages.GetValueOrDefault(dp.Stat, 0) < 0 ? dp.Value * 0.1 : 0),
            "flat_boost" => (EvalConditions(dp.Conditions, field, enemy) ? dp.Value * 0.1 : 0),
            _ => 0
        };
    }

    private double CalcStatScaling(string statKey, Dictionary<string, int> stages, bool isRaised, bool isSync)
    {
        if (statKey == "all_stats")
        {
            int count = 0;
            foreach (var k in new[] { "atk", "def", "spa", "spd", "spe", "acc", "eva" })
            {
                int s = stages.GetValueOrDefault(k, 0);
                count += isRaised ? Math.Clamp(s, 0, 6) : Math.Clamp(-s, 0, 6);
            }
            double step = isSync ? 0.0667 : 0.026;
            double max = isSync ? 1.2 : 1.1;
            return Math.Clamp(Math.Round(count * step, 2), 0.0, max);
        }
        else
        {
            int s = stages.GetValueOrDefault(statKey, 0);
            int count = isRaised ? Math.Clamp(s, 0, 6) : Math.Clamp(-s, 0, 6);
            double step = isSync ? 0.167 : 0.05;
            double max = isSync ? 1.0 : 0.3;
            return Math.Clamp(Math.Round(count * step, 2), 0.0, max);
        }
    }

    private bool EvalConditions(List<List<string>> conditionGroups, FieldState field, CombatantState enemy)
    {
        if (conditionGroups.Count == 0) return true;
        foreach (var andGroup in conditionGroups)
        {
            bool allMatch = true;
            foreach (var c in andGroup)
            {
                bool match = c switch
                {
                    "sunny" => field.Weather == "Sunny",
                    "rain" => field.Weather == "Rainy",
                    "sandstorm" => field.Weather == "Sandstorm",
                    "hail" => field.Weather == "Hail",
                    "burned" => enemy.StatusCondition == "burned",
                    "paralyzed" => enemy.StatusCondition == "paralyzed",
                    "poisoned" => enemy.StatusCondition == "poisoned" || enemy.StatusCondition == "badly poisoned",
                    "frozen" => enemy.StatusCondition == "frozen",
                    "asleep" => enemy.StatusCondition == "asleep",
                    "confused" => enemy.VolatileStatus.GetValueOrDefault("confused", false),
                    "trapped" => enemy.VolatileStatus.GetValueOrDefault("trapped", false),
                    "flinching" => enemy.VolatileStatus.GetValueOrDefault("flinching", false),
                    _ => true
                };
                if (!match) { allMatch = false; break; }
            }
            if (allMatch) return true;
        }
        return false;
    }

    private double EvalMoveScaling(
        MoveItem move,
        CombatantState ally,
        CombatantState enemy,
        FieldState field,
        DamageRulesDocument rules,
        List<MultiplierPill> pills)
    {
        if (ally.Pair == null) return 1.0;

        var rule = rules.MoveScaling.FirstOrDefault(ms =>
            (string.Equals(ms.SyncPair, ally.Pair.DisplayName, StringComparison.OrdinalIgnoreCase) || ms.SyncPair == "*") &&
            string.Equals(ms.MoveName, move.Name, StringComparison.OrdinalIgnoreCase));

        if (rule == null)
        {
            if (move.IsSync && move.Description.Contains("more the target’s Defense is lowered", StringComparison.OrdinalIgnoreCase))
            {
                int defStage = enemy.Stages.GetValueOrDefault("def", 0);
                if (defStage < 0)
                {
                    double m = 1.0 + Math.Abs(defStage) * (1.0 / 6.0);
                    pills.Add(new MultiplierPill { Label = "Sync Scaling (Def-)", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    return m;
                }
            }
            if (move.IsSync && move.Description.Contains("more the target’s Speed is lowered", StringComparison.OrdinalIgnoreCase))
            {
                int speStage = enemy.Stages.GetValueOrDefault("spe", 0);
                if (speStage < 0)
                {
                    double m = 1.0 + Math.Abs(speStage) * (1.0 / 6.0);
                    pills.Add(new MultiplierPill { Label = "Sync Scaling (Spe-)", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    return m;
                }
            }
            return 1.0;
        }

        var stages = rule.Who == "user" ? ally.Stages : enemy.Stages;
        bool isRaised = rule.Direction == "raised";
        int count = 0;

        if (rule.Stat == "all_stats")
        {
            foreach (var k in new[] { "atk", "def", "spa", "spd", "spe", "acc", "eva" })
            {
                int s = stages.GetValueOrDefault(k, 0);
                count += isRaised ? Math.Clamp(s, 0, 6) : Math.Clamp(-s, 0, 6);
            }
        }
        else
        {
            int s = stages.GetValueOrDefault(rule.Stat, 0);
            count = isRaised ? Math.Clamp(s, 0, 6) : Math.Clamp(-s, 0, 6);
        }

        double step = rule.StepPer1000 / 1000.0;
        double mult = 1.0 + count * step;
        if (rule.CapPer1000 > 0)
        {
            mult = Math.Clamp(mult, 0.0, rule.CapPer1000 / 1000.0);
        }

        if (mult > 1.0)
        {
            pills.Add(new MultiplierPill { Label = $"Move Scaling ({rule.Stat})", Value = $"×{mult:0.##}", Color = "#fd79a8" });
        }

        return mult;
    }

    private static bool MatchesMoveName(string moveName, string targetName, bool isSync)
    {
        if (string.Equals(moveName, targetName, StringComparison.OrdinalIgnoreCase)) return true;
        string normMove = moveName.Replace("\r", "").Replace("\n", " ").Trim();
        string normTarget = targetName.Replace("\r", "").Replace("\n", " ").Trim();
        if (string.Equals(normMove, normTarget, StringComparison.OrdinalIgnoreCase)) return true;
        if (isSync && (normTarget.EndsWith("Sync Beam", StringComparison.OrdinalIgnoreCase) ||
                       normTarget.EndsWith("Sync Impact", StringComparison.OrdinalIgnoreCase) ||
                       normTarget.EndsWith("Tera Blast", StringComparison.OrdinalIgnoreCase) ||
                       normMove.Contains(normTarget, StringComparison.OrdinalIgnoreCase) ||
                       normTarget.Contains(normMove, StringComparison.OrdinalIgnoreCase)))
        {
            return true;
        }
        return false;
    }

}