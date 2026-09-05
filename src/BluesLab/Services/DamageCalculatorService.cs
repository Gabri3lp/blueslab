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

    public int GetMoveMultiplier(int fullMoveLevel, string role, bool isSync, bool isMax = false)
    {
        if (isMax)
        {
            int baseLvl = Math.Clamp(Math.Min(fullMoveLevel, 5), 1, 5);
            return 100 + (baseLvl - 1) * 5;
        }

        int baseLevel = Math.Clamp(Math.Min(fullMoveLevel, 5), 1, 5);
        int baseMultiplier = 100 + (baseLevel - 1) * 5;

        if (fullMoveLevel <= 5) return baseMultiplier;

        int saLevel = fullMoveLevel - 5;
        string r = role.ToLowerInvariant().Trim();
        bool isStrikeSprintMulti = r.StartsWith("strike") || r.StartsWith("sprint") || r.StartsWith("multi");
        bool isTechField = r.StartsWith("tech") || r.StartsWith("field");

        if (isStrikeSprintMulti)
        {
            if (!isSync)
            {
                if (saLevel >= 4) return 160;
                if (saLevel >= 2) return 130;
            }
            else
            {
                if (saLevel >= 3) return 140;
            }
        }
        else if (isTechField)
        {
            if (isSync)
            {
                if (saLevel >= 4) return 160;
                if (saLevel >= 2) return 130;
            }
            else
            {
                if (saLevel >= 3) return 140;
            }
        }

        return baseMultiplier;
    }

    public int CalcPower(int basePower, int fullMoveLevel, string role, bool isSync, double increment = 1.0, bool isMax = false)
    {
        if (basePower <= 0) return 0;
        int mult = GetMoveMultiplier(fullMoveLevel, role, isSync, isMax);
        int scaled = (int)Math.Floor((double)basePower * mult / 100.0);
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
        bool ignoreBurnPenalty = false,
        int mitigation = 0,
        bool critOffense = false,
        bool critDefense = false,
        double inBattleStatMult = 1.0)
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
            double scaledVal = rawBase * formMult;
            afterMult = (int)Math.Floor(scaledVal) + gear;
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

        if (isBurned && stat == "atk" && !ignoreBurnPenalty)
        {
            variation *= 0.8;
        }

        int calculated = (int)Math.Floor(beforeStage * variation * inBattleStatMult);

        // When critical offense, attacker ignores negative stat stages
        if (critOffense)
        {
            int basePlusGrid = (int)Math.Floor(beforeStage * inBattleStatMult);
            return Math.Max(calculated, basePlusGrid);
        }

        return Math.Max(1, calculated);
    }

    public double GetInBattleStatMultiplier(
        string stat,
        CombatantState combatant,
        FieldState field,
        HashSet<long>? activeGridCells = null,
        List<MultiplierPill>? pills = null)
    {
        double mult = 1.0;
        var pair = combatant.Pair;
        if (pair == null) return mult;

        string s = stat.ToLowerInvariant().Trim();
        var passives = pair.Passives ?? new List<PassiveItem>();
        if (combatant.FormIndex > 0 && pair.Variations != null && combatant.FormIndex <= pair.Variations.Count && pair.Variations[combatant.FormIndex - 1].Passives != null)
        {
            passives = pair.Variations[combatant.FormIndex - 1].Passives;
        }

        bool hasWeather = !string.IsNullOrWhiteSpace(field.Weather) && !field.Weather.Equals("None", StringComparison.OrdinalIgnoreCase);
        bool hasTerrain = !string.IsNullOrWhiteSpace(field.Terrain) && !field.Terrain.Equals("None", StringComparison.OrdinalIgnoreCase);
        bool hasZone = !string.IsNullOrWhiteSpace(field.Zone) && !field.Zone.Equals("None", StringComparison.OrdinalIgnoreCase);
        bool hasField = hasWeather || hasTerrain || hasZone;

        foreach (var ps in passives)
        {
            long pid = ps.Id;
            string pname = ps.Name ?? string.Empty;

            // Weather Buff (23011101): +30% to Atk, Def, SpA, SpD, Spe when weather conditions are in effect
            if (pid == 23011101 || pname.Equals("Weather Buff", StringComparison.OrdinalIgnoreCase) || pname.Contains("Clima Favorable", StringComparison.OrdinalIgnoreCase))
            {
                if (hasWeather && (s == "atk" || s == "def" || s == "spa" || s == "spd" || s == "spe"))
                {
                    mult *= 1.30;
                    pills?.Add(new MultiplierPill { Label = "Weather Buff", Value = "×1.3", Color = "#e67e22" });
                }
            }

            // Sedimentary (23010401): +30% to Def, SpD in Sandstorm
            if (pid == 23010401 || pname.Equals("Sedimentary", StringComparison.OrdinalIgnoreCase))
            {
                if (hasWeather && field.Weather.Equals("Sandstorm", StringComparison.OrdinalIgnoreCase) && (s == "def" || s == "spd"))
                {
                    mult *= 1.30;
                    pills?.Add(new MultiplierPill { Label = "Sedimentary", Value = "×1.3", Color = "#d35400" });
                }
            }

            // Hail and Hearty (23011001): +30% to Def, SpD in Hail
            if (pid == 23011001 || pname.Equals("Hail and Hearty", StringComparison.OrdinalIgnoreCase))
            {
                if (hasWeather && field.Weather.Equals("Hail", StringComparison.OrdinalIgnoreCase) && (s == "def" || s == "spd"))
                {
                    mult *= 1.30;
                    pills?.Add(new MultiplierPill { Label = "Hail and Hearty", Value = "×1.3", Color = "#74b9ff" });
                }
            }

            // Healthy Strength 5 (23010505): +50% to Atk when HP >= 50%
            if (pid == 23010505 || pname.Equals("Healthy Strength 5", StringComparison.OrdinalIgnoreCase) || pname.Contains("Healthy Strength"))
            {
                if (s == "atk")
                {
                    mult *= 1.50;
                    pills?.Add(new MultiplierPill { Label = "Healthy Strength", Value = "×1.5", Color = "#e74c3c" });
                }
            }

            // Fortify 3 (23010903): +30% to Def, SpD when HP <= 50%
            if (pid == 23010903 || pname.Contains("Fortify", StringComparison.OrdinalIgnoreCase))
            {
                if (combatant.HpPercent <= 50 && (s == "def" || s == "spd"))
                {
                    mult *= 1.30;
                    pills?.Add(new MultiplierPill { Label = "Fortify", Value = "×1.3", Color = "#1abc9c" });
                }
            }

            // Allied Field Effect Multiplier 2 (23011502): +20% to all 5 stats
            if (pid == 23011502 || pname.Contains("Allied Field Effect Multiplier", StringComparison.OrdinalIgnoreCase))
            {
                if (hasField && (s == "atk" || s == "def" || s == "spa" || s == "spd" || s == "spe"))
                {
                    mult *= 1.20;
                    pills?.Add(new MultiplierPill { Label = "Allied Field Boost", Value = "×1.2", Color = "#16a085" });
                }
            }

            // Rules of the Enchanted Land (99016701): +20% Def, SpD
            if (pid == 99016701 || pname.Contains("Rules of the Enchanted Land", StringComparison.OrdinalIgnoreCase))
            {
                if (hasField && (s == "def" || s == "spd"))
                {
                    mult *= 1.20;
                    pills?.Add(new MultiplierPill { Label = "Enchanted Land", Value = "×1.2", Color = "#9b59b6" });
                }
            }

            // Becalming Beauty (99027801): +50% Def, SpD when with status
            if (pid == 99027801 || pname.Contains("Becalming Beauty", StringComparison.OrdinalIgnoreCase))
            {
                if (!string.IsNullOrEmpty(combatant.StatusCondition) && (s == "def" || s == "spd"))
                {
                    mult *= 1.50;
                    pills?.Add(new MultiplierPill { Label = "Becalming Beauty", Value = "×1.5", Color = "#00cec9" });
                }
            }

            // Mind over Matter 4 (23011604): +40% SpA
            if (pid == 23011604 || pname.Contains("Mind over Matter", StringComparison.OrdinalIgnoreCase))
            {
                if (s == "spa")
                {
                    mult *= 1.40;
                    pills?.Add(new MultiplierPill { Label = "Mind over Matter", Value = "×1.4", Color = "#e84393" });
                }
            }

            // Soul-Clad Rage (99044601): +50% to all 5 stats
            if (pid == 99044601 || pname.Contains("Soul-Clad Rage", StringComparison.OrdinalIgnoreCase))
            {
                if (s == "atk" || s == "def" || s == "spa" || s == "spd" || s == "spe")
                {
                    mult *= 1.50;
                    pills?.Add(new MultiplierPill { Label = "Soul-Clad Rage", Value = "×1.5", Color = "#6c5ce7" });
                }
            }

            // While S-Tera: 5 Stats ↑ 1 (23012301): +10% to all 5 stats
            if (pid == 23012301 || pname.Contains("While S-Tera", StringComparison.OrdinalIgnoreCase))
            {
                bool isTera = combatant.FormIndex > 0 && pair.Variations != null && combatant.FormIndex <= pair.Variations.Count &&
                              (pair.Variations[combatant.FormIndex - 1].FormName.Contains("Tera", StringComparison.OrdinalIgnoreCase) ||
                               string.Equals(pair.Variations[combatant.FormIndex - 1].Type, "Stellar", StringComparison.OrdinalIgnoreCase));
                if (isTera && (s == "atk" || s == "def" || s == "spa" || s == "spd" || s == "spe"))
                {
                    mult *= 1.10;
                    pills?.Add(new MultiplierPill { Label = "S-Tera 5 Stats", Value = "×1.1", Color = "#fdcb6e" });
                }
            }
        }

        // Active Grid Cells
        if (activeGridCells != null && pair.Grid != null)
        {
            foreach (var cellId in activeGridCells)
            {
                var cell = pair.Grid.FirstOrDefault(c => c.CellId == cellId);
                if (cell == null) continue;
                long abId = cell.AbilityId;
                string cTitle = cell.Title ?? string.Empty;

                // Sand Screen (2301010100000): +50% SpD in Sandstorm
                if (abId == 2301010100000 || cTitle.Contains("Sand Screen", StringComparison.OrdinalIgnoreCase))
                {
                    if (s == "spd" && hasWeather && field.Weather.Equals("Sandstorm", StringComparison.OrdinalIgnoreCase))
                    {
                        mult *= 1.50;
                        pills?.Add(new MultiplierPill { Label = "Grid: Sand Screen", Value = "×1.5", Color = "#d35400" });
                    }
                }

                // Ice Shell (2301020100000): +50% Def in Hail
                if (abId == 2301020100000 || cTitle.Contains("Ice Shell", StringComparison.OrdinalIgnoreCase))
                {
                    if (s == "def" && hasWeather && field.Weather.Equals("Hail", StringComparison.OrdinalIgnoreCase))
                    {
                        mult *= 1.50;
                        pills?.Add(new MultiplierPill { Label = "Grid: Ice Shell", Value = "×1.5", Color = "#74b9ff" });
                    }
                }

                // Weird Shield (2301030100000): +50% SpD in Psychic Terrain
                if (abId == 2301030100000 || cTitle.Contains("Weird Shield", StringComparison.OrdinalIgnoreCase))
                {
                    if (s == "spd" && hasTerrain && field.Terrain.Equals("Psychic Terrain", StringComparison.OrdinalIgnoreCase))
                    {
                        mult *= 1.50;
                        pills?.Add(new MultiplierPill { Label = "Grid: Weird Shield", Value = "×1.5", Color = "#9b59b6" });
                    }
                }
            }
        }

        return mult;
    }

    public TeamMoveDamageResult CalculateTeamDamage(
        MoveItem move,
        TeamBattleState team,
        DamageRulesDocument rules)
    {
        var attacker = team.ActiveAttacker;
        var activeGrid = team.ActiveAttackerGrid;

        // Set shared sync boosts and calculate master passive allies
        attacker.SyncBoosts = team.AllySyncBuffs;
        if (attacker.Pair != null)
        {
            foreach (var mp in rules.MasterPassives.Where(m => string.Equals(m.SyncPair, attacker.Pair.DisplayName, StringComparison.OrdinalIgnoreCase)))
            {
                attacker.MasterPassiveAllyCount[mp.PassiveName] = team.GetMasterPassiveAllyCount(mp.PassiveName);
            }
        }

        // Apply enemy team sync buffs
        foreach (var enemy in team.Enemies)
        {
            enemy.SyncBoosts = team.EnemySyncBuffs;
        }

        bool isAoE = (team.Field.TargetCount > 1) ||
                     (move.IsSync && (attacker.Pair?.Role?.Contains("Strike", StringComparison.OrdinalIgnoreCase) == true || (attacker.HasExRole && attacker.Pair?.ExRole?.Contains("Strike", StringComparison.OrdinalIgnoreCase) == true))) ||
                     (move.Target?.Contains("all", StringComparison.OrdinalIgnoreCase) == true);

        var leftRes = CalculateDamage(move, attacker, team.Enemies[0], team.Field, rules, activeGrid);
        var centerRes = CalculateDamage(move, attacker, team.Enemies[1], team.Field, rules, activeGrid);
        var rightRes = CalculateDamage(move, attacker, team.Enemies[2], team.Field, rules, activeGrid);

        return new TeamMoveDamageResult
        {
            Move = move,
            IsAoE = isAoE,
            LeftDamage = leftRes,
            CenterDamage = centerRes,
            RightDamage = rightRes,
            ActiveTargetIndex = team.ActiveTargetIndex
        };
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
        
        string effectiveMoveType = move.Type;
        bool isStellarForm = ally.FormIndex > 0 && ally.FormIndex <= pair.Variations.Count &&
            (string.Equals(pair.Variations[ally.FormIndex - 1].Type, "Stellar", StringComparison.OrdinalIgnoreCase) ||
             (pair.Variations[ally.FormIndex - 1].FormName?.Contains("Stellar", StringComparison.OrdinalIgnoreCase) == true));

        if (isStellarForm)
        {
            effectiveMoveType = "Stellar";
            // Terapagos Stellar Form doubles the base power of Tera Starstorm and Kaleidoscopic Tera Starstorm
            if (!move.IsSync && (move.Name.Contains("Tera Starstorm", StringComparison.OrdinalIgnoreCase) || move.Name.Contains("Kaleidoscopic", StringComparison.OrdinalIgnoreCase)))
            {
                rawPower *= 2;
            }
        }

        int fullMoveLevel = ally.SuperAwakeningLevel > 0 ? (5 + ally.SuperAwakeningLevel) : ally.MoveLevel;
        bool isEx = ally.StarLevel.Contains("EX", StringComparison.OrdinalIgnoreCase) || ally.StarLevel.Contains("6★");
        bool isTechBase = pair.Role.StartsWith("Tech", StringComparison.OrdinalIgnoreCase);
        bool isTechExRole = ally.HasExRole && !string.IsNullOrEmpty(pair.ExRole) && pair.ExRole.StartsWith("Tech", StringComparison.OrdinalIgnoreCase);
        bool isTechExSync = move.IsSync && isEx && (isTechBase || isTechExRole);
        double syncIncrement = isTechExSync ? 1.5 : 1.0;

        int power = CalcPower(rawPower, fullMoveLevel, pair.Role, move.IsSync, syncIncrement, move.IsMax);

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

        // Passive skill power ups + Master Skills + PMUN/SMUN/SYUN stacks
        int passivePercentage = (int)Math.Round(EvalPassivePowerUps(move, ally, enemy, field, rules, activeGridCells, pills) * 100);
        int masterPercentage = (int)Math.Round(EvalMasterPassives(move, ally, rules) * 100);
        if (masterPercentage > 0)
        {
            pills.Add(new MultiplierPill { Label = "Master Passive", Value = $"+{masterPercentage}%", Color = "#9b59b6" });
        }

        int boostNextPercentage = 0;
        if (MoveScopeRules.AllowsMoveBoostNext(move))
        {
            if (isPhysical) boostNextPercentage += ally.PhysicalBoostNext * 40;
            if (isSpecial) boostNextPercentage += ally.SpecialBoostNext * 40;
        }
        else if (MoveScopeRules.AllowsSyncBoostNext(move))
        {
            // SYUN stacks provide +10% per stack to sync moves matching PoMaTools engine
            boostNextPercentage += ally.SyncMoveBoostNext * 10;
        }

        int totalPowerupPercent = 100 + passivePercentage + masterPercentage + boostNextPercentage;

        // Innate Move Scaling (move_scaling.json, base 1000)
        int innateModifier1000 = (int)Math.Round(EvalMoveScaling(move, ally, enemy, field, rules, pills) * 1000);

        int battlePower = (int)Math.Floor(Math.Floor((double)baseMovePower * totalPowerupPercent / 100.0) * innateModifier1000 / 1000.0);

        pills.Insert(0, new MultiplierPill { Label = "Move Power", Value = $"{battlePower}", Color = "#2ecc71" });

        // 2. Attacker Stat (Offense) with Form Scale
        string atkStatKey = isPhysical ? "atk" : "spa";
        int jsonAtkStat = pair.Stats.GetStatAtLevel(atkStatKey, int.TryParse(ally.CharLevel, out int cl) ? cl : 180);
        var potBonus = CalcPotentialBonus(pair.Rarity, ally.StarLevel);
        int exAtkBonus = ally.HasExRole ? GetExRoleBonus(pair.ExRole).GetValueOrDefault(atkStatKey, 0) : 0;
        
        int effectiveFormIdx = ally.FormIndex;
        // In PMEX & PoMaTools: The Sync Move triggers Mega Evolution first, so the Sync Move damage
        // is always computed using the Mega Form stats and multiplier!
        if (move.IsSync && effectiveFormIdx == 0 && pair.HasMega && pair.Variations.Count > 0)
        {
            effectiveFormIdx = 1;
        }

        double formStatMult = 1.0;
        if (effectiveFormIdx > 0 && effectiveFormIdx <= pair.Variations.Count)
        {
            var variation = pair.Variations[effectiveFormIdx - 1];
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

        bool hasBurnUseless = move.Name.Equals("Facade", StringComparison.OrdinalIgnoreCase) ||
                              move.Id == 263 ||
                              (pair.Passives != null && pair.Passives.Any(p => p.Id == 99015901 || p.Name.Contains("Fiery Dance") || p.Name.Contains("Danza Ardiente")));

        double inBattleAtkMult = GetInBattleStatMultiplier(atkStatKey, ally, field, activeGridCells, pills);

        int attackerStat = CalcTotalStat(
            atkStatKey,
            jsonAtkStat,
            ally.Stages.GetValueOrDefault(atkStatKey, 0),
            potential: potBonus.GetValueOrDefault(atkStatKey, 0),
            exBonus: exAtkBonus,
            formMult: formStatMult,
            inBattleStatMult: inBattleAtkMult,
            hasSa: pair.HasSuperAwakening,
            saLevel: ally.SuperAwakeningLevel,
            role: pair.Role,
            gear: ally.Gear.GetValueOrDefault(atkStatKey, 0),
            gridStat: gridAtkStat,
            isBurned: ally.StatusCondition == "burned",
            ignoreBurnPenalty: hasBurnUseless,
            critOffense: ally.IsCriticalMove
        );

        pills.Add(new MultiplierPill { Label = isPhysical ? "Atk Stat" : "Sp. Atk Stat", Value = $"{attackerStat}", Color = "#3498db" });

        // 3. Defender Stat (Defense)
        string defStatKey = isPhysical ? "def" : "spd";
        int jsonDefStat = enemy.ManualStats.GetValueOrDefault(defStatKey, 95);
        double inBattleDefMult = GetInBattleStatMultiplier(defStatKey, enemy, field);
        int defenderStat = CalcTotalStat(
            defStatKey,
            jsonDefStat,
            enemy.Stages.GetValueOrDefault(defStatKey, 0),
            mitigation: enemy.Mitigations.GetValueOrDefault(defStatKey, 0),
            inBattleStatMult: inBattleDefMult,
            critDefense: ally.IsCriticalMove
        );

        // 4. Exact Fractional Multipliers Product (Numerator `ne` & Denominator `he`)
        double ne = 1.0;
        double he = 1.0;

        // Special Multiplier: Ash's Passion (99011401) on Thunder x1.30
        if (pair.Passives != null && pair.Passives.Any(p => p.Id == 99011401 || p.Name.Contains("Ash’s Passion") || p.Name.Contains("Ash's Passion")))
        {
            if (move.Name.Equals("Thunder", StringComparison.OrdinalIgnoreCase) || move.Name.Equals("打雷", StringComparison.OrdinalIgnoreCase))
            {
                ne *= 13.0;
                he *= 10.0;
                pills.Add(new MultiplierPill { Label = "Ash’s Passion", Value = "×1.3", Color = "#f1c40f" });
            }
        }

        // Weather, Terrain, Zone
        bool isFire = string.Equals(effectiveMoveType, "Fire", StringComparison.OrdinalIgnoreCase);
        bool isWater = string.Equals(effectiveMoveType, "Water", StringComparison.OrdinalIgnoreCase);
        bool isElectric = string.Equals(effectiveMoveType, "Electric", StringComparison.OrdinalIgnoreCase);
        bool isGrass = string.Equals(effectiveMoveType, "Grass", StringComparison.OrdinalIgnoreCase);
        bool isPsychic = string.Equals(effectiveMoveType, "Psychic", StringComparison.OrdinalIgnoreCase);

        bool weatherBoost = (field.Weather.Equals("Sunny", StringComparison.OrdinalIgnoreCase) && isFire) ||
                            (field.Weather.Equals("Rainy", StringComparison.OrdinalIgnoreCase) && isWater);
        if (weatherBoost)
        {
            ne *= 3.0;
            he *= field.WeatherEx ? 1.0 : 2.0;
            pills.Add(new MultiplierPill { Label = field.Weather, Value = field.WeatherEx ? "×3.0" : "×1.5", Color = "#d35400" });
        }

        bool terrainBoost = (field.Terrain.Equals("Electric Terrain", StringComparison.OrdinalIgnoreCase) && isElectric) ||
                            (field.Terrain.Equals("Grassy Terrain", StringComparison.OrdinalIgnoreCase) && isGrass) ||
                            (field.Terrain.Equals("Psychic Terrain", StringComparison.OrdinalIgnoreCase) && isPsychic);
        if (terrainBoost)
        {
            ne *= 3.0;
            he *= field.TerrainEx ? 1.0 : 2.0;
            pills.Add(new MultiplierPill { Label = field.Terrain, Value = field.TerrainEx ? "×3.0" : "×1.5", Color = "#27ae60" });
        }

        bool zoneBoost = !string.IsNullOrEmpty(field.Zone) && field.Zone.StartsWith(effectiveMoveType, StringComparison.OrdinalIgnoreCase);
        if (zoneBoost)
        {
            ne *= 3.0;
            he *= field.ZoneEx ? 1.0 : 2.0;
            pills.Add(new MultiplierPill { Label = field.Zone, Value = field.ZoneEx ? "×3.0" : "×1.5", Color = "#8e44ad" });
        }

        // Tera Boost (does not apply to Sync Moves)
        bool isTeraForm = ally.FormIndex > 0 && ally.FormIndex <= pair.Variations.Count &&
            (pair.Variations[ally.FormIndex - 1].FormName?.Contains("Tera", StringComparison.OrdinalIgnoreCase) == true ||
             pair.Variations[ally.FormIndex - 1].FormName?.Contains("Stellar", StringComparison.OrdinalIgnoreCase) == true ||
             pair.Variations[ally.FormIndex - 1].TerastalMoveId > 0);

        if (isTeraForm && MoveScopeRules.AllowsTeraBoost(move))
        {
            if (isStellarForm)
            {
                ne *= 2.0;
                pills.Add(new MultiplierPill { Label = "Stellar Boost", Value = "×2.0", Color = "#9b59b6" });
            }
            else if (string.Equals(effectiveMoveType, pair.Type, StringComparison.OrdinalIgnoreCase) || 
                     string.Equals(effectiveMoveType, pair.Variations[ally.FormIndex - 1].Type, StringComparison.OrdinalIgnoreCase))
            {
                ne *= 3.0;
                he *= 2.0;
                pills.Add(new MultiplierPill { Label = "Tera Boost", Value = "×1.5", Color = "#3498db" });
            }
        }

        // Type Effectiveness
        bool isSuperEffective = (!string.IsNullOrEmpty(enemy.Weakness) &&
            string.Equals(effectiveMoveType, enemy.Weakness, StringComparison.OrdinalIgnoreCase)) ||
            (isStellarForm && !string.IsNullOrEmpty(enemy.Weakness));

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
        int effectiveSyncBoosts = ally.SyncBoosts;
        // In PMEX / PoMaTools: To be in a Mega or Sync-Tera form, the pair already synced once to transform.
        // Therefore, all moves in that form automatically gain the Sync Buff(s) granted by that sync (+2 if Support EX, +1 otherwise)!
        // Forms that trigger automatically on entry (e.g. Terapagos Terastal Form) or via trainer moves/stances do NOT gain automatic sync buffs.
        if (IsSyncTransformationForm(pair, ally.FormIndex))
        {
            effectiveSyncBoosts += GetSyncBuffsGrantedBySync(ally);
        }

        if (effectiveSyncBoosts > 0)
        {
            ne *= (2 + effectiveSyncBoosts);
            he *= 2.0;
            pills.Add(new MultiplierPill { Label = "Sync Buffs", Value = $"×{1.0 + effectiveSyncBoosts * 0.5:0.#}", Color = "#e67e22" });
        }

        // Target count (AoE scaling: only applies to moves that hit all opponents, exempting Sync Moves and Max Moves)
        bool isAoEMove = !move.IsMax && move.Target != null && (
            move.Target.Contains("all", StringComparison.OrdinalIgnoreCase) ||
            move.Target.Contains("opponents", StringComparison.OrdinalIgnoreCase) ||
            move.Target.Contains("entire", StringComparison.OrdinalIgnoreCase)
        );

        // Check if passive grants Extend Range / No AoE power reduction (e.g. Extend Range, Expand Reach, Arc Suit passives, etc.)
        bool hasAoENoDecayPassive = false;
        if (pair != null)
        {
            var passives = pair.Passives ?? new List<PassiveItem>();
            if (ally.FormIndex > 0 && pair.Variations != null && ally.FormIndex <= pair.Variations.Count && pair.Variations[ally.FormIndex - 1].Passives != null)
            {
                passives = pair.Variations[ally.FormIndex - 1].Passives;
            }

            foreach (var ps in passives)
            {
                string pDesc = ps.Description ?? string.Empty;
                string pName = ps.Name ?? string.Empty;
                if (pDesc.Contains("not lowered even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                    pDesc.Contains("not reduced even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                    pDesc.Contains("target all opponents is not reduced", StringComparison.OrdinalIgnoreCase) ||
                    pDesc.Contains("target all opponents is not lowered", StringComparison.OrdinalIgnoreCase) ||
                    pDesc.Contains("moves affected by this passive skill are not lowered", StringComparison.OrdinalIgnoreCase) ||
                    pDesc.Contains("moves affected by this passive skill are not reduced", StringComparison.OrdinalIgnoreCase) ||
                    pName.Contains("Extend Range", StringComparison.OrdinalIgnoreCase) ||
                    pName.Contains("Expand Reach", StringComparison.OrdinalIgnoreCase))
                {
                    hasAoENoDecayPassive = true;
                    break;
                }
            }

            // Also check Super Awakening Passive
            if (!hasAoENoDecayPassive && ally.SuperAwakeningLevel >= 5 && pair.SuperAwakeningPassive != null)
            {
                string saDesc = pair.SuperAwakeningPassive.Description ?? string.Empty;
                if (saDesc.Contains("not lowered even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                    saDesc.Contains("not reduced even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                    saDesc.Contains("target all opponents is not reduced", StringComparison.OrdinalIgnoreCase) ||
                    saDesc.Contains("target all opponents is not lowered", StringComparison.OrdinalIgnoreCase))
                {
                    hasAoENoDecayPassive = true;
                }
            }

            // Also check active grid cells
            if (!hasAoENoDecayPassive && pair.Grid != null)
            {
                foreach (var cellId in activeGridCells)
                {
                    var cell = pair.Grid.FirstOrDefault(c => c.CellId == cellId);
                    if (cell != null)
                    {
                        string cDesc = cell.Description ?? string.Empty;
                        if (cDesc.Contains("not lowered even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            cDesc.Contains("not reduced even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            cDesc.Contains("target all opponents is not reduced", StringComparison.OrdinalIgnoreCase) ||
                            cDesc.Contains("target all opponents is not lowered", StringComparison.OrdinalIgnoreCase))
                        {
                            hasAoENoDecayPassive = true;
                            break;
                        }
                    }
                }
            }
        }

        // Check if the move itself has no decay in its description or name
        string mDesc = move.Description ?? string.Empty;
        bool isMoveNoDecay = mDesc.Contains("not lowered even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("not reduced even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("not lowered when there are multiple opponents", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("not reduced when there are multiple opponents", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("is not lowered even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("is not reduced even if there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("is not lowered when there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("is not reduced when there are multiple targets", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("damage is not reduced", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("damage is not lowered", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("power of this attack is not reduced", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("power of this attack is not lowered", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("power of this move is not reduced", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("power of this move is not lowered", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("power is not reduced", StringComparison.OrdinalIgnoreCase) ||
                            mDesc.Contains("power is not lowered", StringComparison.OrdinalIgnoreCase);

        // AoE penalty only applies to multi-target moves (and NOT to sync moves, and NOT to max moves, and NOT if protected by move or passive)
        if (field.TargetCount > 1 && isAoEMove && MoveScopeRules.AllowsAoEPenalty(move) && !isMoveNoDecay && !hasAoENoDecayPassive)
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
        int rebuff = enemy.EnemyTypeRebuffs.GetValueOrDefault(effectiveMoveType, 0);
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

        // Circles (apply to regular moves and sync moves, NOT Max moves matching PoMaTools: "MV"===z.kind||"SN"==z.kind)
        if (MoveScopeRules.AllowsCircles(move))
        {
            foreach (var region in CombatantState.CircleRegions)
            {
                int allies = Math.Clamp(ally.CircleAllyCount.GetValueOrDefault(region, 1), 1, 3);
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
                        pills.Add(new MultiplierPill { Label = $"{region} Circle (Def)", Value = $"×{(105.0 + 5.0 * allies) / 100.0:0.##}", Color = "#00cec9" });
                    }
                }
            }

            // Enemy Defensive Circles (reduces incoming attack & sync damage to enemy)
            foreach (var region in CombatantState.CircleRegions)
            {
                int enemyAllies = Math.Clamp(enemy.CircleAllyCount.GetValueOrDefault(region, 1), 1, 3);
                var enemyActive = enemy.CircleActive.GetValueOrDefault(region);
                if (enemyActive != null && enemyActive.GetValueOrDefault("defensive"))
                {
                    ne *= 100.0 - (10.0 + 3.0 * enemyAllies);
                    he *= 100.0;
                    pills.Add(new MultiplierPill { Label = $"{region} Circle (Enemy Def)", Value = $"×{(100.0 - (10.0 + 3.0 * enemyAllies)) / 100.0:0.##}", Color = "#6c5ce7" });
                }
            }
        }

        // Breaks on Target (only apply to regular moves, NOT Sync Moves and NOT Max Moves matching PoMaTools: "MV"===z.kind: x1.5 damage)
        if (MoveScopeRules.AllowsBreaks(move))
        {
            if (isPhysical && enemy.PhysicalBreak) { ne *= 3.0; he *= 2.0; pills.Add(new MultiplierPill { Label = "Phys Break", Value = "×1.5", Color = "#e84393" }); }
            if (isSpecial && enemy.SpecialBreak) { ne *= 3.0; he *= 2.0; pills.Add(new MultiplierPill { Label = "Spec Break", Value = "×1.5", Color = "#e84393" }); }
        }

        // Damage Reductions on Target (Reflect / Light Screen on opponent reduces damage taken: x0.66 damage)
        // Only apply to regular moves (NOT Sync Moves and NOT Max Moves)
        // Critical hits ignore damage reduction screens on the target
        if (!ally.IsCriticalMove && MoveScopeRules.AllowsScreens(move))
        {
            if (isPhysical && enemy.PhysicalDamageReduction)
            {
                ne *= 2.0;
                he *= 3.0;
                pills.Add(new MultiplierPill { Label = "Phys Dmg Red", Value = "×0.66", Color = "#e67e22" });
            }
            if (isSpecial && enemy.SpecialDamageReduction)
            {
                ne *= 2.0;
                he *= 3.0;
                pills.Add(new MultiplierPill { Label = "Spec Dmg Red", Value = "×0.66", Color = "#e67e22" });
            }
        }

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
            Breakdown = pills,
            TargetMaxHp = enemy.ManualStats.GetValueOrDefault("hp", 0)
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
            // Super Awakening Passive (Unlocked at SA 5)
            if (ally.SuperAwakeningLevel >= 5 && ally.Pair.SuperAwakeningPassive != null && !string.IsNullOrEmpty(ally.Pair.SuperAwakeningPassive.Name))
            {
                var saRule = rules.DamagePassives.FirstOrDefault(dp => string.Equals(dp.Name, ally.Pair.SuperAwakeningPassive.Name, StringComparison.OrdinalIgnoreCase));
                if (saRule != null)
                {
                    double v = EvalSingleDamagePassive(saRule, move, ally, enemy, field);
                    if (v > 0)
                    {
                        total += v;
                        pills.Add(new MultiplierPill { Label = $"SA: {saRule.Name}", Value = $"+{v * 100:0.#}%", Color = "#e74c3c" });
                    }
                }
            }
            int effectiveFormForPassives = ally.FormIndex;
            if (move.IsSync && effectiveFormForPassives == 0 && ally.Pair.HasMega && ally.Pair.Variations.Count > 0)
            {
                effectiveFormForPassives = 1;
            }

            var passivesList = (effectiveFormForPassives > 0 && effectiveFormForPassives <= ally.Pair.Variations.Count && ally.Pair.Variations[effectiveFormForPassives - 1].Passives.Count > 0)
                ? ally.Pair.Variations[effectiveFormForPassives - 1].Passives
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
        if (dp.SubPassives != null && dp.SubPassives.Count > 0)
        {
            double subTotal = 0;
            foreach (var sp in dp.SubPassives)
            {
                subTotal += EvalSingleDamagePassive(sp, move, ally, enemy, field);
            }
            return subTotal;
        }

        if (!MoveScopeRules.AllowsPassive(dp.AppliesTo, move)) return 0;

        if (!string.IsNullOrEmpty(dp.MoveName) && !MatchesMoveName(move.Name, dp.MoveName, move.IsSync))
        {
            return 0;
        }

        // SpecialMulti passives like Ash's Passion are applied multiplicatively in CalculateDamage
        if (dp.Name.Contains("Ash’s Passion") || dp.Name.Contains("Ash's Passion"))
        {
            return 0;
        }

        return dp.Mechanism switch
        {
            "user_stat_raised" => CalcStatScaling(dp.Stat, ally.Stages, true, move.IsSync),
            "target_stat_lowered" => CalcStatScaling(dp.Stat, enemy.Stages, false, move.IsSync),
            "stat_is_raised" => (ally.Stages.GetValueOrDefault(dp.Stat, 0) > 0 ? dp.Value * 0.1 : 0),
            "stat_is_lowered" => (enemy.Stages.GetValueOrDefault(dp.Stat, 0) < 0 ? dp.Value * 0.1 : 0),
            "hp_scaling" => CalcHpScaling(
                dp.StatTarget == "target" ? enemy.HpPercent : ally.HpPercent,
                dp.Value,
                isTarget: dp.StatTarget == "target",
                isLessHp: dp.Conditions.Count == 0 || dp.Conditions.Any(g => g.Any(c => c.Contains("low") || c.Contains("less") || c.Contains("reduced")))
            ),
            "flat_boost" => (EvalConditions(dp.Conditions, field, ally, enemy, move) ? dp.Value * 0.1 : 0),
            _ => 0
        };
    }

    public static double CalcHpScaling(int hpPercent, int passiveValue, bool isTarget, bool isLessHp = true)
    {
        // PoMaTools 4-tier HP scaling:
        // HP = 100% -> 0, 51-99% -> 1, 34-50% -> 2, <= 33% -> 3
        int tier = hpPercent >= 100 ? 0 : (hpPercent >= 51 ? 1 : (hpPercent >= 34 ? 2 : 3));
        double[] thresholds = isLessHp ? [0.0, 0.25, 0.50, 1.00] : [1.00, 0.50, 0.25, 0.0];
        double factor = isTarget ? 0.10 : 0.05;
        double rawBonus = (passiveValue * 10.0) * factor * thresholds[tier];
        return Math.Ceiling(rawBonus * 100.0) / 100.0 / 100.0;
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
            if (isSync)
            {
                // PoMaTools: Math.round(Math.min(count, 18) * 667 / 100) -> 0% to 120%
                int pct = (int)Math.Round(Math.Min(count, 18) * 667.0 / 100.0);
                return pct / 100.0;
            }
            else
            {
                // PoMaTools: Math.min(Math.floor(count * 26 / 10), 110) -> 0% to 110%
                int pct = Math.Min((int)Math.Floor(count * 26.0 / 10.0), 110);
                return pct / 100.0;
            }
        }
        else
        {
            int s = stages.GetValueOrDefault(statKey, 0);
            int count = isRaised ? Math.Clamp(s, 0, 6) : Math.Clamp(-s, 0, 6);
            if (isSync)
            {
                // PoMaTools: Math.round(Math.max(stages, 0) * 167 / 10) -> gives 17, 33, 50, 67, 84, 100%
                int pct = (int)Math.Round(count * 167.0 / 10.0);
                return pct / 100.0;
            }
            else
            {
                // PoMaTools: count * 5 -> gives 5, 10, 15, 20, 25, 30%
                int pct = count * 5;
                return pct / 100.0;
            }
        }
    }

    private bool EvalConditions(List<List<string>> conditionGroups, FieldState field, CombatantState ally, CombatantState enemy, MoveItem move)
    {
        if (conditionGroups.Count == 0) return true;
        foreach (var andGroup in conditionGroups)
        {
            bool allMatch = true;
            foreach (var c in andGroup)
            {
                string cond = c.ToLowerInvariant().Trim();
                bool match = cond switch
                {
                    "sunny" => field.Weather == "Sunny",
                    "rain" or "rainy" => field.Weather == "Rainy",
                    "sandstorm" => field.Weather == "Sandstorm",
                    "hail" => field.Weather == "Hail",
                    "no_weather" => string.IsNullOrEmpty(field.Weather),
                    "any_weather" => !string.IsNullOrEmpty(field.Weather),
                    "electric_terrain" => field.Terrain == "Electric Terrain",
                    "grassy_terrain" => field.Terrain == "Grassy Terrain",
                    "psychic_terrain" => field.Terrain == "Psychic Terrain",
                    "any_terrain" => !string.IsNullOrEmpty(field.Terrain),
                    "fairy_zone" => field.Zone == "Fairy Zone",
                    "dragon_zone" => field.Zone == "Dragon Zone",
                    "dark_zone" => field.Zone == "Dark Zone",
                    "ghost_zone" => field.Zone == "Ghost Zone",
                    "flying_zone" => field.Zone == "Flying Zone",
                    "grass_zone" => field.Zone == "Grass Zone",
                    "fire_zone" => field.Zone == "Fire Zone",
                    "ground_zone" => field.Zone == "Ground Zone",
                    "rock_zone" => field.Zone == "Rock Zone",
                    "steel_zone" => field.Zone == "Steel Zone",
                    "electric_zone" => field.Zone == "Electric Zone",
                    "poison_zone" => field.Zone == "Poison Zone",
                    "normal_zone" => field.Zone == "Normal Zone",
                    "any_weather_terrain_zone" => !string.IsNullOrEmpty(field.Weather) || !string.IsNullOrEmpty(field.Terrain) || !string.IsNullOrEmpty(field.Zone),
                    "burned" => enemy.StatusCondition == "burned",
                    "paralyzed" => enemy.StatusCondition == "paralyzed",
                    "poisoned" => enemy.StatusCondition == "poisoned" || enemy.StatusCondition == "badly poisoned",
                    "frozen" => enemy.StatusCondition == "frozen",
                    "asleep" => enemy.StatusCondition == "asleep",
                    "any_status" or "any_condition" => !string.IsNullOrEmpty(enemy.StatusCondition),
                    "confused" => enemy.VolatileStatus.GetValueOrDefault("confused", false),
                    "trapped" => enemy.VolatileStatus.GetValueOrDefault("trapped", false),
                    "flinching" => enemy.VolatileStatus.GetValueOrDefault("flinching", false),
                    "flinch_confuse_trap" => enemy.VolatileStatus.GetValueOrDefault("confused", false) || enemy.VolatileStatus.GetValueOrDefault("trapped", false) || enemy.VolatileStatus.GetValueOrDefault("flinching", false),
                    "critical" => ally.IsCriticalMove,
                    "super_effective" or "super_efective" => (!string.IsNullOrEmpty(enemy.Weakness) && string.Equals(move.Type, enemy.Weakness, StringComparison.OrdinalIgnoreCase)),
                    "has_rebuff" or "rebuff_lowered" or "target_rebuff" => enemy.EnemyTypeRebuffs.GetValueOrDefault(move.Type, 0) < 0 || enemy.EnemyTypeRebuffs.Values.Any(v => v < 0),
                    "user_rebuff" or "user_rebuff_raised" => ally.UserTypeRebuffs.Values.Any(v => v > 0),
                    "user_rebuff_lowered" => ally.UserTypeRebuffs.Values.Any(v => v < 0),
                    "hp_full" => ally.HpPercent >= 100,
                    "hp_low" => ally.HpPercent <= 33 || ally.HpPercent <= 20,
                    "hp_reduced" => ally.HpPercent < 100,
                    "hp_half_more" or "hp_above_half" => ally.HpPercent >= 50,
                    "hp_half_less" => ally.HpPercent <= 50,
                    "target_hp_low" => enemy.HpPercent <= 33 || enemy.HpPercent <= 20,
                    "target_hp_half_less" => enemy.HpPercent <= 50,
                    "damage_field" or "any_damage_field" => !string.IsNullOrEmpty(enemy.DamageField) || !string.IsNullOrEmpty(ally.DamageField),
                    "target_damage_field" => !string.IsNullOrEmpty(enemy.DamageField),
                    "user_damage_field" => !string.IsNullOrEmpty(ally.DamageField),
                    "circle_active" or "battle_circle" or "battle_circle_active" or "any_circle" => ally.CircleActive.Values.Any(d => d.Values.Any(v => v)),
                    "physical_circle" => ally.CircleActive.Values.Any(d => d.GetValueOrDefault("physical")),
                    "special_circle" => ally.CircleActive.Values.Any(d => d.GetValueOrDefault("special")),
                    "physical_damage_reduction" or "phys_dmg_red" or "physical_reduction" => ally.PhysicalDamageReduction || enemy.PhysicalDamageReduction,
                    "special_damage_reduction" or "spec_dmg_red" or "special_reduction" => ally.SpecialDamageReduction || enemy.SpecialDamageReduction,
                    "damage_reduction" or "any_damage_reduction" => ally.PhysicalDamageReduction || ally.SpecialDamageReduction || enemy.PhysicalDamageReduction || enemy.SpecialDamageReduction,
                    "physical_break" or "phys_break" => enemy.PhysicalBreak || ally.PhysicalBreak,
                    "special_break" or "spec_break" => enemy.SpecialBreak || ally.SpecialBreak,
                    "has_break" or "any_break" => enemy.PhysicalBreak || enemy.SpecialBreak || ally.PhysicalBreak || ally.SpecialBreak,
                    "only_one_alive" or "berry" or "first_sync" => true,
                    "all_stats_not_high" => ally.Stages.Values.All(v => v <= 0),
                    "any_stat_in_low" => ally.Stages.Values.Any(v => v < 0),
                    "target_all_stats_not_high" => enemy.Stages.Values.All(v => v <= 0),
                    "target_any_stat_in_low" => enemy.Stages.Values.Any(v => v < 0),
                    _ => (cond.Contains("zone") && !string.IsNullOrEmpty(field.Zone) && field.Zone.ToLowerInvariant().Contains(cond.Replace("_zone", ""))) ||
                         (cond.Contains("damage_field") && ((!string.IsNullOrEmpty(ally.DamageField) && ally.DamageField.ToLowerInvariant().Contains(cond.Replace("_damage_field", ""))) || (!string.IsNullOrEmpty(enemy.DamageField) && enemy.DamageField.ToLowerInvariant().Contains(cond.Replace("_damage_field", ""))))) ||
                         (cond.Contains("circle") && ally.CircleActive.Any(kv => kv.Key.ToLowerInvariant().Contains(cond.Replace("_circle", "")) && kv.Value.Values.Any(v => v)))
                };
                if (!match) { allMatch = false; break; }
            }
            if (allMatch) return true;
        }
        return false;
    }

    private static string NormalizeMoveName(string? name)
    {
        if (string.IsNullOrWhiteSpace(name)) return "";
        return string.Join(" ", name.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries));
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

        string normMoveName = NormalizeMoveName(move.Name);
        string pairName = ally.Pair.DisplayName;

        var rule = rules.MoveScaling.FirstOrDefault(ms =>
            (ms.SyncPair == "*" ||
             string.Equals(ms.SyncPair, pairName, StringComparison.OrdinalIgnoreCase) ||
             ms.SyncPair.StartsWith(pairName, StringComparison.OrdinalIgnoreCase) ||
             pairName.StartsWith(ms.SyncPair, StringComparison.OrdinalIgnoreCase) ||
             (pairName.Contains(" & ") && ms.SyncPair.StartsWith(pairName.Substring(0, pairName.IndexOf(" & ") + 3), StringComparison.OrdinalIgnoreCase))) &&
            string.Equals(NormalizeMoveName(ms.MoveName), normMoveName, StringComparison.OrdinalIgnoreCase));

        if (rule == null)
        {
            if (!string.IsNullOrEmpty(move.Description))
            {
                double descMult = 1.0;
                string desc = NormalizeMoveName(move.Description);

                // 1. Dual Screens / Damage Reductions in move descriptions (e.g. Urbain & Meganium Four-Fleur Solar Beam)
                bool hasDualScreenText = desc.Contains("Physical Damage Reduction effect", StringComparison.OrdinalIgnoreCase) &&
                                         desc.Contains("Special Damage Reduction effect", StringComparison.OrdinalIgnoreCase) &&
                                         desc.Contains("allied field", StringComparison.OrdinalIgnoreCase);

                if (hasDualScreenText)
                {
                    if (ally.PhysicalDamageReduction && ally.SpecialDamageReduction)
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Dual Screens)", Value = "×2.0", Color = "#fd79a8" });
                    }
                    else if (ally.PhysicalDamageReduction || ally.SpecialDamageReduction)
                    {
                        descMult *= 1.5;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Screen)", Value = "×1.5", Color = "#fd79a8" });
                    }
                }
                else if (desc.Contains("Physical Damage Reduction effect applies to the allied field", StringComparison.OrdinalIgnoreCase) && desc.Contains("increases 50%", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.PhysicalDamageReduction)
                    {
                        descMult *= 1.5;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Phys Red)", Value = "×1.5", Color = "#fd79a8" });
                    }
                }
                else if (desc.Contains("Special Damage Reduction effect applies to the allied field", StringComparison.OrdinalIgnoreCase) && desc.Contains("increases 50%", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.SpecialDamageReduction)
                    {
                        descMult *= 1.5;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Spec Red)", Value = "×1.5", Color = "#fd79a8" });
                    }
                }

                // 2. Team does NOT have a sync buff (e.g. Red Anniversary Charizard B Dragon Claw)
                if (desc.Contains("team does not have a sync buff", StringComparison.OrdinalIgnoreCase) && (desc.Contains("doubled", StringComparison.OrdinalIgnoreCase) || desc.Contains("power is doubled", StringComparison.OrdinalIgnoreCase)))
                {
                    if (ally.SyncBoosts == 0)
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (No Sync Buff)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 3. Target HP <= 50% (e.g. Brine)
                if ((desc.Contains("remaining HP is at half or below", StringComparison.OrdinalIgnoreCase) || desc.Contains("HP is half or less", StringComparison.OrdinalIgnoreCase)) && (desc.Contains("doubled", StringComparison.OrdinalIgnoreCase) || desc.Contains("power is doubled", StringComparison.OrdinalIgnoreCase)))
                {
                    if (enemy.HpPercent <= 50)
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Target HP ≤50%)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 4. User HP pinch / low (e.g. Flail, Reversal, in a pinch)
                if (desc.Contains("percentage of remaining HP", StringComparison.OrdinalIgnoreCase) || desc.Contains("less HP the user has", StringComparison.OrdinalIgnoreCase) || desc.Contains("more damage the user has taken", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.HpPercent < 100)
                    {
                        double hpScale = 1.0 + (100 - ally.HpPercent) / 100.0;
                        descMult *= hpScale;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Low HP)", Value = $"×{hpScale:0.##}", Color = "#fd79a8" });
                    }
                }
                else if (desc.Contains("in a pinch", StringComparison.OrdinalIgnoreCase) && desc.Contains("increases 20%", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.HpPercent <= 33)
                    {
                        descMult *= 1.2;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Pinch)", Value = "×1.2", Color = "#fd79a8" });
                    }
                }

                // 5. Super Effective 30% increase in description
                if (desc.Contains("30% when it is super effective", StringComparison.OrdinalIgnoreCase))
                {
                    if (!string.IsNullOrEmpty(enemy.Weakness) && string.Equals(move.Type, enemy.Weakness, StringComparison.OrdinalIgnoreCase))
                    {
                        descMult *= 1.3;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (SE 30%)", Value = "×1.3", Color = "#fd79a8" });
                    }
                }

                // 6. Target Speed is raised (doubles)
                if (desc.Contains("target’s Speed is raised", StringComparison.OrdinalIgnoreCase) || desc.Contains("target's Speed is raised", StringComparison.OrdinalIgnoreCase))
                {
                    if (enemy.Stages.GetValueOrDefault("spe", 0) > 0 && (desc.Contains("doubled", StringComparison.OrdinalIgnoreCase) || desc.Contains("power is doubled", StringComparison.OrdinalIgnoreCase)))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Target Spe+)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 7. Mega Evolved increases move power (e.g. Arc Suit Blue Sacred Hurricane, Harmony Rushing Rapids Aqua Jet)
                string normDescQuotes = desc.Replace("’", "'");
                bool megaDoublesPower = normDescQuotes.Contains("Mega Evolved, also doubles", StringComparison.OrdinalIgnoreCase);
                bool megaBoosts50 = normDescQuotes.Contains("Mega Evolved, also increases this attack's power by 50%", StringComparison.OrdinalIgnoreCase);

                if (ally.FormIndex > 0)
                {
                    if (megaDoublesPower)
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Mega)", Value = "×2.0", Color = "#fd79a8" });
                    }
                    else if (megaBoosts50)
                    {
                        descMult *= 1.5;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Mega +50%)", Value = "×1.5", Color = "#fd79a8" });
                    }
                }

                // 8. User poisoned/paralyzed/burned (e.g. Facade)
                if (desc.Contains("user is poisoned, badly poisoned, paralyzed, or burned", StringComparison.OrdinalIgnoreCase) || desc.Contains("user is affected by a status condition", StringComparison.OrdinalIgnoreCase))
                {
                    if (!string.IsNullOrEmpty(ally.StatusCondition))
                    {
                        double m = move.IsSync ? 2.0 : (desc.Contains("doubled", StringComparison.OrdinalIgnoreCase) ? 2.0 : 1.5);
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (User Status)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                }

                // 9. Target Status / Interferences (Hex, Venoshock, B moves, etc.)
                if (desc.Contains("affected by a status condition, flinching, confused, or trapped", StringComparison.OrdinalIgnoreCase))
                {
                    if (!string.IsNullOrEmpty(enemy.StatusCondition) || enemy.VolatileStatus.Values.Any(v => v))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Status/Hindrance)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }
                else if (desc.Contains("target is affected by a status condition", StringComparison.OrdinalIgnoreCase) || desc.Contains("target has a status condition", StringComparison.OrdinalIgnoreCase))
                {
                    if (!string.IsNullOrEmpty(enemy.StatusCondition))
                    {
                        double m = move.IsSync ? 2.0 : (desc.Contains("50%", StringComparison.OrdinalIgnoreCase) ? 1.5 : (desc.Contains("20%", StringComparison.OrdinalIgnoreCase) ? 1.2 : 2.0));
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Status)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                }
                else
                {
                    if (desc.Contains("target is paralyzed", StringComparison.OrdinalIgnoreCase) && enemy.StatusCondition == "paralyzed")
                    {
                        double m = move.IsSync ? 2.0 : (desc.Contains("50%", StringComparison.OrdinalIgnoreCase) ? 1.5 : 2.0);
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Paralyzed)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                    if (desc.Contains("target is burned", StringComparison.OrdinalIgnoreCase) && enemy.StatusCondition == "burned")
                    {
                        double m = move.IsSync ? 2.0 : (desc.Contains("50%", StringComparison.OrdinalIgnoreCase) ? 1.5 : 2.0);
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Burned)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                    if ((desc.Contains("target is poisoned", StringComparison.OrdinalIgnoreCase) || desc.Contains("poisoned or badly poisoned", StringComparison.OrdinalIgnoreCase)) && (enemy.StatusCondition == "poisoned" || enemy.StatusCondition == "badly poisoned"))
                    {
                        double m = move.IsSync ? 2.0 : (desc.Contains("doubled", StringComparison.OrdinalIgnoreCase) ? 2.0 : (desc.Contains("50%", StringComparison.OrdinalIgnoreCase) ? 1.5 : 2.0));
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Poisoned)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                    if (desc.Contains("target is asleep", StringComparison.OrdinalIgnoreCase) && enemy.StatusCondition == "asleep")
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Asleep)", Value = "×2.0", Color = "#fd79a8" });
                    }
                    if (desc.Contains("target is frozen", StringComparison.OrdinalIgnoreCase) && enemy.StatusCondition == "frozen")
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Frozen)", Value = "×2.0", Color = "#fd79a8" });
                    }
                    if (desc.Contains("target is confused", StringComparison.OrdinalIgnoreCase) && enemy.VolatileStatus.GetValueOrDefault("confused", false))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Confused)", Value = "×2.0", Color = "#fd79a8" });
                    }
                    if (desc.Contains("target is trapped", StringComparison.OrdinalIgnoreCase) && enemy.VolatileStatus.GetValueOrDefault("trapped", false))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Trapped)", Value = "×2.0", Color = "#fd79a8" });
                    }
                    if (desc.Contains("target is flinching", StringComparison.OrdinalIgnoreCase) && enemy.VolatileStatus.GetValueOrDefault("flinching", false))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Flinching)", Value = "×2.0", Color = "#fd79a8" });
                    }
                    if (desc.Contains("target is restrained", StringComparison.OrdinalIgnoreCase) && enemy.VolatileStatus.GetValueOrDefault("restrained", false))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Restrained)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 10. Weather / Terrain / Zone in Move descriptions
                // Specific Zone checking
                string[] zoneTypes = ["Ghost", "Dark", "Fairy", "Rock", "Dragon", "Steel", "Poison", "Flying", "Bug", "Fighting", "Electric", "Grass", "Water", "Fire", "Ice", "Ground", "Psychic", "Normal"];
                bool matchedSpecificZone = false;
                foreach (var zt in zoneTypes)
                {
                    if (desc.Contains($"zone is a {zt} Zone", StringComparison.OrdinalIgnoreCase) || desc.Contains($"zone is an {zt} Zone", StringComparison.OrdinalIgnoreCase))
                    {
                        matchedSpecificZone = true;
                        if (!string.IsNullOrEmpty(field.Zone) && field.Zone.Contains(zt, StringComparison.OrdinalIgnoreCase))
                        {
                            double m = 2.0;
                            descMult *= m;
                            pills.Add(new MultiplierPill { Label = $"Move Scaling ({zt} Zone)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                        }
                    }
                }
                if (!matchedSpecificZone && (desc.Contains("zone is a", StringComparison.OrdinalIgnoreCase) || desc.Contains("zone applies", StringComparison.OrdinalIgnoreCase) || desc.Contains("in a zone", StringComparison.OrdinalIgnoreCase)))
                {
                    if (!string.IsNullOrEmpty(field.Zone))
                    {
                        double m = 2.0;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling ({field.Zone})", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                }

                // Specific Terrain checking
                string[] terrainTypes = ["Electric", "Grassy", "Psychic"];
                bool matchedSpecificTerrain = false;
                foreach (var tt in terrainTypes)
                {
                    if (desc.Contains($"terrain is {tt} Terrain", StringComparison.OrdinalIgnoreCase))
                    {
                        matchedSpecificTerrain = true;
                        if (!string.IsNullOrEmpty(field.Terrain) && field.Terrain.Contains(tt, StringComparison.OrdinalIgnoreCase))
                        {
                            double m = move.IsSync ? 2.0 : (desc.Contains("50%", StringComparison.OrdinalIgnoreCase) ? 1.5 : 2.0);
                            descMult *= m;
                            pills.Add(new MultiplierPill { Label = $"Move Scaling ({tt} Terrain)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                        }
                    }
                }
                if (!matchedSpecificTerrain && (desc.Contains("terrain is", StringComparison.OrdinalIgnoreCase) || desc.Contains("terrain applies", StringComparison.OrdinalIgnoreCase) || desc.Contains("terrain is in effect", StringComparison.OrdinalIgnoreCase)))
                {
                    if (!string.IsNullOrEmpty(field.Terrain))
                    {
                        double m = move.IsSync ? 2.0 : (desc.Contains("50%", StringComparison.OrdinalIgnoreCase) ? 1.5 : 2.0);
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling ({field.Terrain})", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                }

                if (desc.Contains("weather is sunny", StringComparison.OrdinalIgnoreCase) || desc.Contains("during sunny weather", StringComparison.OrdinalIgnoreCase))
                {
                    if (field.Weather == "Sunny") { descMult *= 2.0; pills.Add(new MultiplierPill { Label = "Move Scaling (Sun)", Value = "×2.0", Color = "#fd79a8" }); }
                }
                if (desc.Contains("during a sandstorm", StringComparison.OrdinalIgnoreCase) || desc.Contains("weather is sandstorm", StringComparison.OrdinalIgnoreCase))
                {
                    if (field.Weather == "Sandstorm") { descMult *= 2.0; pills.Add(new MultiplierPill { Label = "Move Scaling (Sand)", Value = "×2.0", Color = "#fd79a8" }); }
                }
                if (desc.Contains("during a hailstorm", StringComparison.OrdinalIgnoreCase) || desc.Contains("during hail", StringComparison.OrdinalIgnoreCase) || desc.Contains("weather is hail", StringComparison.OrdinalIgnoreCase))
                {
                    if (field.Weather == "Hail") { descMult *= 2.0; pills.Add(new MultiplierPill { Label = "Move Scaling (Hail)", Value = "×2.0", Color = "#fd79a8" }); }
                }
                if (desc.Contains("weather conditions, a terrain, or a zone are in effect", StringComparison.OrdinalIgnoreCase) || desc.Contains("weather conditions are in effect", StringComparison.OrdinalIgnoreCase))
                {
                    if (!string.IsNullOrEmpty(field.Weather) || !string.IsNullOrEmpty(field.Terrain) || !string.IsNullOrEmpty(field.Zone))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (WTZ)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 11. Circle active on allied field in description
                if (desc.Contains("circle applies to the allied field of play", StringComparison.OrdinalIgnoreCase) || desc.Contains("when a circle applies", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.CircleActive.Values.Any(d => d.Values.Any(v => v)))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Circle)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 12. Damage Field in description
                if (desc.Contains("applies to the opponent’s field of play", StringComparison.OrdinalIgnoreCase) || desc.Contains("applies to the opponent's field of play", StringComparison.OrdinalIgnoreCase) || desc.Contains("damage field applies", StringComparison.OrdinalIgnoreCase))
                {
                    if (!string.IsNullOrEmpty(enemy.DamageField))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Dmg Field)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 13. Type Rebuff lowered in description
                if (desc.Contains("Type Rebuff is lowered", StringComparison.OrdinalIgnoreCase) || desc.Contains("type rebuff is lowered", StringComparison.OrdinalIgnoreCase))
                {
                    if (enemy.EnemyTypeRebuffs.GetValueOrDefault(move.Type, 0) < 0 || enemy.EnemyTypeRebuffs.Values.Any(v => v < 0))
                    {
                        double m = 2.0;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Rebuff-)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                }

                // 14. Target has sync buff (e.g. +50% or doubled)
                if (desc.Contains("target has a sync buff", StringComparison.OrdinalIgnoreCase))
                {
                    if (enemy.SyncBoosts > 0 || enemy.HasSyncBuff)
                    {
                        double m = desc.Contains("doubled", StringComparison.OrdinalIgnoreCase) ? 2.0 : 1.5;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (Target Sync Buff)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                }

                // 15. User Sync Buff scaling
                if (desc.Contains("user’s sync buff is raised", StringComparison.OrdinalIgnoreCase) || desc.Contains("user's sync buff is raised", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.SyncBoosts > 0)
                    {
                        double m = 1.0 + Math.Min(ally.SyncBoosts, 10) * 0.10;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling (Sync Buffs +{ally.SyncBoosts})", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    }
                }

                // 16. Stats lowered on Target: Defense, Sp. Def, Speed, Attack, Sp. Atk, Accuracy, Evasiveness
                string[] stats = ["def", "spd", "spe", "atk", "spa", "acc", "eva"];
                string[] names = ["Defense", "Sp. Def", "Speed", "Attack", "Sp. Atk", "accuracy", "evasiveness"];
                for (int i = 0; i < stats.Length; i++)
                {
                    if (desc.Contains($"more the target’s {names[i]} is lowered", StringComparison.OrdinalIgnoreCase) ||
                        desc.Contains($"more the target's {names[i]} is lowered", StringComparison.OrdinalIgnoreCase) ||
                        desc.Contains($"more the currently targeted opponent’s {names[i]} is lowered", StringComparison.OrdinalIgnoreCase))
                    {
                        int st = enemy.Stages.GetValueOrDefault(stats[i], 0);
                        if (st < 0)
                        {
                            int stageCount = Math.Clamp(-st, 0, 6);
                            int descStep = move.IsSync ? 167 : 50;
                            int bonus1000 = Math.Min(stageCount * descStep, 1000);
                            double m = (1000 + bonus1000) / 1000.0;
                            descMult *= m;
                            pills.Add(new MultiplierPill { Label = $"Scaling ({names[i]}-)", Value = $"×{m:0.###}", Color = "#fd79a8" });
                        }
                    }
                    if (desc.Contains($"more the user’s {names[i]} is raised", StringComparison.OrdinalIgnoreCase) ||
                        desc.Contains($"more the user's {names[i]} is raised", StringComparison.OrdinalIgnoreCase) ||
                        desc.Contains($"more the user’s {names[i]} is increased", StringComparison.OrdinalIgnoreCase))
                    {
                        int st = ally.Stages.GetValueOrDefault(stats[i], 0);
                        if (st > 0)
                        {
                            int stageCount = Math.Clamp(st, 0, 6);
                            int descStep = move.IsSync ? 167 : 50;
                            int bonus1000 = Math.Min(stageCount * descStep, 1000);
                            double m = (1000 + bonus1000) / 1000.0;
                            descMult *= m;
                            pills.Add(new MultiplierPill { Label = $"Scaling ({names[i]}+)", Value = $"×{m:0.###}", Color = "#fd79a8" });
                        }
                    }
                }

                // 17. All Stats user raised
                if (desc.Contains("more the user’s stats are raised", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more the user's stats are raised", StringComparison.OrdinalIgnoreCase))
                {
                    int sumRaised = 0;
                    foreach (var k in new[] { "atk", "def", "spa", "spd", "spe", "acc", "eva" })
                    {
                        int s = ally.Stages.GetValueOrDefault(k, 0);
                        if (s > 0) sumRaised += Math.Clamp(s, 0, 6);
                    }
                    if (sumRaised > 0)
                    {
                        int descStep = move.IsSync ? 67 : 26;
                        int bonus1000 = Math.Min(sumRaised * descStep, 1200);
                        double m = (1000 + bonus1000) / 1000.0;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Scaling (Stats+)", Value = $"×{m:0.###}", Color = "#fd79a8" });
                    }
                }

                // 18. All Stats target lowered
                if (desc.Contains("more the target’s stats are lowered", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more the target's stats are lowered", StringComparison.OrdinalIgnoreCase))
                {
                    int sumLowered = 0;
                    foreach (var k in new[] { "atk", "def", "spa", "spd", "spe", "acc", "eva" })
                    {
                        int s = enemy.Stages.GetValueOrDefault(k, 0);
                        if (s < 0) sumLowered += Math.Clamp(-s, 0, 6);
                    }
                    if (sumLowered > 0)
                    {
                        int descStep = move.IsSync ? 67 : 26;
                        int bonus1000 = Math.Min(sumLowered * descStep, 1200);
                        double m = (1000 + bonus1000) / 1000.0;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Scaling (Stats-)", Value = $"×{m:0.###}", Color = "#fd79a8" });
                    }
                }

                // 19. Defense or Sp. Def lowered on target
                if (desc.Contains("Defense or Sp. Def are lowered", StringComparison.OrdinalIgnoreCase))
                {
                    int defS = enemy.Stages.GetValueOrDefault("def", 0);
                    int spdS = enemy.Stages.GetValueOrDefault("spd", 0);
                    int sum = (defS < 0 ? -defS : 0) + (spdS < 0 ? -spdS : 0);
                    if (sum > 0)
                    {
                        int bonus1000 = Math.Min(sum * 50, 600);
                        double m = (1000 + bonus1000) / 1000.0;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = "Scaling (Def/SpD-)", Value = $"×{m:0.###}", Color = "#fd79a8" });
                    }
                }

                // 20. None of the target's stats are raised
                if (desc.Contains("none of the target’s stats are raised", StringComparison.OrdinalIgnoreCase) || desc.Contains("none of the target's stats are raised", StringComparison.OrdinalIgnoreCase))
                {
                    if (enemy.Stages.Values.All(v => v <= 0))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (No Target Buffs)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 21. Next Effects (PMUN, SMUN, SYUN) in move descriptions
                if (desc.Contains("more the user’s Physical Moves ↑ Next effect is increased", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more the user's Physical Moves ↑ Next effect is increased", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.PhysicalBoostNext > 0)
                    {
                        double m = 1.0 + ally.PhysicalBoostNext * 0.50;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling (PMUN +{ally.PhysicalBoostNext})", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    }
                }
                if (desc.Contains("more the user’s Special Moves ↑ Next effect is increased", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more the user's Special Moves ↑ Next effect is increased", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.SpecialBoostNext > 0)
                    {
                        double m = 1.0 + ally.SpecialBoostNext * 0.50;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling (SMUN +{ally.SpecialBoostNext})", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    }
                }
                if (desc.Contains("more the user’s Sync Move ↑ Next effect is increased", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more the user's Sync Move ↑ Next effect is increased", StringComparison.OrdinalIgnoreCase))
                {
                    if (ally.SyncMoveBoostNext > 0)
                    {
                        double m = 1.0 + ally.SyncMoveBoostNext * 0.50;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling (SYUN +{ally.SyncMoveBoostNext})", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    }
                }

                // 22. Rebuff on user
                if ((desc.Contains("more the user’s", StringComparison.OrdinalIgnoreCase) || desc.Contains("more the user's", StringComparison.OrdinalIgnoreCase)) &&
                    desc.Contains("Type Rebuff is increased", StringComparison.OrdinalIgnoreCase))
                {
                    int reb = ally.UserTypeRebuffs.GetValueOrDefault(move.Type, 0);
                    if (reb == 0)
                    {
                        reb = ally.UserTypeRebuffs.Values.FirstOrDefault(v => v > 0);
                    }
                    if (reb > 0)
                    {
                        double m = 1.0 + reb * 0.50;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling (User Rebuff +{reb})", Value = $"×{m:0.#}", Color = "#fd79a8" });
                    }
                }

                // 23. User Defense lowered
                if (desc.Contains("more the user’s Defense is lowered", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more the user's Defense is lowered", StringComparison.OrdinalIgnoreCase))
                {
                    int defLowered = ally.Stages.GetValueOrDefault("def", 0);
                    if (defLowered < 0)
                    {
                        int stagesCount = Math.Clamp(-defLowered, 0, 6);
                        double m = 1.0 + stagesCount * 0.20;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling (User Def -{stagesCount})", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    }
                }

                // 24. User Defense or Sp. Def raised
                if (desc.Contains("more the user’s Defense or Sp. Def are raised", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more the user's Defense or Sp. Def are raised", StringComparison.OrdinalIgnoreCase))
                {
                    int defR = Math.Max(0, ally.Stages.GetValueOrDefault("def", 0));
                    int spdR = Math.Max(0, ally.Stages.GetValueOrDefault("spd", 0));
                    int sum = defR + spdR;
                    if (sum > 0)
                    {
                        double m = 1.0 + Math.Min(sum, 12) * 0.10;
                        descMult *= m;
                        pills.Add(new MultiplierPill { Label = $"Move Scaling (User Def/SpD +{sum})", Value = $"×{m:0.##}", Color = "#fd79a8" });
                    }
                }

                // 25. No field effects on opponent and entire field
                if (desc.Contains("no field effects on the opponents’ field of play and also no effects on the entire field of play", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("no field effects on the opponents' field of play and also no effects on the entire field of play", StringComparison.OrdinalIgnoreCase))
                {
                    if (string.IsNullOrEmpty(field.Weather) && string.IsNullOrEmpty(field.Terrain) && string.IsNullOrEmpty(field.Zone) && string.IsNullOrEmpty(enemy.DamageField))
                    {
                        descMult *= 2.0;
                        pills.Add(new MultiplierPill { Label = "Move Scaling (No Field Effects)", Value = "×2.0", Color = "#fd79a8" });
                    }
                }

                // 26. Gauge slots used / amount used
                if (desc.Contains("Uses a maximum of 6 slots of the user’s move gauge", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("The more amount used, the greater the power", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("increases based on the amount used", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 2.0;
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (6 Gauges Used)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                }

                // 27. Fainted allies
                if (desc.Contains("more fainted Pokémon on your team", StringComparison.OrdinalIgnoreCase) ||
                    desc.Contains("more fainted Pokemon on your team", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 2.0;
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (Fainted Allies)", Value = $"×{m:0.#}", Color = "#fd79a8" });
                }

                // 28. Hit count / times used
                if (desc.Contains("power increases each time the user is hit", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 7.0;
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (Max Hits Taken)", Value = "×7.0", Color = "#fd79a8" });
                }
                if (desc.Contains("more times Icicle Crash is used", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 3.0;
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (4x Icicle Crash)", Value = "×3.0", Color = "#fd79a8" });
                }
                if (desc.Contains("power increases for each hit", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 2.0;
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (Multi-hit)", Value = "×2.0", Color = "#fd79a8" });
                }
                if (desc.Contains("power increases when successfully used in succession", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 2.0;
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (Succession)", Value = "×2.0", Color = "#fd79a8" });
                }

                // 29. Specific MP Scaling (Erika Lum Berry, Cynthia Spiritomb)
                if (desc.Contains("remaining MP for the user’s Lum Berry", StringComparison.OrdinalIgnoreCase) || desc.Contains("powers up by 400%", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 5.0; // 400% powerup = 5.0x
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (3 MP Lum Berry)", Value = "×5.0", Color = "#fd79a8" });
                }
                if (desc.Contains("The more MP reduced, the greater the power of this attack", StringComparison.OrdinalIgnoreCase))
                {
                    double m = 2.0;
                    descMult *= m;
                    pills.Add(new MultiplierPill { Label = "Move Scaling (Max MP Reduced)", Value = "×2.0", Color = "#fd79a8" });
                }

                if (descMult > 1.0)
                {
                    return descMult;
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
        else if (rule.Stat == "def_spd")
        {
            int s1 = stages.GetValueOrDefault("def", 0);
            int s2 = stages.GetValueOrDefault("spd", 0);
            count = (isRaised ? Math.Max(0, s1) : Math.Max(0, -s1)) + (isRaised ? Math.Max(0, s2) : Math.Max(0, -s2));
        }
        else if (rule.Stat == "rebuff")
        {
            var rebuffs = rule.Who == "user" ? ally.UserTypeRebuffs : enemy.EnemyTypeRebuffs;
            int reb = rebuffs.GetValueOrDefault(move.Type, 0);
            if (reb == 0 && rule.Who == "user")
            {
                reb = rebuffs.Values.FirstOrDefault(v => v > 0);
            }
            count = isRaised ? Math.Max(0, reb) : Math.Max(0, -reb);
        }
        else if (rule.Stat == "hp")
        {
            int hpPct = rule.Who == "user" ? ally.HpPercent : enemy.HpPercent;
            count = isRaised ? (hpPct >= 100 ? 1 : 0) : Math.Clamp(100 - hpPct, 0, 100);
        }
        else if (rule.Stat == "boost_rank_pmun")
        {
            count = ally.PhysicalBoostNext;
        }
        else if (rule.Stat == "boost_rank_smun")
        {
            count = ally.SpecialBoostNext;
        }
        else if (rule.Stat == "boost_rank_syun")
        {
            count = ally.SyncMoveBoostNext;
        }
        else if (rule.Stat.StartsWith("cond:"))
        {
            string cond = rule.Stat.Substring(5).ToLowerInvariant();
            bool matched = cond switch
            {
                "sunny" => field.Weather == "Sunny",
                "rain" => field.Weather == "Rainy",
                "sandstorm" => field.Weather == "Sandstorm",
                "hail" => field.Weather == "Hail",
                "any_weather" => !string.IsNullOrEmpty(field.Weather),
                "electric_terrain" => field.Terrain == "Electric Terrain",
                "grassy_terrain" => field.Terrain == "Grassy Terrain",
                "psychic_terrain" => field.Terrain == "Psychic Terrain",
                "any_terrain" => !string.IsNullOrEmpty(field.Terrain),
                "burned" => enemy.StatusCondition == "burned",
                "paralyzed" => enemy.StatusCondition == "paralyzed",
                "poisoned" => enemy.StatusCondition == "poisoned" || enemy.StatusCondition == "badly poisoned",
                "asleep" => enemy.StatusCondition == "asleep",
                "frozen" => enemy.StatusCondition == "frozen",
                "any_status" => !string.IsNullOrEmpty(enemy.StatusCondition),
                "user_any_status" => !string.IsNullOrEmpty(ally.StatusCondition),
                "confused" => enemy.VolatileStatus.GetValueOrDefault("confused", false),
                "trapped" => enemy.VolatileStatus.GetValueOrDefault("trapped", false),
                "flinching" => enemy.VolatileStatus.GetValueOrDefault("flinching", false),
                "restrained" => enemy.VolatileStatus.GetValueOrDefault("restrained", false),
                "flinch_confuse_trap" => enemy.VolatileStatus.GetValueOrDefault("confused", false) || enemy.VolatileStatus.GetValueOrDefault("trapped", false) || enemy.VolatileStatus.GetValueOrDefault("flinching", false),
                "target_rebuff_lowered" => enemy.EnemyTypeRebuffs.GetValueOrDefault(move.Type, 0) < 0 || enemy.EnemyTypeRebuffs.Values.Any(v => v < 0),
                "user_rebuff_raised" or "user_rebuff" => ally.UserTypeRebuffs.GetValueOrDefault(move.Type, 0) > 0 || ally.UserTypeRebuffs.Values.Any(v => v > 0),
                "user_rebuff_lowered" => ally.UserTypeRebuffs.GetValueOrDefault(move.Type, 0) < 0 || ally.UserTypeRebuffs.Values.Any(v => v < 0),
                "super_effective" => (!string.IsNullOrEmpty(enemy.Weakness) && string.Equals(move.Type, enemy.Weakness, StringComparison.OrdinalIgnoreCase)),
                "target_sync_buff" => enemy.SyncBoosts > 0 || enemy.HasSyncBuff,
                "target_hp_half" => enemy.HpPercent <= 50,
                "user_prev_move_failed" => true,
                "damage_field" or "damage_field_dmfd_13" => !string.IsNullOrEmpty(enemy.DamageField),
                _ => (!string.IsNullOrEmpty(field.Zone) && cond.Contains("zone") && field.Zone.ToLowerInvariant().Contains(cond.Replace("_zone", "")))
            };
            count = matched ? 1 : 0;
        }
        else
        {
            int s = stages.GetValueOrDefault(rule.Stat, 0);
            count = isRaised ? Math.Clamp(s, 0, 6) : Math.Clamp(-s, 0, 6);
        }

        int step = rule.StepPer1000 > 0 ? rule.StepPer1000 : (
            rule.Stat == "boost_rank_pmun" || rule.Stat == "boost_rank_smun" ? 500 :
            rule.Stat == "boost_rank_syun" ? 500 :
            rule.Stat == "hp" ? 10 :
            rule.Stat.StartsWith("cond:") ? 1000 :
            (move.IsSync ? (rule.Stat == "all_stats" ? 67 : 167) : 50)
        );
        int bonus = count * step;
        if (rule.CapPer1000 > 0)
        {
            bonus = Math.Min(bonus, rule.CapPer1000);
        }
        else if (move.IsSync)
        {
            bonus = Math.Min(bonus, rule.Stat == "all_stats" ? 1200 : 1000);
        }

        double mult = (1000 + bonus) / 1000.0;
        if (mult > 1.0)
        {
            string label = rule.Stat.StartsWith("cond:") ? rule.Stat.Substring(5) : rule.Stat;
            if (rule.Stat == "rebuff")
            {
                label = rule.Who == "user" ? $"User Rebuff +{count}" : $"Target Rebuff -{count}";
            }
            pills.Add(new MultiplierPill { Label = $"Move Scaling ({label})", Value = $"×{mult:0.###}", Color = "#fd79a8" });
        }

        return mult;
    }

    private static bool MatchesMoveName(string moveName, string targetName, bool isSync)
    {
        if (string.Equals(moveName, targetName, StringComparison.OrdinalIgnoreCase)) return true;
        string normMove = moveName.Replace("\r", "").Replace("\n", " ").Trim();
        string normTarget = targetName.Replace("\r", "").Replace("\n", " ").Trim();
        if (string.Equals(normMove, normTarget, StringComparison.OrdinalIgnoreCase)) return true;
        if (isSync && (normTarget.Contains("Sync Move", StringComparison.OrdinalIgnoreCase) ||
                       normTarget.EndsWith("Sync Beam", StringComparison.OrdinalIgnoreCase) ||
                       normTarget.EndsWith("Sync Impact", StringComparison.OrdinalIgnoreCase) ||
                       normTarget.EndsWith("Tera Blast", StringComparison.OrdinalIgnoreCase) ||
                       normMove.Contains(normTarget, StringComparison.OrdinalIgnoreCase) ||
                       normTarget.Contains(normMove, StringComparison.OrdinalIgnoreCase)))
        {
            return true;
        }
        return false;
    }

    public static int GetSyncBuffsGrantedBySync(CombatantState ally)
    {
        if (ally.Pair == null) return 1;
        bool isEx = ally.StarLevel.Contains("EX", StringComparison.OrdinalIgnoreCase) || ally.StarLevel.Contains("6★");
        bool isSupportBase = ally.Pair.Role.StartsWith("Support", StringComparison.OrdinalIgnoreCase);
        bool isSupportExRole = ally.HasExRole && !string.IsNullOrEmpty(ally.Pair.ExRole) && ally.Pair.ExRole.StartsWith("Support", StringComparison.OrdinalIgnoreCase);
        return (isEx && (isSupportBase || isSupportExRole)) ? 2 : 1;
    }

    public static bool IsSyncTransformationForm(SyncPairDetail? pair, int formIndex)
    {
        if (pair == null || formIndex <= 0 || pair.Variations == null || formIndex > pair.Variations.Count)
            return false;

        var form = pair.Variations[formIndex - 1];
        string formName = form.FormName ?? string.Empty;

        // Terastal Form in Terapagos is automatic upon battle entry (passive Prepare for Battle), so it does NOT require a sync move
        if (formName.Equals("Terastal Form", StringComparison.OrdinalIgnoreCase))
            return false;

        // Mega Evolution always requires a sync move
        if (formName.Contains("Mega", StringComparison.OrdinalIgnoreCase) || (pair.HasMega && pair.Variations.Count == 1))
            return true;

        // Stellar Form / Sync Terastallization requires a sync move
        if (formName.Contains("Stellar", StringComparison.OrdinalIgnoreCase) || 
            formName.Equals("Tera", StringComparison.OrdinalIgnoreCase) ||
            form.TerastalMoveId > 0)
        {
            return true;
        }

        return false;
    }

    public static readonly Dictionary<string, string> TypeToDefaultMaxMove = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Normal"] = "Max Strike",
        ["Fire"] = "Max Flare",
        ["Water"] = "Max Geyser",
        ["Grass"] = "Max Overgrowth",
        ["Electric"] = "Max Lightning",
        ["Ice"] = "Max Hailstorm",
        ["Fighting"] = "Max Knuckle",
        ["Poison"] = "Max Ooze",
        ["Ground"] = "Max Quake",
        ["Flying"] = "Max Airstream",
        ["Psychic"] = "Max Mindstorm",
        ["Bug"] = "Max Flutterby",
        ["Rock"] = "Max Rockfall",
        ["Ghost"] = "Max Phantasm",
        ["Dragon"] = "Max Wyrmwind",
        ["Dark"] = "Max Darkness",
        ["Steel"] = "Max Steelspike",
        ["Fairy"] = "Max Starfall"
    };

    public static readonly Dictionary<string, (int Id, string Desc)> KnownMaxMoves = new(StringComparer.OrdinalIgnoreCase)
    {
        ["G-Max Wildfire"] = (7047, "Applies Fire Damage Field to the opponents' field of play. (Fire Damage Field: The sync pairs will take Fire-type damage whenever they take an action.)"),
        ["Max Airstream"] = (7008, "Raises the Speed of all allied sync pairs by 2 stat ranks."),
        ["Max Quake"] = (7011, "Raises the Sp. Def of all allied sync pairs by 2 stat ranks."),
        ["Max Flare"] = (7022, "Makes the weather sunny."),
        ["Max Strike"] = (7003, "Lowers the Speed of all opposing sync pairs by 2 stat ranks."),
        ["Max Geyser"] = (7024, "Makes the weather rainy."),
        ["Max Knuckle"] = (7005, "Raises the Attack of all allied sync pairs by 2 stat ranks."),
        ["Max Lightning"] = (7027, "Turns the field of play’s terrain into Electric Terrain."),
        ["Max Overgrowth"] = (7025, "Turns the field of play’s terrain into Grassy Terrain."),
        ["Max Mindstorm"] = (7030, "Turns the field of play’s terrain into Psychic Terrain."),
        ["Max Rockfall"] = (7013, "Causes a sandstorm."),
        ["Max Hailstorm"] = (7029, "Causes a hailstorm."),
        ["Max Ooze"] = (7010, "Raises the Sp. Atk of all allied sync pairs by 2 stat ranks."),
        ["Max Steelspike"] = (7019, "Raises the Defense of all allied sync pairs by 2 stat ranks."),
        ["Max Wyrmwind"] = (7034, "Lowers the Attack of all opposing sync pairs by 2 stat ranks."),
        ["Max Darkness"] = (7035, "Lowers the Sp. Def of all opposing sync pairs by 2 stat ranks."),
        ["Max Starfall"] = (7038, "Turns the field of play’s terrain into Misty Terrain."),
        ["Max Flutterby"] = (7016, "Lowers the Sp. Atk of all opposing sync pairs by 2 stat ranks."),
        ["Max Phantasm"] = (7018, "Lowers the Defense of all opposing sync pairs by 2 stat ranks."),
        ["G-Max Replenish"] = (7000, "Has a chance (50%) of restoring one MP for the user."),
        ["G-Max Terror"] = (7001, "Applies the no evasion effect to all opposing sync pairs."),
        ["G-Max Smite"] = (7040, "Leaves all opposing sync pairs confused."),
        ["G-Max Rapid Flow"] = (7041, "Attacks with three consecutive hits."),
        ["G-Max Volt Crash"] = (7042, "Leaves all opposing sync pairs paralyzed."),
        ["G-Max Volcalith"] = (7043, "Applies Rock Damage Field to the opponents' field of play."),
        ["G-Max Resonance"] = (7044, "Applies the Physical Damage Reduction and Special Damage Reduction effects to the allied field of play."),
        ["G-Max Drum Solo"] = (7045, "Ignores passive skills that would reduce damage or protect the target."),
        ["G-Max Fireball"] = (7050, "Makes the weather sunny."),
        ["G-Max Malodor"] = (7048, "Leaves all opposing sync pairs poisoned."),
        ["G-Max Steelsurge"] = (7049, "Applies Steel Damage Field to the opponents' field of play."),
        ["G-Max Stun Shock"] = (7051, "Leaves all opposing sync pairs poisoned or paralyzed."),
        ["G-Max Centiferno"] = (7052, "Leaves all opposing sync pairs trapped."),
        ["G-Max Snooze"] = (7054, "Leaves all opposing sync pairs asleep.")
    };

    public bool HasDynamax(SyncPairDetail? pair)
    {
        if (pair == null) return false;
        if (pair.HasDynamax) return true;
        if (pair.Variations != null && pair.Variations.Any(v => v.FormId == 4 || 
                                                               v.FormName.Equals("Dynamax", StringComparison.OrdinalIgnoreCase) ||
                                                               v.FormName.Equals("Form 4", StringComparison.OrdinalIgnoreCase)))
            return true;

        bool hasDMaxGrid = pair.Grid != null && pair.Grid.Any(c =>
        {
            string t = c.Title.Replace("\r", "").Replace("\n", " ");
            return c.ColorKind.Equals("max", StringComparison.OrdinalIgnoreCase) ||
                   t.Contains("G-Max", StringComparison.OrdinalIgnoreCase) ||
                   (t.Contains("Max Move", StringComparison.OrdinalIgnoreCase) && 
                    !t.Contains("DR", StringComparison.OrdinalIgnoreCase) && 
                    !t.Contains("Damage Reduction", StringComparison.OrdinalIgnoreCase)) ||
                   (t.StartsWith("Max ", StringComparison.OrdinalIgnoreCase) && 
                    t.Contains(":") && 
                    !t.Contains("Maximum", StringComparison.OrdinalIgnoreCase) && 
                    !t.Contains("Tera Blast", StringComparison.OrdinalIgnoreCase) && 
                    !t.Contains("Sync", StringComparison.OrdinalIgnoreCase));
        });
        if (hasDMaxGrid) return true;

        bool hasDMaxPassive = pair.Passives != null && pair.Passives.Any(p =>
            (p.Name.StartsWith("MAX ", StringComparison.OrdinalIgnoreCase) || p.Name.Contains("Max Moves", StringComparison.OrdinalIgnoreCase)) &&
            !p.Description.Contains("opponent's max move", StringComparison.OrdinalIgnoreCase) &&
            !p.Description.Contains("opposing sync pairs' max moves", StringComparison.OrdinalIgnoreCase)
        );
        return hasDMaxPassive;
    }

    public bool IsDynamaxActive(SyncPairDetail? pair, int formIndex)
    {
        if (pair == null || formIndex <= 0 || pair.Variations == null || formIndex > pair.Variations.Count)
            return false;
        var form = pair.Variations[formIndex - 1];
        return form.FormId == 4 || 
               form.FormName.Equals("Dynamax", StringComparison.OrdinalIgnoreCase) ||
               form.FormName.Equals("Form 4", StringComparison.OrdinalIgnoreCase);
    }

    public List<MoveItem> GetMaxMoves(SyncPairDetail? pair)
    {
        var list = new List<MoveItem>();
        if (pair == null || !HasDynamax(pair)) return list;

        var gridMaxNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var cell in pair.Grid)
        {
            if (cell.PowerBonus != null)
            {
                foreach (var key in cell.PowerBonus.Keys)
                {
                    string norm = key.Replace("\r", "").Replace("\n", " ").Trim();
                    if ((norm.StartsWith("Max ", StringComparison.OrdinalIgnoreCase) || norm.StartsWith("G-Max", StringComparison.OrdinalIgnoreCase)) &&
                        !norm.Contains("Sync", StringComparison.OrdinalIgnoreCase))
                    {
                        gridMaxNames.Add(norm);
                    }
                }
            }
            string titleNorm = cell.Title.Replace("\r", "").Replace("\n", " ").Trim();
            if (titleNorm.StartsWith("G-Max", StringComparison.OrdinalIgnoreCase) ||
                (titleNorm.StartsWith("Max ", StringComparison.OrdinalIgnoreCase) && !titleNorm.Contains("Maximum", StringComparison.OrdinalIgnoreCase)))
            {
                string candidate = titleNorm.Contains(":") ? titleNorm.Substring(0, titleNorm.IndexOf(":")).Trim() : titleNorm;
                if (candidate.StartsWith("Max ", StringComparison.OrdinalIgnoreCase) || candidate.StartsWith("G-Max", StringComparison.OrdinalIgnoreCase))
                {
                    gridMaxNames.Add(candidate);
                }
            }
        }

        bool hitsAll = pair.Passives != null && pair.Passives.Any(p =>
            p.Name.Equals("Targets Maxed", StringComparison.OrdinalIgnoreCase) ||
            p.Name.Contains("P-Moves & Max Moves Expansion", StringComparison.OrdinalIgnoreCase) ||
            p.Name.Contains("Champion Who Hears the Cheers", StringComparison.OrdinalIgnoreCase) ||
            p.Description.Contains("sync move or max move attacks an opponent, the target becomes all opposing", StringComparison.OrdinalIgnoreCase) ||
            p.Description.Contains("max move attacks an opponent, the target becomes all opposing", StringComparison.OrdinalIgnoreCase) ||
            p.Description.Contains("max moves attacks an opponent, the target becomes all opposing", StringComparison.OrdinalIgnoreCase)
        );

        bool normalBecomesGround = pair.Passives != null && pair.Passives.Any(p => p.Name.Contains("Giovanni’s Cunning") || p.Name.Contains("Giovanni's Cunning"));

        bool isGigantamaxCharizard = (pair.MonsterName != null && pair.MonsterName.Contains("Charizard", StringComparison.OrdinalIgnoreCase)) &&
            (pair.Variations != null && pair.Variations.Any(v => v.ActorId != null && v.ActorId.Contains("glizardon", StringComparison.OrdinalIgnoreCase)));

        var regularAtkMoves = pair.Moves.Where(m => !m.IsSync && !m.Category.Equals("Status", StringComparison.OrdinalIgnoreCase) && int.TryParse(m.Power, out int p) && p > 0).ToList();

        int maxMoveFallbackId = 99000;
        var seenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var atkMove in regularAtkMoves)
        {
            string moveType = atkMove.Type;
            if (normalBecomesGround && moveType.Equals("Normal", StringComparison.OrdinalIgnoreCase))
            {
                moveType = "Ground";
            }

            string? matchedName = null;
            foreach (var gn in gridMaxNames)
            {
                if (gn.StartsWith("G-Max", StringComparison.OrdinalIgnoreCase))
                {
                    if (string.Equals(moveType, pair.Type, StringComparison.OrdinalIgnoreCase))
                    {
                        matchedName = gn;
                        break;
                    }
                }
                else if (TypeToDefaultMaxMove.TryGetValue(moveType, out var expectedName) && string.Equals(gn, expectedName, StringComparison.OrdinalIgnoreCase))
                {
                    matchedName = gn;
                    break;
                }
            }

            if (matchedName == null && isGigantamaxCharizard && string.Equals(moveType, "Fire", StringComparison.OrdinalIgnoreCase))
            {
                matchedName = "G-Max Wildfire";
            }

            matchedName ??= TypeToDefaultMaxMove.TryGetValue(moveType, out var defName) ? defName : "Max Strike";

            // In Pokémon Masters EX, Max Strike has base power 450 (scaling to 540). All other standard Max Moves & G-Max moves have base power 400 (scaling to 480).
            int maxBasePower = string.Equals(matchedName, "Max Strike", StringComparison.OrdinalIgnoreCase) ? 450 : 400;

            if (seenNames.Contains(matchedName))
            {
                var existing = list.FirstOrDefault(m => string.Equals(m.Name, matchedName, StringComparison.OrdinalIgnoreCase));
                if (existing != null && int.TryParse(existing.Power, out int ep) && maxBasePower > ep)
                {
                    existing.Power = maxBasePower.ToString();
                }
                continue;
            }

            seenNames.Add(matchedName);

            int moveId = maxMoveFallbackId++;
            string moveDesc = "Max move. Never misses. Cannot be reduced by multiple target damage reduction.";
            if (KnownMaxMoves.TryGetValue(matchedName, out var known))
            {
                moveId = known.Id;
                moveDesc = known.Desc;
            }

            list.Add(new MoveItem
            {
                Id = moveId,
                Slot = 6 + list.Count,
                Name = matchedName,
                Type = moveType,
                Category = atkMove.Category,
                Power = maxBasePower.ToString(),
                Accuracy = "-",
                Gauge = "-",
                Target = hitsAll ? "All opponents" : "An opponent",
                Description = moveDesc,
                IsSync = false,
                IsMax = true,
                MaxUses = 1
            });
        }

        return list;
    }
}