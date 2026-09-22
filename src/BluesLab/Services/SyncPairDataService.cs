using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using BluesLab.Models;
using Microsoft.JSInterop;

namespace BluesLab.Services;

public class SyncPairDataService
{
    private readonly HttpClient _http;
    private readonly IJSRuntime _js;
    private List<PairManifestItem>? _manifestCache;
    private DamageRulesDocument? _rulesCache;
    private ThemesDatabaseDocument? _themesDbCache;
    private readonly Dictionary<string, SyncPairDetail> _pairDetailsCache = new();

    private static readonly JsonSerializerOptions _jsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true,
        NumberHandling = JsonNumberHandling.AllowReadingFromString | JsonNumberHandling.WriteAsString
    };

    public SyncPairDataService(HttpClient http, IJSRuntime js)
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
            Console.WriteLine($"[SyncPairDataService] Cache fetch fallback for {url}: {ex.Message}");
        }

        return await _http.GetFromJsonAsync<T>(url, _jsonOptions);
    }

    public async Task<ThemesDatabaseDocument> GetThemesDatabaseAsync()
    {
        if (_themesDbCache != null)
            return _themesDbCache;

        try
        {
            _themesDbCache = await FetchJsonWithCacheAsync<ThemesDatabaseDocument>("data/themes_database.json") ?? new();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading themes database: {ex.Message}");
            _themesDbCache = new();
        }

        return _themesDbCache;
    }

    public async Task<List<PairManifestItem>> GetManifestAsync()
    {
        if (_manifestCache != null)
            return _manifestCache;

        try
        {
            _manifestCache = await FetchJsonWithCacheAsync<List<PairManifestItem>>("data/pairs_manifest.json") ?? new();
            var themesDb = await GetThemesDatabaseAsync();
            if (themesDb.PairThemes.Count > 0)
            {
                foreach (var item in _manifestCache)
                {
                    if (themesDb.PairThemes.TryGetValue(item.TrainerId, out var ths))
                    {
                        item.Themes = ths;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading pairs manifest: {ex.Message}");
            _manifestCache = new();
        }

        return _manifestCache;
    }

    public async Task<SyncPairDetail?> GetPairDetailAsync(string trainerId)
    {
        if (_pairDetailsCache.TryGetValue(trainerId, out var cached))
            return cached;

        try
        {
            var detail = await FetchJsonWithCacheAsync<SyncPairDetail>($"data/pairs/{trainerId}.json");
            if (detail != null)
            {
                var themesDb = await GetThemesDatabaseAsync();
                if (themesDb.PairThemes.TryGetValue(trainerId, out var ths))
                {
                    detail.Themes = ths;
                }
                _pairDetailsCache[trainerId] = detail;
                return detail;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading pair detail for {trainerId}: {ex.Message}");
        }

        return null;
    }

    public async Task<DamageRulesDocument> GetDamageRulesAsync()
    {
        if (_rulesCache != null)
            return _rulesCache;

        try
        {
            _rulesCache = await FetchJsonWithCacheAsync<DamageRulesDocument>("data/damage_rules.json") ?? new();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading damage rules: {ex.Message}");
            _rulesCache = new();
        }

        return _rulesCache;
    }
}