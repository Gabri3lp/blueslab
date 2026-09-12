using System.IO.Compression;
using System.Text.Json;
using BluesLab.Models;
using Microsoft.JSInterop;

namespace BluesLab.Services;

public class TeamConfigurationService
{
    private readonly IJSRuntime _js;
    private readonly SyncPairDataService _dataService;
    private readonly StageService _stageService;
    public const string StorageKey = "blueslab_saved_teams";

    public TeamConfigurationService(IJSRuntime js, SyncPairDataService dataService, StageService stageService)
    {
        _js = js;
        _dataService = dataService;
        _stageService = stageService;
    }

    public TeamConfigDto? DeserializeToken(string token) => ImportFromToken(token);

    public async Task ApplyConfigAsync(TeamBattleState targetState, TeamConfigDto dto)
    {
        await ApplyConfigToStateAsync(dto, targetState, _dataService, _stageService);
    }

    public TeamConfigDto ExportToDto(TeamBattleState state, string name = "", string? desc = null)
    {
        var dto = new TeamConfigDto
        {
            Name = string.IsNullOrWhiteSpace(name) ? "My Team" : name.Trim(),
            Description = desc,
            SelectedLeagueId = state.SelectedLeagueId,
            SelectedFightId = state.SelectedFightId,
            AllySyncBuffs = state.AllySyncBuffs,
            AlliedPhysicalDamageReduction = state.AlliedPhysicalDamageReduction,
            AlliedSpecialDamageReduction = state.AlliedSpecialDamageReduction,
            ActiveAttackerIndex = state.ActiveAttackerIndex,
            ActiveTargetIndex = state.ActiveTargetIndex,
            EnemySyncBuffs = state.EnemySyncBuffs,
            EnemyPhysicalDamageReduction = state.EnemyPhysicalDamageReduction,
            EnemySpecialDamageReduction = state.EnemySpecialDamageReduction,
            EnemyDamageField = state.EnemyDamageField
        };

        // Field State
        dto.Field = new FieldStateDto
        {
            Weather = state.Field.Weather,
            WeatherEx = state.Field.WeatherEx,
            Terrain = state.Field.Terrain,
            TerrainEx = state.Field.TerrainEx,
            Zone = state.Field.Zone,
            ZoneEx = state.Field.ZoneEx
        };

        // Active Circles
        foreach (var (reg, circles) in state.TeamCircles)
        {
            var activeTypes = circles.Where(kv => kv.Value).Select(kv => kv.Key).ToList();
            if (activeTypes.Count > 0)
            {
                dto.ActiveCircles[reg] = activeTypes;
            }
        }

        // Team Gear
        dto.TeamGearPreset = state.TeamGearPreset;
        dto.TeamGear = new Dictionary<string, int>(state.TeamGear);
        dto.TeamGearMoveBoost = state.TeamGearMoveBoost;
        dto.TeamGearSyncBoost = state.TeamGearSyncBoost;

        // Allies (3 slots)
        for (int i = 0; i < 3 && i < state.Allies.Count; i++)
        {
            var ally = state.Allies[i];
            var allyDto = new AllySlotDto
            {
                TrainerId = ally.Pair?.TrainerId,
                FormIndex = ally.FormIndex,
                MoveLevel = ally.MoveLevel,
                SuperAwakeningLevel = ally.SuperAwakeningLevel,
                HasExRole = ally.HasExRole,
                StarLevel = ally.StarLevel,
                CharLevel = ally.CharLevel,
                LuckySkillName = ally.LuckySkillName,
                PhysicalBoostNext = ally.PhysicalBoostNext,
                SpecialBoostNext = ally.SpecialBoostNext,
                SyncMoveBoostNext = ally.SyncMoveBoostNext,
                IsCriticalMove = ally.IsCriticalMove,
                SuperEffectiveNext = ally.SuperEffectiveNext,
                ThemeSkillsActive = ally.ThemeSkillsActive,
                GearPreset = ally.GearPreset,
                Gear = new Dictionary<string, int>(ally.Gear),
                GearMoveBoost = ally.GearMoveBoost,
                GearSyncBoost = ally.GearSyncBoost,
                Stages = new Dictionary<string, int>(ally.Stages),
                ActiveGridCells = i < state.AllyActiveGrids.Count ? state.AllyActiveGrids[i].ToList() : new List<long>()
            };
            dto.Allies.Add(allyDto);
        }

        // Enemies (3 slots)
        for (int i = 0; i < 3 && i < state.Enemies.Count; i++)
        {
            var opp = state.Enemies[i];
            var oppDto = new EnemySlotDto
            {
                CustomTrainerName = opp.CustomTrainerName,
                CustomPokemonName = opp.CustomPokemonName,
                CustomIconUrl = opp.CustomIconUrl,
                Weakness = opp.Weakness,
                StatusCondition = opp.StatusCondition,
                PhysicalBreak = opp.PhysicalBreak,
                SpecialBreak = opp.SpecialBreak,
                ManualStats = new Dictionary<string, int>(opp.ManualStats),
                Stages = new Dictionary<string, int>(opp.Stages),
                Mitigations = new Dictionary<string, int>(opp.Mitigations),
                VolatileStatus = new Dictionary<string, bool>(opp.VolatileStatus),
                Rebuffs = opp.EnemyTypeRebuffs.Where(kv => kv.Value != 0).ToDictionary(kv => kv.Key, kv => kv.Value)
            };
            dto.Enemies.Add(oppDto);
        }

        return dto;
    }

