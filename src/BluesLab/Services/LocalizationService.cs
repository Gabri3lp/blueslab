using System.Net.Http.Json;
using System.Text.RegularExpressions;
using BluesLab.Models;
using Microsoft.JSInterop;

namespace BluesLab.Services;

public class LocalizationService
{
    private readonly HttpClient _http;
    private readonly IJSRuntime _js;

    public const string StorageKey = "blueslab_locale";

    public static readonly IReadOnlyDictionary<string, string> SupportedLanguages = new Dictionary<string, string>
    {
        ["es"] = "Español",
        ["en"] = "English",
        ["ja"] = "日本語",
        ["zh"] = "繁體中文",
        ["fr"] = "Français"
    };

    private static readonly Dictionary<string, int> TypeToId = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Normal"] = 1, ["Fire"] = 2, ["Water"] = 3, ["Electric"] = 4, ["Grass"] = 5,
        ["Ice"] = 6, ["Fighting"] = 7, ["Poison"] = 8, ["Ground"] = 9, ["Flying"] = 10,
        ["Psychic"] = 11, ["Bug"] = 12, ["Rock"] = 13, ["Ghost"] = 14, ["Dragon"] = 15,
        ["Dark"] = 16, ["Steel"] = 17, ["Fairy"] = 18, ["Stellar"] = 99
    };

    private static readonly Dictionary<string, int> RoleToId = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Strike (Physical)"] = 0,
        ["Strike (Special)"] = 1,
        ["Support"] = 2,
        ["Tech"] = 3,
        ["Sprint"] = 4,
        ["Field"] = 5,
        ["Multi"] = 6,
        ["Strike"] = 999
    };

    private Dictionary<string, string> _strings = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, Dictionary<string, string>> _cache = new(StringComparer.OrdinalIgnoreCase);

    public string CurrentLanguage { get; private set; } = "es";
    public bool IsLoaded { get; private set; }

    public event Action? OnLanguageChanged;

    public LocalizationService(HttpClient http, IJSRuntime js)
    {
        _http = http;
        _js = js;
    }

    public async Task InitializeAsync()
    {
        if (IsLoaded) return;

        string targetLang = "es";
        try
        {
            var saved = await _js.InvokeAsync<string?>("localStorage.getItem", StorageKey);
            if (!string.IsNullOrWhiteSpace(saved) && SupportedLanguages.ContainsKey(saved))
            {
                targetLang = saved;
            }
        }
        catch
        {
            // Fallback to default if JS interop is unavailable
        }

        await SetLanguageAsync(targetLang, persist: false);
    }

    public async Task SetLanguageAsync(string lang, bool persist = true)
    {
        if (!SupportedLanguages.ContainsKey(lang))
        {
            lang = "es";
        }

        if (lang == CurrentLanguage && IsLoaded)
        {
            return;
        }

        CurrentLanguage = lang;

        if (_cache.TryGetValue(lang, out var cached))
        {
            _strings = cached;
            IsLoaded = true;
        }
        else
        {
            var dict = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

            try
            {
                var common = await _http.GetFromJsonAsync<Dictionary<string, string>>($"locales/common_{lang}.json");
                if (common != null)
                {
                    foreach (var (k, v) in common)
                    {
                        dict[k] = v;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading common_{lang}.json: {ex.Message}");
            }

            try
            {
                var data = await _http.GetFromJsonAsync<Dictionary<string, string>>($"locales/{lang}.json");
                if (data != null)
                {
                    foreach (var (k, v) in data)
                    {
                        dict[k] = v;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading {lang}.json: {ex.Message}");
            }

            _strings = dict;
            _cache[lang] = dict;
            IsLoaded = true;
        }

        if (persist)
        {
            try
            {
                await _js.InvokeVoidAsync("localStorage.setItem", StorageKey, lang);
            }
            catch
            {
                // Ignored if localStorage is disabled
            }
        }

        OnLanguageChanged?.Invoke();
    }

    public string T(string key, string fallback = "")
    {
        if (string.IsNullOrEmpty(key)) return fallback;
        if (_strings.TryGetValue(key, out var val) && !string.IsNullOrWhiteSpace(val))
        {
            return CleanTags(val);
        }
        return string.IsNullOrEmpty(fallback) ? key : fallback;
    }

    public string GetTrainerName(string trainerId, string trainerKey = "", string? trainerBaseId = null, string fallback = "")
    {
        if (!string.IsNullOrEmpty(trainerKey) && _strings.TryGetValue($"trainer_name_{trainerKey}", out var byKey) && !string.IsNullOrWhiteSpace(byKey))
        {
            return CleanTags(byKey);
        }

        if (!string.IsNullOrEmpty(trainerId) && _strings.TryGetValue($"trainer_name_{trainerId}", out var byId) && !string.IsNullOrWhiteSpace(byId))
        {
            return CleanTags(byId);
        }

        if (!string.IsNullOrEmpty(trainerBaseId))
        {
            if (_strings.TryGetValue($"trainer_name_{trainerBaseId}", out var byBase) && !string.IsNullOrWhiteSpace(byBase))
            {
                return CleanTags(byBase);
            }

            if (int.TryParse(trainerBaseId, out var baseNum))
            {
                var chKey = $"trainer_name_ch{baseNum:D4}";
                if (_strings.TryGetValue(chKey, out var byCh) && !string.IsNullOrWhiteSpace(byCh))
                {
                    return CleanTags(byCh);
                }
            }
        }

        return string.IsNullOrEmpty(fallback) ? trainerId : fallback;
    }

    public string GetPokemonName(string monsterBaseId, string pokemonKey = "", string fallback = "")
    {
        if (!string.IsNullOrEmpty(pokemonKey) && _strings.TryGetValue($"pokemon_name_{pokemonKey}", out var byKey) && !string.IsNullOrWhiteSpace(byKey))
        {
            return CleanTags(byKey);
        }

        if (!string.IsNullOrEmpty(monsterBaseId))
        {
            if (_strings.TryGetValue($"pokemon_name_{monsterBaseId}", out var byMb) && !string.IsNullOrWhiteSpace(byMb))
            {
                return CleanTags(byMb);
            }

            // Normalization attempts
            if (monsterBaseId.StartsWith("210") && monsterBaseId.Length >= 8)
            {
                var norm = "200" + monsterBaseId[3..];
                if (_strings.TryGetValue($"pokemon_name_{norm}", out var val) && !string.IsNullOrWhiteSpace(val))
                    return CleanTags(val);
            }

            if (monsterBaseId.Length >= 8)
            {
                var norm = monsterBaseId[..6] + "00";
                if (_strings.TryGetValue($"pokemon_name_{norm}", out var val) && !string.IsNullOrWhiteSpace(val))
                    return CleanTags(val);
            }

            if (monsterBaseId.Length >= 10)
            {
                var norm = "200" + monsterBaseId[3..8];
                if (_strings.TryGetValue($"pokemon_name_{norm}", out var val) && !string.IsNullOrWhiteSpace(val))
                    return CleanTags(val);
            }
        }

        return string.IsNullOrEmpty(fallback) ? monsterBaseId : fallback;
    }

    public string GetDisplayName(PairManifestItem item)
    {
        var tr = GetTrainerName(item.TrainerId, item.TrainerKey, item.TrainerBaseId, item.TrainerName);
        var pk = GetPokemonName(item.MonsterBaseId, item.PokemonKey, item.MonsterName);

        if (string.IsNullOrWhiteSpace(pk)) return tr;
        if (string.IsNullOrWhiteSpace(tr)) return pk;

        return $"{tr} & {pk}";
    }

    public string GetDisplayName(SyncPairDetail detail)
    {
        var tr = GetTrainerName(detail.TrainerId, "", detail.TrainerBaseId, detail.TrainerName);
        var pk = GetPokemonName(detail.MonsterBaseId, "", detail.MonsterName);

        if (string.IsNullOrWhiteSpace(pk)) return tr;
        if (string.IsNullOrWhiteSpace(tr)) return pk;

        return $"{tr} & {pk}";
    }

    public string GetMoveName(int moveId, string fallback = "")
    {
        if (moveId <= 0) return fallback;
        return T($"move_name_{moveId}", fallback);
    }

    public string GetMoveDescription(int moveId, string fallback = "")
    {
        if (moveId <= 0) return fallback;
        return T($"move_desc_{moveId}", fallback);
    }

    public string GetPassiveName(int passiveId, string fallback = "")
    {
        if (passiveId <= 0) return fallback;
        return T($"passive_name_{passiveId}", fallback);
    }

    public string GetPassiveDescription(int passiveId, string fallback = "")
    {
        if (passiveId <= 0) return fallback;
        return T($"passive_desc_{passiveId}", fallback);
    }

    public string GetTileTitle(long abilityId, string fallback = "")
    {
        if (abilityId <= 0) return fallback;
        return T($"tile_name_{abilityId}", fallback);
    }

    public string GetTileDescription(long abilityId, string fallback = "")
    {
        if (abilityId <= 0) return fallback;
        return T($"tile_desc_{abilityId}", fallback);
    }

    public string GetTypeName(string englishType)
    {
        if (string.IsNullOrEmpty(englishType)) return "";
        if (TypeToId.TryGetValue(englishType, out var id))
        {
            var localized = T($"type_{id}");
            if (!string.IsNullOrEmpty(localized) && !localized.Equals($"type_{id}", StringComparison.OrdinalIgnoreCase))
            {
                return localized;
            }
        }
        return englishType;
    }

    public string GetRoleName(string englishRole)
    {
        if (string.IsNullOrEmpty(englishRole)) return "";
        if (RoleToId.TryGetValue(englishRole, out var id))
        {
            var localized = T($"role_{id}");
            if (!string.IsNullOrEmpty(localized) && !localized.Equals($"role_{id}", StringComparison.OrdinalIgnoreCase))
            {
                return localized;
            }
        }
        return englishRole;
    }

    private static string CleanTags(string input)
    {
        if (string.IsNullOrEmpty(input)) return "";
        // Clean out raw formatting tags like [Digit:1digit ], [Name:Type ], etc. if they remain
        var cleaned = Regex.Replace(input, @"\[[^\]]+\]", "").Trim();
        return cleaned;
    }
}
