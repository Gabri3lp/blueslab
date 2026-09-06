using System.Text.Json.Serialization;

namespace BluesLab.Models;

public class TeamConfigDto
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8];
    public string Name { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public string? Description { get; set; }

    // Stage selection
    public string SelectedLeagueId { get; set; } = "circuit_1";
    public string SelectedFightId { get; set; } = "circuit_1_falkner";

    // Field conditions
    public FieldStateDto Field { get; set; } = new();

    // Allied team side effects
    public int AllySyncBuffs { get; set; }
    public bool AlliedPhysicalDamageReduction { get; set; }
    public bool AlliedSpecialDamageReduction { get; set; }
    public Dictionary<string, List<string>> ActiveCircles { get; set; } = new();

    // Allies (3 slots)
    public List<AllySlotDto> Allies { get; set; } = new();

    // Active indices
    public int ActiveAttackerIndex { get; set; } = 0;
    public int ActiveTargetIndex { get; set; } = 1;

    // Enemy side effects & targets (3 slots)
    public int EnemySyncBuffs { get; set; }
    public bool EnemyPhysicalDamageReduction { get; set; }
    public bool EnemySpecialDamageReduction { get; set; }
    public string EnemyDamageField { get; set; } = string.Empty;
    public List<EnemySlotDto> Enemies { get; set; } = new();
}

public class AllySlotDto
{
    public string? TrainerId { get; set; }
    public int FormIndex { get; set; }
    public int MoveLevel { get; set; } = 5;
    public int SuperAwakeningLevel { get; set; }
    public bool HasExRole { get; set; }
    public string StarLevel { get; set; } = "5★ EX";
    public string CharLevel { get; set; } = "180";
    public string? LuckySkillName { get; set; }
    public Dictionary<string, int> Stages { get; set; } = new();
    public int PhysicalBoostNext { get; set; }
    public int SpecialBoostNext { get; set; }
    public int SyncMoveBoostNext { get; set; }
    public bool IsCriticalMove { get; set; } = true;
    public bool SuperEffectiveNext { get; set; }
    public List<long> ActiveGridCells { get; set; } = new();
}

public class EnemySlotDto
{
    public string CustomTrainerName { get; set; } = string.Empty;
    public string CustomPokemonName { get; set; } = string.Empty;
    public string CustomIconUrl { get; set; } = string.Empty;
    public string Weakness { get; set; } = string.Empty;
    public Dictionary<string, int> ManualStats { get; set; } = new();
    public Dictionary<string, int> Stages { get; set; } = new();
    public Dictionary<string, int> Mitigations { get; set; } = new();
    public string StatusCondition { get; set; } = string.Empty;
    public Dictionary<string, bool> VolatileStatus { get; set; } = new();
    public bool PhysicalBreak { get; set; }
    public bool SpecialBreak { get; set; }
    public Dictionary<string, int> Rebuffs { get; set; } = new();
}

public class FieldStateDto
{
    public string Weather { get; set; } = string.Empty;
    public bool WeatherEx { get; set; }
    public string Terrain { get; set; } = string.Empty;
    public bool TerrainEx { get; set; }
    public string Zone { get; set; } = string.Empty;
    public bool ZoneEx { get; set; }
}

public class TeamSavedItemDto
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public string? Description { get; set; }
    public List<string> PairTrainerIds { get; set; } = new();
    public List<string> PairDisplayNames { get; set; } = new();
    public List<string> PairIconUrls { get; set; } = new();
    public string StageTitle { get; set; } = string.Empty;
    public TeamConfigDto Config { get; set; } = new();
}

public class TeamComparisonMoveResult
{
    public string MoveName { get; set; } = string.Empty;
    public string MoveType { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public bool IsSync { get; set; }
    public bool IsMax { get; set; }

    // Config A values
    public double DamageA { get; set; }
    public double HpPercentA { get; set; }

    // Config B values
    public double DamageB { get; set; }
    public double HpPercentB { get; set; }

    // Comparison diff
    public double DamageDiff => DamageB - DamageA;
    public double DiffPercent => DamageA > 0 ? ((DamageB - DamageA) / DamageA) * 100.0 : (DamageB > 0 ? 100.0 : 0.0);
    public bool IsBetterInB => DamageB > DamageA;
}

public class TeamComparisonSummary
{
    public string ConfigAName { get; set; } = "Current Team";
    public string ConfigBName { get; set; } = "Compared Team";
    public List<TeamComparisonMoveResult> MoveResults { get; set; } = new();
}