    public string ExportToToken(TeamBattleState state, string name = "")
    {
        var dto = ExportToDto(state, name);
        return SerializeAndCompress(dto);
    }

    public string SerializeAndCompress(TeamConfigDto dto)
    {
        var jsonBytes = JsonSerializer.SerializeToUtf8Bytes(dto);
        using var outputStream = new MemoryStream();
        using (var gzip = new GZipStream(outputStream, CompressionLevel.Optimal))
        {
            gzip.Write(jsonBytes, 0, jsonBytes.Length);
        }
        var compressedBytes = outputStream.ToArray();
        return Convert.ToBase64String(compressedBytes)
            .Replace("+", "-")
            .Replace("/", "_")
            .TrimEnd('=');
    }

    public TeamConfigDto? ImportFromToken(string token)
    {
        if (string.IsNullOrWhiteSpace(token)) return null;

        try
        {
            string b64 = token.Trim().Replace("-", "+").Replace("_", "/");
            switch (b64.Length % 4)
            {
                case 2: b64 += "=="; break;
                case 3: b64 += "="; break;
            }

            var compressedBytes = Convert.FromBase64String(b64);
            using var inputStream = new MemoryStream(compressedBytes);
            using var gzip = new GZipStream(inputStream, CompressionMode.Decompress);
            using var outputStream = new MemoryStream();
            gzip.CopyTo(outputStream);
            var jsonBytes = outputStream.ToArray();
            return JsonSerializer.Deserialize<TeamConfigDto>(jsonBytes);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error decoding team token: {ex.Message}");
            return null;
        }
    }

