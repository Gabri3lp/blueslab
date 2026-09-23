using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using BluesLab.Models;
using Microsoft.JSInterop;

namespace BluesLab.Services;

public class StageService
{
    private readonly HttpClient _http;
    private readonly IJSRuntime _js;
    private List<StageLeague>? _leagues;

    private static readonly JsonSerializerOptions _jsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true,
        NumberHandling = JsonNumberHandling.AllowReadingFromString | JsonNumberHandling.WriteAsString
    };

    public StageService(HttpClient http, IJSRuntime js)
    {
        _http = http;
        _js = js;
    }

    private async Task<T?> FetchJsonWithCacheAsync<T>(string url)
    {
        try
        {
            var json = await _js.InvokeAsync<string?>("bluesLabCache.fetchJson", url);
            if (!string.IsNullOrEmpty(json))
            {
                try
                {
                    var parsed = JsonSerializer.Deserialize<T>(json, _jsonOptions);
                    if (parsed != null)
                        return parsed;
                }
                catch (JsonException jex)
                {
                    Console.WriteLine($"[StageService] Deserialization error for {url}: {jex.Message}. Evicting from cache.");
                    try { await _js.InvokeVoidAsync("bluesLabCache.delete", url); } catch { }
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[StageService] Cache fetch fallback for {url}: {ex.Message}");
        }

        return await _http.GetFromJsonAsync<T>(url, _jsonOptions);
    }

    private List<TowerStageType>? _towerStages;
    private List<StageFight>? _ultimateStages;

    public async Task<List<StageLeague>> GetLeaguesAsync()
    {
        if (_leagues == null)
        {
            try
            {
                _leagues = await FetchJsonWithCacheAsync<List<StageLeague>>("data/gym_stages.json") ?? new();
            }
            catch
            {
                // Fallback to stages_manifest.json if gym_stages.json not found
                try
                {
                    _leagues = await FetchJsonWithCacheAsync<List<StageLeague>>("data/stages_manifest.json") ?? new();
                }
                catch
                {
                    _leagues = new();
                }
            }
        }
        return _leagues;
    }

    public async Task<List<TowerStageType>> GetTowerStagesAsync()
    {
        if (_towerStages == null)
        {
            try
            {
                _towerStages = await FetchJsonWithCacheAsync<List<TowerStageType>>("data/tower_stages.json") ?? new();
            }
            catch
            {
                _towerStages = new();
            }
        }
        return _towerStages;
    }

    public async Task<List<StageFight>> GetUltimateStagesAsync()
    {
        if (_ultimateStages == null)
        {
            try
            {
                _ultimateStages = await FetchJsonWithCacheAsync<List<StageFight>>("data/ultimate_stages.json") ?? new();
            }
            catch
            {
                _ultimateStages = new();
            }
        }
        return _ultimateStages;
    }

    public async Task<StageFight?> GetFightAsync(string leagueId, string fightId)
    {
        var leagues = await GetLeaguesAsync();
        var league = leagues.FirstOrDefault(l => l.LeagueId == leagueId);
        return league?.Fights.FirstOrDefault(f => f.FightId == fightId);
    }

    public static readonly string[] DamageChallengeTypes =
    [
        "Fire", "Water", "Grass", "Electric", "Ice",
        "Fighting", "Poison", "Ground", "Flying", "Psychic",
        "Bug", "Rock", "Ghost", "Dragon", "Dark",
        "Steel", "Fairy"
    ];

    public StageFight CreateDamageChallengeFight(string type, int targetCount = 3)
    {
        int count = targetCount == 1 ? 1 : 3;
        var fight = new StageFight
        {
            FightId = $"dc_{type.ToLowerInvariant()}_vs{count}",
            Title = $"{type} (vs {count})",
            Leader = type,
            StageType = "damage_challenge",
            Theme = string.Empty,
            Rules = new List<string>()
        };

        var zeroMitigations = new Dictionary<string, int>
        {
            ["def"] = 0,
            ["spd"] = 0,
            ["atk"] = 0,
            ["spa"] = 0,
            ["spe"] = 0
        };

        if (count == 1)
        {
            fight.Opponents.Add(new StageOpponent
            {
                SlotIndex = 1,
                TrainerName = type,
                PokemonName = $"{type} Boss",
                IconUrl = CombatantState.GetTypeIcon(type),
                Weakness = type,
                Hp = 99999999,
                Atk = 100,
                Def = 83,
                SpA = 100,
                SpD = 83,
                Spe = 100,
                Mitigations = new Dictionary<string, int>(zeroMitigations),
                Passives = new List<StagePassive>()
            });
        }
        else
        {
            fight.Opponents.Add(new StageOpponent
            {
                SlotIndex = 0,
                TrainerName = type,
                PokemonName = $"{type} Minion",
                IconUrl = CombatantState.GetTypeIcon(type),
                Weakness = type,
                Hp = 99999999,
                Atk = 100,
                Def = 83,
                SpA = 100,
                SpD = 83,
                Spe = 100,
                Mitigations = new Dictionary<string, int>(zeroMitigations),
                Passives = new List<StagePassive>()
            });

            fight.Opponents.Add(new StageOpponent
            {
                SlotIndex = 1,
                TrainerName = type,
                PokemonName = $"{type} Boss",
                IconUrl = CombatantState.GetTypeIcon(type),
                Weakness = type,
                Hp = 99999999,
                Atk = 100,
                Def = 83,
                SpA = 100,
                SpD = 83,
                Spe = 100,
                Mitigations = new Dictionary<string, int>(zeroMitigations),
                Passives = new List<StagePassive>()
            });

            fight.Opponents.Add(new StageOpponent
            {
                SlotIndex = 2,
                TrainerName = type,
                PokemonName = $"{type} Minion",
                IconUrl = CombatantState.GetTypeIcon(type),
                Weakness = type,
                Hp = 99999999,
                Atk = 100,
                Def = 83,
                SpA = 100,
                SpD = 83,
                Spe = 100,
                Mitigations = new Dictionary<string, int>(zeroMitigations),
                Passives = new List<StagePassive>()
            });
        }

        return fight;
    }

    public void ApplyFightToEnemies(TeamBattleState state, StageFight fight)
    {
        state.SelectedFightId = fight.FightId;
        state.EnemySyncBuffs = 0;
        state.EnemyPhysicalDamageReduction = false;
        state.EnemySpecialDamageReduction = false;
        state.EnemyDamageField = string.Empty;
        state.ActiveFight = fight;
        state.TargetEnemyCount = fight.Opponents.Count;
        state.ActiveTargetIndex = 1;

        if (fight.Opponents.Count == 1)
        {
            state.Enemies[0].CustomTrainerName = string.Empty;
            state.Enemies[0].CustomPokemonName = string.Empty;
            state.Enemies[0].CustomIconUrl = string.Empty;
            state.Enemies[0].ManualStats["hp"] = 0;

            state.Enemies[2].CustomTrainerName = string.Empty;
            state.Enemies[2].CustomPokemonName = string.Empty;
            state.Enemies[2].CustomIconUrl = string.Empty;
            state.Enemies[2].ManualStats["hp"] = 0;
        }

        for (int i = 0; i < 3 && i < fight.Opponents.Count; i++)
        {
            var opp = fight.Opponents[i];
            int slot = Math.Clamp(opp.SlotIndex, 0, 2);
            var enemy = state.Enemies[slot];

            enemy.CustomTrainerName = opp.TrainerName;
            enemy.CustomPokemonName = opp.PokemonName;
            enemy.CustomIconUrl = opp.IconUrl;

            enemy.ManualStats["hp"] = opp.Hp;
            enemy.ManualStats["atk"] = opp.Atk;
            enemy.ManualStats["def"] = opp.Def;
            enemy.ManualStats["spa"] = opp.SpA;
            enemy.ManualStats["spd"] = opp.SpD;
            enemy.ManualStats["spe"] = opp.Spe;
            enemy.Weakness = opp.Weakness;

            // Default enemy debuffs to -6 (crit 0)
            foreach (var k in enemy.Stages.Keys.ToList())
            {
                enemy.Stages[k] = k == "crit" ? 0 : -6;
            }
            foreach (var k in enemy.EnemyTypeRebuffs.Keys.ToList())
            {
                enemy.EnemyTypeRebuffs[k] = 0;
            }

            // Stat Mitigations
            if (opp.Mitigations != null && opp.Mitigations.Count > 0)
            {
                foreach (var (k, v) in opp.Mitigations)
                {
                    enemy.Mitigations[k] = v;
                }
            }
            else
            {
                enemy.Mitigations["def"] = 5;
                enemy.Mitigations["spd"] = 5;
                enemy.Mitigations["atk"] = 5;
                enemy.Mitigations["spa"] = 5;
                enemy.Mitigations["spe"] = 5;
            }

            // Status Mitigations & Passives
            enemy.StatusMitigations = opp.StatusMitigations != null 
                ? new Dictionary<string, int>(opp.StatusMitigations) 
                : new Dictionary<string, int>();

            enemy.StagePassives = opp.Passives != null 
                ? new List<StagePassive>(opp.Passives) 
                : new List<StagePassive>();

            enemy.StatusCondition = string.Empty;
            enemy.VolatileStatus["confused"] = false;
            enemy.VolatileStatus["trapped"] = false;
            enemy.VolatileStatus["flinching"] = false;
        }
    }
}