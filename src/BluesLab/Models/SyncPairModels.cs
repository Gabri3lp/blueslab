using System.Text.Json.Serialization;

namespace BluesLab.Models;

public class PairManifestItem
{
    [JsonPropertyName("trainerId")]
    public string TrainerId { get; set; } = string.Empty;

    [JsonPropertyName("monsterId")]
    public string MonsterId { get; set; } = string.Empty;

    [JsonPropertyName("monsterBaseId")]
    public string MonsterBaseId { get; set; } = string.Empty;

    [JsonPropertyName("displayName")]
    public string DisplayName { get; set; } = string.Empty;

    [JsonPropertyName("trainerName")]
    public string TrainerName { get; set; } = string.Empty;

    [JsonPropertyName("monsterName")]
    public string MonsterName { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("exRole")]
    public string ExRole { get; set; } = string.Empty;

    [JsonPropertyName("rarity")]
    public int Rarity { get; set; } = 5;

    [JsonPropertyName("hasEx")]
    public bool HasEx { get; set; }

    [JsonPropertyName("hasMega")]
    public bool HasMega { get; set; }

    [JsonPropertyName("hasTera")]
    public bool HasTera { get; set; }

    [JsonPropertyName("hasDynamax")]
    public bool HasDynamax { get; set; }

    [JsonPropertyName("hasSuperAwakening")]
    public bool HasSuperAwakening { get; set; }

    [JsonPropertyName("superAwakeningPassive")]
    public PassiveItem? SuperAwakeningPassive { get; set; }

    [JsonPropertyName("iconUrl")]
    public string IconUrl { get; set; } = string.Empty;

    [JsonPropertyName("pokemonIconUrl")]
    public string PokemonIconUrl { get; set; } = string.Empty;

    [JsonPropertyName("gridTileCount")]
    public int GridTileCount { get; set; }

    [JsonPropertyName("trainerBaseId")]
    public string TrainerBaseId { get; set; } = string.Empty;

    [JsonPropertyName("trainerKey")]
    public string TrainerKey { get; set; } = string.Empty;

    [JsonPropertyName("pokemonKey")]
    public string PokemonKey { get; set; } = string.Empty;
}

public class SyncPairDetail
{
    [JsonPropertyName("trainerId")]
    public string TrainerId { get; set; } = string.Empty;

    [JsonPropertyName("trainerBaseId")]
    public string TrainerBaseId { get; set; } = string.Empty;

    [JsonPropertyName("monsterId")]
    public string MonsterId { get; set; } = string.Empty;

    [JsonPropertyName("monsterBaseId")]
    public string MonsterBaseId { get; set; } = string.Empty;

    [JsonPropertyName("displayName")]
    public string DisplayName { get; set; } = string.Empty;

    [JsonPropertyName("trainerName")]
    public string TrainerName { get; set; } = string.Empty;

    [JsonPropertyName("monsterName")]
    public string MonsterName { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("weakness")]
    public string Weakness { get; set; } = string.Empty;

    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("exRole")]
    public string ExRole { get; set; } = string.Empty;

    [JsonPropertyName("rarity")]
    public int Rarity { get; set; } = 5;

    [JsonPropertyName("hasEx")]
    public bool HasEx { get; set; }

    [JsonPropertyName("hasMega")]
    public bool HasMega { get; set; }

    [JsonPropertyName("hasTera")]
    public bool HasTera { get; set; }

    [JsonPropertyName("hasDynamax")]
    public bool HasDynamax { get; set; }

    [JsonPropertyName("hasSuperAwakening")]
    public bool HasSuperAwakening { get; set; }

    [JsonPropertyName("superAwakeningPassive")]
    public PassiveItem? SuperAwakeningPassive { get; set; }

    [JsonPropertyName("syncMoveName")]
    public string SyncMoveName { get; set; } = string.Empty;

    [JsonPropertyName("iconUrl")]
    public string IconUrl { get; set; } = string.Empty;

    [JsonPropertyName("pokemonIconUrl")]
    public string PokemonIconUrl { get; set; } = string.Empty;

    [JsonPropertyName("stats")]
    public PairStats Stats { get; set; } = new();

    [JsonPropertyName("moves")]
    public List<MoveItem> Moves { get; set; } = new();

    [JsonPropertyName("passives")]
    public List<PassiveItem> Passives { get; set; } = new();

    [JsonPropertyName("variations")]
    public List<VariationItem> Variations { get; set; } = new();

    [JsonPropertyName("grid")]
    public List<GridCellItem> Grid { get; set; } = new();
}