    public async Task ApplyConfigToStateAsync(
        TeamConfigDto dto,
        TeamBattleState targetState,
        SyncPairDataService dataService,
        StageService stageService)
    {
        if (dto == null || targetState == null) return;

        // 1. Stage selection
        if (!string.IsNullOrEmpty(dto.SelectedLeagueId))
        {
            targetState.SelectedLeagueId = dto.SelectedLeagueId;
        }
        if (!string.IsNullOrEmpty(dto.SelectedFightId))
        {
            targetState.SelectedFightId = dto.SelectedFightId;
        }

        var leagues = await stageService.GetLeaguesAsync();
        var league = leagues.FirstOrDefault(l => l.LeagueId == targetState.SelectedLeagueId);
        var fight = league?.Fights.FirstOrDefault(f => f.FightId == targetState.SelectedFightId);
        if (fight != null)
        {
            stageService.ApplyFightToEnemies(targetState, fight);
        }

        // 2. Field conditions
        if (dto.Field != null)
        {
            targetState.Field.Weather = dto.Field.Weather ?? string.Empty;
            targetState.Field.WeatherEx = dto.Field.WeatherEx;
            targetState.Field.Terrain = dto.Field.Terrain ?? string.Empty;
            targetState.Field.TerrainEx = dto.Field.TerrainEx;
            targetState.Field.Zone = dto.Field.Zone ?? string.Empty;
            targetState.Field.ZoneEx = dto.Field.ZoneEx;
        }

        // 3. Ally team buffs & screens
        targetState.AllySyncBuffs = dto.AllySyncBuffs;
        targetState.AlliedPhysicalDamageReduction = dto.AlliedPhysicalDamageReduction;
        targetState.AlliedSpecialDamageReduction = dto.AlliedSpecialDamageReduction;

        // 4. Team Circles
        targetState.ClearAllCircles();
        if (dto.ActiveCircles != null)
        {
            foreach (var (reg, types) in dto.ActiveCircles)
            {
                if (!targetState.TeamCircles.ContainsKey(reg))
                {
                    targetState.TeamCircles[reg] = new Dictionary<string, bool>
                    {
                        ["physical"] = false,
                        ["special"] = false,
                        ["defensive"] = false
                    };
                }
                foreach (var t in types)
                {
                    targetState.TeamCircles[reg][t] = true;
                }
            }
        }

        // 4.5. Team Gear
        targetState.TeamGearPreset = string.IsNullOrEmpty(dto.TeamGearPreset) ? "4star" : dto.TeamGearPreset;
        bool isPresetValid = targetState.TeamGearPreset != "none" && targetState.TeamGearPreset != "custom";
        bool teamGearAllZero = dto.TeamGear == null || dto.TeamGear.Count == 0 || dto.TeamGear.Values.All(v => v == 0);

        if (isPresetValid && teamGearAllZero)
        {
            targetState.ApplyTeamGearPreset(targetState.TeamGearPreset);
        }
        else if (dto.TeamGear != null && dto.TeamGear.Count > 0)
        {
            foreach (var s in CombatantState.StatLabels)
            {
                targetState.TeamGear[s] = dto.TeamGear.GetValueOrDefault(s, 0);
            }
        }
        else
        {
            targetState.ApplyTeamGearPreset(targetState.TeamGearPreset);
        }
        targetState.TeamGearMoveBoost = dto.TeamGearMoveBoost;
        targetState.TeamGearSyncBoost = dto.TeamGearSyncBoost;
        targetState.SyncTeamGearToAllies();

        // 5. Allies
        if (dto.Allies != null)
        {
            for (int i = 0; i < 3; i++)
            {
                if (i < dto.Allies.Count && !string.IsNullOrEmpty(dto.Allies[i].TrainerId))
                {
                    var aDto = dto.Allies[i];
                    var detail = await dataService.GetPairDetailAsync(aDto.TrainerId!);
                    if (detail != null)
                    {
                        var ally = targetState.Allies[i];
                        ally.Pair = detail;
                        ally.FormIndex = aDto.FormIndex;
                        ally.MoveLevel = aDto.MoveLevel;
                        ally.SuperAwakeningLevel = aDto.SuperAwakeningLevel;
                        ally.HasExRole = aDto.HasExRole;
                        ally.StarLevel = string.IsNullOrEmpty(aDto.StarLevel) ? (detail.HasEx ? "5★ EX" : $"{detail.Rarity}★") : aDto.StarLevel;
                        ally.CharLevel = string.IsNullOrEmpty(aDto.CharLevel) ? "180" : aDto.CharLevel;
                        ally.LuckySkillName = aDto.LuckySkillName;
                        ally.PhysicalBoostNext = aDto.PhysicalBoostNext;
                        ally.SpecialBoostNext = aDto.SpecialBoostNext;
                        ally.SyncMoveBoostNext = aDto.SyncMoveBoostNext;
                        ally.IsCriticalMove = aDto.IsCriticalMove;
                        ally.SuperEffectiveNext = aDto.SuperEffectiveNext;
                        ally.ThemeSkillsActive = aDto.ThemeSkillsActive;

                        // Ally Gear
                        if (!string.IsNullOrEmpty(aDto.GearPreset))
                        {
                            ally.GearPreset = aDto.GearPreset;
                        }
                        bool isAllyPresetValid = ally.GearPreset != "none" && ally.GearPreset != "custom";
                        bool allyGearAllZero = aDto.Gear == null || aDto.Gear.Count == 0 || aDto.Gear.Values.All(v => v == 0);

                        if (isAllyPresetValid && allyGearAllZero)
                        {
                            foreach (var s in CombatantState.StatLabels)
                            {
                                ally.Gear[s] = targetState.TeamGear.GetValueOrDefault(s, 0);
                            }
                        }
                        else if (aDto.Gear != null && aDto.Gear.Count > 0)
                        {
                            foreach (var s in CombatantState.StatLabels)
                            {
                                ally.Gear[s] = aDto.Gear.GetValueOrDefault(s, 0);
                            }
                        }
                        else
                        {
                            foreach (var s in CombatantState.StatLabels)
                            {
                                ally.Gear[s] = targetState.TeamGear.GetValueOrDefault(s, 0);
                            }
                        }
                        ally.GearMoveBoost = aDto.GearMoveBoost;
                        ally.GearSyncBoost = aDto.GearSyncBoost;

                        if (aDto.Stages != null && aDto.Stages.Count > 0)
                        {
                            foreach (var (k, v) in aDto.Stages)
                            {
                                ally.Stages[k] = v;
                            }
                        }

                        targetState.AllyActiveGrids[i].Clear();
                        if (aDto.ActiveGridCells != null)
                        {
                            foreach (var cellId in aDto.ActiveGridCells)
                            {
                                targetState.AllyActiveGrids[i].Add(cellId);
                            }
                        }
                    }
                }
                else
                {
                    targetState.Allies[i] = new CombatantState();
                    targetState.AllyActiveGrids[i].Clear();
                }
            }
        }

        // 6. Active Indices
        targetState.ActiveAttackerIndex = Math.Clamp(dto.ActiveAttackerIndex, 0, 2);
        targetState.ActiveTargetIndex = Math.Clamp(dto.ActiveTargetIndex, 0, 2);

        // 7. Enemy side effects
        targetState.EnemySyncBuffs = dto.EnemySyncBuffs;
        targetState.EnemyPhysicalDamageReduction = dto.EnemyPhysicalDamageReduction;
        targetState.EnemySpecialDamageReduction = dto.EnemySpecialDamageReduction;
        targetState.EnemyDamageField = dto.EnemyDamageField ?? string.Empty;

        // 8. Enemy targets
        if (dto.Enemies != null)
        {
            for (int i = 0; i < 3 && i < dto.Enemies.Count && i < targetState.Enemies.Count; i++)
            {
                var eDto = dto.Enemies[i];
                var opp = targetState.Enemies[i];

                if (!string.IsNullOrEmpty(eDto.CustomTrainerName)) opp.CustomTrainerName = eDto.CustomTrainerName;
                if (!string.IsNullOrEmpty(eDto.CustomPokemonName)) opp.CustomPokemonName = eDto.CustomPokemonName;
                if (!string.IsNullOrEmpty(eDto.CustomIconUrl)) opp.CustomIconUrl = eDto.CustomIconUrl;
                if (!string.IsNullOrEmpty(eDto.Weakness)) opp.Weakness = eDto.Weakness;

                if (eDto.ManualStats != null && eDto.ManualStats.Count > 0)
                {
                    foreach (var (k, v) in eDto.ManualStats) opp.ManualStats[k] = v;
                }
                if (eDto.Stages != null && eDto.Stages.Count > 0)
                {
                    foreach (var (k, v) in eDto.Stages) opp.Stages[k] = v;
                }
                if (eDto.Mitigations != null && eDto.Mitigations.Count > 0)
                {
                    foreach (var (k, v) in eDto.Mitigations) opp.Mitigations[k] = v;
                }
                opp.StatusCondition = eDto.StatusCondition ?? string.Empty;
                if (eDto.VolatileStatus != null)
                {
                    foreach (var (k, v) in eDto.VolatileStatus) opp.VolatileStatus[k] = v;
                }
                opp.PhysicalBreak = eDto.PhysicalBreak;
                opp.SpecialBreak = eDto.SpecialBreak;

                if (eDto.Rebuffs != null)
                {
                    foreach (var t in CombatantState.AllTypes)
                    {
                        opp.EnemyTypeRebuffs[t] = eDto.Rebuffs.GetValueOrDefault(t, 0);
                    }
                }
            }
        }

        targetState.UpdateCircleAllyCounts();
    }

