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
            var json = await _js.InvokeAsync<string>("bluesLabCache.fetchJson", url);
            if (!string.IsNullOrEmpty(json))
            {
                return JsonSerializer.Deserialize<T>(json, _jsonOptions);
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

    public void ApplyFightToEnemies(TeamBattleState state, StageFight fight)
    {
        state.SelectedFightId = fight.FightId;
        state.EnemySyncBuffs = 0;
        state.EnemyPhysicalDamageReduction = false;
        state.EnemySpecialDamageReduction = false;
        state.EnemyDamageField = string.Empty;
        state.ActiveFight = fight;
        state.ActiveTargetIndex = 1;
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