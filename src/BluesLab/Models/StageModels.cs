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
}