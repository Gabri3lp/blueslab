using System.Text.Json.Serialization;

namespace BluesLab.Models;

public class StageLeague
{
    [JsonPropertyName("leagueId")]
    public string LeagueId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("fights")]
    public List<StageFight> Fights { get; set; } = new();
}

public class StageFight
{
    [JsonPropertyName("fightId")]
    public string FightId { get; set; } = string.Empty;

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("leader")]
    public string Leader { get; set; } = string.Empty;

    [JsonPropertyName("stageType")]
    public string StageType { get; set; } = string.Empty;

    [JsonPropertyName("theme")]
    public string Theme { get; set; } = string.Empty;

    [JsonPropertyName("rules")]
    public List<string> Rules { get; set; } = new();

    [JsonPropertyName("opponents")]
    public List<StageOpponent> Opponents { get; set; } = new();
}

public class StageOpponent
{
    [JsonPropertyName("slotIndex")]
    public int SlotIndex { get; set; } // 0=Left, 1=Center, 2=Right

    [JsonPropertyName("trainerName")]
    public string TrainerName { get; set; } = string.Empty;

    [JsonPropertyName("pokemonName")]
    public string PokemonName { get; set; } = string.Empty;

    [JsonPropertyName("pokemonId")]
    public string PokemonId { get; set; } = string.Empty;

    [JsonPropertyName("iconUrl")]
    public string IconUrl { get; set; } = string.Empty;

    [JsonPropertyName("weakness")]
    public string Weakness { get; set; } = "Normal";

    [JsonPropertyName("hp")]
    public int Hp { get; set; } = 2000;

    [JsonPropertyName("atk")]
    public int Atk { get; set; } = 60;

    [JsonPropertyName("def")]
    public int Def { get; set; } = 100;

    [JsonPropertyName("spa")]
    public int SpA { get; set; } = 60;

    [JsonPropertyName("spd")]
    public int SpD { get; set; } = 100;

    [JsonPropertyName("spe")]
    public int Spe { get; set; } = 300;

    [JsonPropertyName("mitigations")]
    public Dictionary<string, int> Mitigations { get; set; } = new();

    [JsonPropertyName("statusMitigations")]
    public Dictionary<string, int> StatusMitigations { get; set; } = new();

    [JsonPropertyName("passives")]
    public List<StagePassive> Passives { get; set; } = new();
}

public class StagePassive
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("mechanism")]
    public string Mechanism { get; set; } = string.Empty; // "stat_multiplier", "damage_mitigation", "crit_immunity", "field_mitigation"

    [JsonPropertyName("condition")]
    public string Condition { get; set; } = string.Empty; // "no_negative_stat", "no_field_effect", "speed_up", "spdef_up", "fluid_fortification", "rain", "sun", "no_status_condition"

    [JsonPropertyName("multiplier")]
    public double Multiplier { get; set; } = 1.0;
}

public class TowerStageType
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("floors")]
    public List<TowerFloor> Floors { get; set; } = new();
}

public class TowerFloor
{
    [JsonPropertyName("floor")]
    public int Floor { get; set; }

    [JsonPropertyName("floorName")]
    public string FloorName { get; set; } = string.Empty;

    [JsonPropertyName("fight")]
    public StageFight Fight { get; set; } = new();
}