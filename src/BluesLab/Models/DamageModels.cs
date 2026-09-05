namespace BluesLab.Models;

public class CombatantState
{
    public static readonly string[] StatLabels = ["hp", "atk", "def", "spa", "spd", "spe"];
    public static readonly string[] StageLabels = ["hp", "atk", "def", "spa", "spd", "spe", "acc", "eva", "crit"];
    public static readonly string[] AllTypes = [
        "Normal", "Fire", "Water", "Grass", "Electric", "Ice",
        "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
        "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy", "Stellar"
    ];
    public static readonly string[] CircleRegions = [
        "Kanto", "Johto", "Hoenn", "Sinnoh", "Unova",
        "Kalos", "Alola", "Galar", "Paldea", "Pasio"
    ];
    public static readonly string[] ValidZoneTypes = [
        "Normal", "Ice", "Fighting", "Poison", "Ground",
        "Flying", "Bug", "Rock", "Ghost", "Dragon",
        "Dark", "Steel", "Fairy"
    ];
    public static readonly Dictionary<string, string> TypeIconMap = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Normal"] = "img/battle/TYPE_001.png",
        ["Fire"] = "img/battle/TYPE_002.png",
        ["Water"] = "img/battle/TYPE_003.png",
        ["Electric"] = "img/battle/TYPE_004.png",
        ["Grass"] = "img/battle/TYPE_005.png",
        ["Ice"] = "img/battle/TYPE_006.png",
        ["Fighting"] = "img/battle/TYPE_007.png",
        ["Poison"] = "img/battle/TYPE_008.png",
        ["Ground"] = "img/battle/TYPE_009.png",
        ["Flying"] = "img/battle/TYPE_010.png",
        ["Psychic"] = "img/battle/TYPE_011.png",
        ["Bug"] = "img/battle/TYPE_012.png",
        ["Rock"] = "img/battle/TYPE_013.png",
        ["Ghost"] = "img/battle/TYPE_014.png",
        ["Dragon"] = "img/battle/TYPE_015.png",
        ["Dark"] = "img/battle/TYPE_016.png",
        ["Steel"] = "img/battle/TYPE_017.png",
        ["Fairy"] = "img/battle/TYPE_018.png",
        ["Stellar"] = "img/battle/TYPE_099.png"
    };

    public static string GetTypeIcon(string type)
    {
        return TypeIconMap.TryGetValue(type, out var icon) ? icon : "img/battle/NONE.png";
    }

    public SyncPairDetail? Pair { get; set; }
    public string CustomTrainerName { get; set; } = string.Empty;
    public string CustomPokemonName { get; set; } = string.Empty;
    public string CustomIconUrl { get; set; } = string.Empty;
    public int FormIndex { get; set; }
    public string CharLevel { get; set; } = "180";
    public string StarLevel { get; set; } = "5★ EX";
    public bool HasExRole { get; set; } = true;
    public int SuperAwakeningLevel { get; set; }
    public int MoveLevel { get; set; } = 5;

    public Dictionary<string, int> Stages { get; set; } = new();
    public string StatusCondition { get; set; } = string.Empty;
    public Dictionary<string, bool> VolatileStatus { get; set; } = new();
    public int HpPercent { get; set; } = 100;
    public int SyncBoosts { get; set; }

    public bool MoveGaugeAccel { get; set; }
    public bool HasSyncBuff { get; set; }
    public bool PrevMoveFailed { get; set; }

    public bool IsCriticalMove { get; set; } = true;
    public int PhysicalBoostNext { get; set; }
    public int SpecialBoostNext { get; set; }
    public bool SuperEffectiveNext { get; set; }
    public bool PhysicalBreak { get; set; }
    public bool SpecialBreak { get; set; }
    public bool PhysicalDamageReduction { get; set; }
    public bool SpecialDamageReduction { get; set; }
    public int SyncMoveBoostNext { get; set; }

    public Dictionary<string, int> Gear { get; set; } = new();
    public Dictionary<string, Dictionary<string, bool>> CircleActive { get; set; } = new();
    public Dictionary<string, int> CircleAllyCount { get; set; } = new();
    public Dictionary<string, int> MasterPassiveAllyCount { get; set; } = new();
    public string? LuckySkillName { get; set; }

    public Dictionary<string, int> UserTypeRebuffs { get; set; } = new();
    public Dictionary<string, int> EnemyTypeRebuffs { get; set; } = new();
    public int StellarRebuff { get; set; }
    public Dictionary<string, int> Mitigations { get; set; } = new();
    public Dictionary<string, int> ManualStats { get; set; } = new();
    public string Weakness { get; set; } = string.Empty;
    public string DamageField { get; set; } = string.Empty;

    public static CombatantState CreateAlly(SyncPairDetail? pair = null)
    {
        var ally = new CombatantState
        {
            Pair = pair,
            HasExRole = pair?.HasEx == true && !string.IsNullOrEmpty(pair.ExRole),
            SuperAwakeningLevel = pair?.HasSuperAwakening == true ? 5 : 0,
            StarLevel = pair?.HasEx == true ? "5★ EX" : (pair?.Rarity == 5 ? "5★ 20/20" : $"{pair?.Rarity ?? 5}★")
        };

        foreach (var s in StageLabels)
            ally.Stages[s] = s == "crit" ? 3 : 6;

        foreach (var s in StatLabels)
            ally.Gear[s] = 100;

        foreach (var r in CircleRegions)
        {
            ally.CircleActive[r] = new Dictionary<string, bool>
            {
                ["physical"] = false,
                ["special"] = false,
                ["defensive"] = false
            };
            ally.CircleAllyCount[r] = 1;
        }

        foreach (var t in AllTypes)
        {
            ally.UserTypeRebuffs[t] = 0;
            ally.EnemyTypeRebuffs[t] = 0;
        }

        ally.VolatileStatus = new Dictionary<string, bool>
        {
            ["confused"] = false,
            ["flinching"] = false,
            ["trapped"] = false,
            ["restrained"] = false
        };

        return ally;
    }

    public static CombatantState CreateEnemy()
    {
        var enemy = new CombatantState
        {
            IsCriticalMove = false,
            ManualStats = new Dictionary<string, int>
            {
                ["hp"] = 1958000,
                ["atk"] = 5400,
                ["def"] = 95,
                ["spa"] = 5400,
                ["spd"] = 95,
                ["spe"] = 72
            },
            Mitigations = new Dictionary<string, int>
            {
                ["atk"] = 5,
                ["def"] = 5,
                ["spa"] = 5,
                ["spd"] = 5,
                ["spe"] = 5
            }
        };

        foreach (var s in StageLabels)
            enemy.Stages[s] = s == "crit" ? 0 : -6;

        foreach (var t in AllTypes)
        {
            enemy.UserTypeRebuffs[t] = 0;
            enemy.EnemyTypeRebuffs[t] = 0;
        }

        enemy.VolatileStatus = new Dictionary<string, bool>
        {
            ["confused"] = false,
            ["flinching"] = false,
            ["trapped"] = false,
            ["restrained"] = false
        };

        return enemy;
    }
}