    public string GenerateShareUrl(string baseUri, TeamBattleState state, string name = "")
    {
        string token = ExportToToken(state, name);
        var uri = new Uri(baseUri);
        var basePart = $"{uri.Scheme}://{uri.Authority}{uri.AbsolutePath}";
        return $"{basePart}?team={token}";
    }

    // Local Storage Management
    public async Task<List<TeamSavedItemDto>> GetSavedTeamsAsync()
    {
        try
        {
            var json = await _js.InvokeAsync<string?>("localStorage.getItem", StorageKey);
            if (string.IsNullOrWhiteSpace(json)) return new List<TeamSavedItemDto>();

            var list = JsonSerializer.Deserialize<List<TeamSavedItemDto>>(json);
            return list?.OrderByDescending(x => x.CreatedAt).ToList() ?? new List<TeamSavedItemDto>();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to load saved teams from localStorage: {ex.Message}");
            return new List<TeamSavedItemDto>();
        }
    }

    public async Task SaveTeamAsync(string name, TeamBattleState state, string? desc = null, string? overwriteId = null)
    {
        var savedList = await GetSavedTeamsAsync();
        var dto = ExportToDto(state, name, desc);

        var item = new TeamSavedItemDto
        {
            Id = !string.IsNullOrEmpty(overwriteId) ? overwriteId : Guid.NewGuid().ToString("N")[..8],
            Name = string.IsNullOrWhiteSpace(name) ? "My Team" : name.Trim(),
            CreatedAt = DateTime.UtcNow,
            Description = desc,
            StageTitle = state.ActiveFight?.Title ?? "Pasio Gym Battle",
            Config = dto
        };

        for (int i = 0; i < 3 && i < state.Allies.Count; i++)
        {
            var ally = state.Allies[i];
            if (ally.Pair != null)
            {
                item.PairTrainerIds.Add(ally.Pair.TrainerId);
                item.PairDisplayNames.Add(ally.Pair.DisplayName);
                item.PairIconUrls.Add(ally.Pair.IconUrl);
            }
        }

        if (!string.IsNullOrEmpty(overwriteId))
        {
            int idx = savedList.FindIndex(x => x.Id == overwriteId);
            if (idx >= 0)
            {
                savedList[idx] = item;
            }
            else
            {
                savedList.Insert(0, item);
            }
        }
        else
        {
            savedList.Insert(0, item);
        }

        var json = JsonSerializer.Serialize(savedList);
        await _js.InvokeVoidAsync("localStorage.setItem", StorageKey, json);
    }