public class PairStats
{
    [JsonPropertyName("hp")]
    public List<int> Hp { get; set; } = new();

    [JsonPropertyName("atk")]
    public List<int> Atk { get; set; } = new();

    [JsonPropertyName("def")]
    public List<int> Def { get; set; } = new();

    [JsonPropertyName("spa")]
    public List<int> Spa { get; set; } = new();

    [JsonPropertyName("spd")]
    public List<int> Spd { get; set; } = new();

    [JsonPropertyName("spe")]
    public List<int> Spe { get; set; } = new();

    private static readonly int[] BreakpointLevels = [1, 30, 45, 100, 120, 140, 200];

    public int GetStatAtLevel(string statName, int level)
    {
        var values = statName.ToLowerInvariant() switch
        {
            "hp" => Hp,
            "atk" => Atk,
            "def" => Def,
            "spa" => Spa,
            "spd" => Spd,
            "spe" => Spe,
            _ => null
        };

        if (values == null || values.Count == 0) return 0;
        if (values.Count < 7) return values.Last();

        level = Math.Clamp(level, 1, 200);

        for (int i = 0; i < BreakpointLevels.Length; i++)
        {
            if (level == BreakpointLevels[i])
                return values[i];
            if (level < BreakpointLevels[i])
            {
                if (i == 0) return values[0];
                int prevLvl = BreakpointLevels[i - 1];
                int nextLvl = BreakpointLevels[i];
                int prevVal = values[i - 1];
                int nextVal = values[i];
                double factor = (double)(level - prevLvl) / (nextLvl - prevLvl);
                return (int)Math.Floor(prevVal + (nextVal - prevVal) * factor);
            }
        }

        return values.Last();
    }
}

public class MoveItem
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("slot")]
    public int Slot { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("category")]
    public string Category { get; set; } = string.Empty;

    [JsonPropertyName("power")]
    public string Power { get; set; } = "0";

    [JsonPropertyName("accuracy")]
    public string Accuracy { get; set; } = "100";

    [JsonPropertyName("gauge")]
    public string Gauge { get; set; } = "0";

    [JsonPropertyName("target")]
    public string Target { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("isSync")]
    public bool IsSync { get; set; }

    [JsonPropertyName("isMax")]
    public bool IsMax { get; set; }

    [JsonPropertyName("maxUses")]
    public int MaxUses { get; set; }

    [JsonPropertyName("uses")]
    public int Uses { get => MaxUses; set => MaxUses = value; }

    [JsonPropertyName("isTrainer")]
    public bool IsTrainer { get; set; }

    [JsonIgnore]
    public bool IsTrainerMove => IsTrainer || string.Equals(Type, "Trainer", StringComparison.OrdinalIgnoreCase) || (Id >= 10000 && Id < 20000);
}

public class PassiveItem
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("slot")]
    public int Slot { get; set; }

    [JsonPropertyName("childPassives")]
    public List<ChildPassiveItem> ChildPassives { get; set; } = new();
}

public class ChildPassiveItem
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
}

public class VariationItem
{
    [JsonPropertyName("formId")]
    public int FormId { get; set; }

    [JsonPropertyName("formName")]
    public string FormName { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("actorId")]
    public string ActorId { get; set; } = string.Empty;

    [JsonPropertyName("statMultiplier")]
    public Dictionary<string, double> StatMultiplier { get; set; } = new();

    [JsonPropertyName("passives")]
    public List<PassiveItem> Passives { get; set; } = new();

    [JsonPropertyName("terastalMoveId")]
    public int TerastalMoveId { get; set; }
}

public class GridCellItem
{
    [JsonPropertyName("cellId")]
    public long CellId { get; set; }

    [JsonPropertyName("abilityId")]
    public long AbilityId { get; set; }

    [JsonPropertyName("q")]
    public int Q { get; set; }

    [JsonPropertyName("r")]
    public int R { get; set; }

    [JsonPropertyName("s")]
    public int S { get; set; }

    [JsonPropertyName("energyCost")]
    public int EnergyCost { get; set; }

    [JsonPropertyName("orbCost")]
    public int OrbCost { get; set; }

    [JsonPropertyName("moveLevel")]
    public int MoveLevel { get; set; } = 1;

    [JsonPropertyName("colorKind")]
    public string ColorKind { get; set; } = string.Empty;

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("statBonus")]
    public Dictionary<string, int> StatBonus { get; set; } = new();

    [JsonPropertyName("powerBonus")]
    public Dictionary<string, int> PowerBonus { get; set; } = new();

    [JsonPropertyName("custom")]
    public List<int>? Custom { get; set; }
}