public class FieldState
{
    public string Zone { get; set; } = string.Empty;
    public bool ZoneEx { get; set; }
    public string Terrain { get; set; } = string.Empty;
    public bool TerrainEx { get; set; }
    public string Weather { get; set; } = string.Empty;
    public bool WeatherEx { get; set; }
    public int TargetCount { get; set; } = 3;
}

public class DamageResult
{
    public string MoveName { get; set; } = string.Empty;
    public int BasePower { get; set; }
    public int ScaledMovePower { get; set; }
    public int AttackerStat { get; set; }
    public int DefenderStat { get; set; }
    public double StatRatio { get; set; }
    public double BattleMultiplier { get; set; }
    public List<int> Rolls { get; set; } = new();
    public int MinDamage => Rolls.Count > 0 ? Rolls.First() : 0;
    public int AvgDamage => Rolls.Count > 0 ? (int)Math.Round(Rolls.Average()) : 0;
    public int MaxDamage => Rolls.Count > 0 ? Rolls.Last() : 0;
    public List<MultiplierPill> Breakdown { get; set; } = new();

    public int TargetMaxHp { get; set; }
    public double AvgHpPercent => TargetMaxHp > 0 ? (double)AvgDamage / TargetMaxHp * 100.0 : 0.0;
    public double MinHpPercent => TargetMaxHp > 0 ? (double)MinDamage / TargetMaxHp * 100.0 : 0.0;
    public double MaxHpPercent => TargetMaxHp > 0 ? (double)MaxDamage / TargetMaxHp * 100.0 : 0.0;
    public double RemainingHpPercent => Math.Max(0.0, 100.0 - AvgHpPercent);
    public double MinRemainingHpPercent => Math.Max(0.0, 100.0 - MaxHpPercent);
    public double MaxRemainingHpPercent => Math.Max(0.0, 100.0 - MinHpPercent);
    public bool IsOHKO => TargetMaxHp > 0 && AvgDamage >= TargetMaxHp;
}

public class MultiplierPill
{
    public string Label { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;
    public string Color { get; set; } = string.Empty;
}

public class TeamMoveDamageResult
{
    public MoveItem Move { get; set; } = new();
    public bool IsAoE { get; set; }
    public DamageResult LeftDamage { get; set; } = new();
    public DamageResult CenterDamage { get; set; } = new();
    public DamageResult RightDamage { get; set; } = new();
    public int ActiveTargetIndex { get; set; } = 1;
    public DamageResult ActiveTargetDamage => ActiveTargetIndex switch
    {
        0 => LeftDamage,
        1 => CenterDamage,
        _ => RightDamage
    };
}