    public async Task DeleteTeamAsync(string id)
    {
        var savedList = await GetSavedTeamsAsync();
        savedList.RemoveAll(x => x.Id == id);
        var json = JsonSerializer.Serialize(savedList);
        await _js.InvokeVoidAsync("localStorage.setItem", StorageKey, json);
    }

    // Compare Current Battle State with another TeamConfigDto
    public async Task<TeamComparisonSummary> CompareTeamsAsync(
        TeamBattleState currentBattle,
        TeamConfigDto targetConfig,
        DamageCalculatorService calcService,
        SyncPairDataService dataService,
        StageService stageService,
        DamageRulesDocument rules,
        LocalizationService loc)
    {
        var summary = new TeamComparisonSummary
        {
            ConfigAName = "Current Team",
            ConfigBName = string.IsNullOrEmpty(targetConfig.Name) ? "Target Team" : targetConfig.Name
        };

        // Create temporary battle state for Config B
        var stateB = new TeamBattleState();
        await ApplyConfigToStateAsync(targetConfig, stateB, dataService, stageService);

        var pairA = currentBattle.ActiveAttacker.Pair;
        var pairB = stateB.ActiveAttacker.Pair;

        if (pairA == null && pairB == null) return summary;

        // Use active attacker in A or B
        var attackerPair = pairA ?? pairB!;
        var battleForMoves = pairA != null ? currentBattle : stateB;
        var moves = attackerPair.Moves;

        foreach (var move in moves)
        {
            var resA = pairA != null ? calcService.CalculateTeamDamage(move, currentBattle, rules) : null;
            var resB = pairB != null ? calcService.CalculateTeamDamage(move, stateB, rules) : null;

            double dmgA = resA?.ActiveTargetDamage.AvgDamage ?? 0;
            double hpA = resA?.ActiveTargetDamage.AvgHpPercent ?? 0;
            double dmgB = resB?.ActiveTargetDamage.AvgDamage ?? 0;
            double hpB = resB?.ActiveTargetDamage.AvgHpPercent ?? 0;

            summary.MoveResults.Add(new TeamComparisonMoveResult
            {
                MoveName = loc.GetMoveName(move.Id, move.Name),
                MoveType = loc.GetTypeName(move.Type),
                Category = move.Category,
                IsSync = move.IsSync,
                IsMax = false,
                DamageA = dmgA,
                HpPercentA = hpA,
                DamageB = dmgB,
                HpPercentB = hpB
            });
        }

        return summary;
    }
}
