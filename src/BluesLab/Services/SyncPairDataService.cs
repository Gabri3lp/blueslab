using System.Net.Http.Json;
using BluesLab.Models;

namespace BluesLab.Services;

public class SyncPairDataService
{
    private readonly HttpClient _http;
    private List<PairManifestItem>? _manifestCache;
    private DamageRulesDocument? _rulesCache;
    private readonly Dictionary<string, SyncPairDetail> _pairDetailsCache = new();

    public SyncPairDataService(HttpClient http)
    {
        _http = http;
    }

    public async Task<List<PairManifestItem>> GetManifestAsync()
    {
        if (_manifestCache != null)
            return _manifestCache;

        try
        {
            _manifestCache = await _http.GetFromJsonAsync<List<PairManifestItem>>("data/pairs_manifest.json") ?? new();
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
            var detail = await _http.GetFromJsonAsync<SyncPairDetail>($"data/pairs/{trainerId}.json");
            if (detail != null)
            {
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
            _rulesCache = await _http.GetFromJsonAsync<DamageRulesDocument>("data/damage_rules.json") ?? new();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error loading damage rules: {ex.Message}");
            _rulesCache = new();
        }

        return _rulesCache;
    }
}