using System.Net.Http.Json;
using BluesLab.Models;

namespace BluesLab.Services;

public class StageService
{
    private readonly HttpClient _http;
    private List<StageLeague>? _leagues;

    public StageService(HttpClient http)
    {
        _http = http;
    }

    public async Task<List<StageLeague>> GetLeaguesAsync()
    {
        if (_leagues == null)
        {
            try
            {
                _leagues = await _http.GetFromJsonAsync<List<StageLeague>>("data/stages_manifest.json") ?? new();
            }
            catch
            {
                _leagues = new();
            }
        }
        return _leagues;
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
        for (int i = 0; i < 3 && i < fight.Opponents.Count; i++)
        {
            var opp = fight.Opponents[i];
            int slot = Math.Clamp(opp.SlotIndex, 0, 2);
            var enemy = state.Enemies[slot];

            enemy.ManualStats["hp"] = opp.Hp;
            enemy.ManualStats["atk"] = opp.Atk;
            enemy.ManualStats["def"] = opp.Def;
            enemy.ManualStats["spa"] = opp.SpA;
            enemy.ManualStats["spd"] = opp.SpD;
            enemy.ManualStats["spe"] = opp.Spe;
            enemy.Weakness = opp.Weakness;

            // Reset stages to 0
            foreach (var k in enemy.Stages.Keys.ToList())
            {
                enemy.Stages[k] = 0;
            }
            foreach (var k in enemy.EnemyTypeRebuffs.Keys.ToList())
            {
                enemy.EnemyTypeRebuffs[k] = 0;
            }
            enemy.StatusCondition = string.Empty;
            enemy.VolatileStatus["confused"] = false;
            enemy.VolatileStatus["trapped"] = false;
            enemy.VolatileStatus["flinching"] = false;
        }
    }
}