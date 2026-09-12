using System.Text.RegularExpressions;
using BluesLab.Models;

namespace BluesLab.Services;

public readonly struct FormattedTileLine
{
    public string Text { get; }
    public double YOffset { get; }

    public FormattedTileLine(string text, double yOffset)
    {
        Text = text;
        YOffset = yOffset;
    }
}

public class FormattedTileLabel
{
    public List<FormattedTileLine> Lines { get; }
    public double FontSize { get; }

    public FormattedTileLabel(List<FormattedTileLine> lines, double fontSize)
    {
        Lines = lines;
        FontSize = fontSize;
    }
}

public static class GridTileFormatter
{
    private static readonly Regex EsStatRegex = new(@"^(PS|Ataque|Defensa|At\.\s*Esp\.|Def\.\s*Esp\.|Velocidad)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex EnStatRegex = new(@"^(HP|Attack|Defense|Sp\.\s*Atk|Sp\.\s*Def|Speed)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex NumberOnlyRegex = new(@"\+\s*(\d+)", RegexOptions.Compiled);

    private static readonly (string Pattern, string Replacement)[] GlobalReplacements =
    [
        (@"Move Gauge Refresh\s*\+?(\d+)", "MGR$1"),
        (@"Movimiento Llenabarras\s*\+?(\d+)", "MGR$1"),
        (@"Llenabarras\s*\+?(\d+)", "MGR$1"),
        (@"MP Refresh\s*\+?(\d+)", "MPR$1"),
        (@"Recupera PM\s*\+?(\d+)", "MPR$1"),
        (@"Movimiento Recupera PM\s*\+?(\d+)", "MPR$1"),
        (@"Restore B-Move MP\s*(\d+)", "Rest. B-MP$1"),
        (@"Restore MP\s*(\d+)", "Rest. MP$1"),
        (@"Free Move Next\s*(\d+)", "FMN $1"),
        (@"Free Move Next", "FMN"),
        (@"Physical & Special Boost", "Phys & Spec"),
        (@"Physical Boost", "Phys Boost"),
        (@"Special Boost", "Spec Boost"),
        (@"Move on Ally:", "Ally:"),
        (@"Movimiento Aliado:", "Aliado:"),
        (@"HP Recovery \(M\)\s*(\d+)", "HP Recov $1"),
        (@"HP Recovery\s*(\d+)", "HP Recov $1"),
        (@"Curación Media\s*\+?(\d+)", "Curac. $1"),
        (@"Accuracy\s*\+\s*(\d+)", "Acc +$1"),
        (@"Precisión\s*\+\s*(\d+)", "Prec +$1"),
        (@"Power\s*\+\s*(\d+)", "Power +$1"),
        (@"Potencia\s*\+\s*(\d+)", "Potencia +$1"),
        (@"Sync CD ↓\s*(\d+)", "Sync CD ↓$1"),
        (@"Attack Move DR\s*(\d+)", "Atk Move DR$1"),
        (@"Inmunidad Golpes Críticos", "Vigilancia"),
        (@"Inmunidad Reducción Defensa", "Inm. Def ↓"),
        (@"Inmunidad Reducción Ataque", "Inm. Atq ↓"),
        (@"Inmunidad Reducción Velocidad", "Inm. Vel ↓"),
        (@"Inmunidad Reducción Def\. Esp\.", "Inm. DefEsp↓"),
        (@"Inmunidad Reducción At\. Esp\.", "Inm. AtqEsp↓"),
        (@"Inmunidad Retroceso", "Inm. Retro."),
        (@"Curación Problemas Estado", "Cura Estado"),
        (@"Inmunidad Problemas Estado", "Inm. Estado"),
        (@"Primeros Auxilios\s*(\d+)", "1.os Aux $1"),
        (@"Natural Remedy", "Nat. Remedy"),
        (@"Quick Cure", "Quick Cure"),
        (@"Sand Shelter", "Sand Shelter"),
        (@"Healthy Healing", "Healthy Heal"),
        (@"Bob and Weave", "Bob & Weave")
    ];

    private static readonly Dictionary<(long AbilityId, string Lang), FormattedTileLabel> LabelCache = new();

    public static FormattedTileLabel FormatTile(string? rawTitle, long abilityId, string language)
    {
        language ??= "en";
        if (abilityId > 0 && LabelCache.TryGetValue((abilityId, language), out var cached))
        {
            return cached;
        }

        var label = FormatTileInternal(rawTitle, language);
        if (abilityId > 0)
        {
            LabelCache[(abilityId, language)] = label;
        }
        return label;
    }

    private static FormattedTileLabel FormatTileInternal(string? rawTitle, string language)
    {
        if (string.IsNullOrWhiteSpace(rawTitle))
        {
            return new FormattedTileLabel(new List<FormattedTileLine>(), 8.0);
        }

        // Clean formatting tags and split camelCase words (e.g. StormIce -> Storm Ice, AllIncomplete -> All Incomplete)
        var t = Regex.Replace(rawTitle, @"([a-z\u00e0-\u00ff])([A-Z\u00c0-\u00df])", "$1 $2");
        t = t.Replace("\r", "").Replace("\n", " ").Trim();
        t = Regex.Replace(t, @"\[[^\]]+\]", "").Trim();
        while (t.Contains("  ")) t = t.Replace("  ", " ");

        // Apply global abbreviations
        foreach (var (pat, repl) in GlobalReplacements)
        {
            t = Regex.Replace(t, pat, repl, RegexOptions.IgnoreCase);
        }

        // 1. Stats (Keep clean, recognizable names on 1 single centered line)
        var mEs = EsStatRegex.Match(t);
        if (mEs.Success)
        {
            var stat = mEs.Groups[1].Value;
            var val = mEs.Groups[2].Value;
            var cleanStat = stat.ToLowerInvariant() switch
            {
                "ps" => "PS",
                "ataque" => "Ataque",
                "defensa" => "Defensa",
                "at. esp." or "at.esp." => "At. Esp.",
                "def. esp." or "def.esp." => "Def. Esp.",
                "velocidad" => "Velocidad",
                _ => stat
            };
            return BuildLabel([$"{cleanStat} +{val}"]);
        }

        var mEn = EnStatRegex.Match(t);
        if (mEn.Success)
        {
            var stat = mEn.Groups[1].Value;
            var val = mEn.Groups[2].Value;
            var cleanStat = stat.ToLowerInvariant() switch
            {
                "hp" => "HP",
                "attack" => "Attack",
                "defense" => "Defense",
                "sp. atk" or "sp.atk" => "Sp. Atk",
                "sp. def" or "sp.def" => "Sp. Def",
                "speed" => "Speed",
                _ => stat
            };
            return BuildLabel([$"{cleanStat} +{val}"]);
        }

        // 2. Sync Moves / Dynamax Moves
        if (t.Contains("Sync Move", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Movimiento Compi", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Impact: Power", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Impacto: Potencia", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Beam: Power", StringComparison.OrdinalIgnoreCase))
        {
            var mNum = NumberOnlyRegex.Match(t);
            var val = mNum.Success ? mNum.Groups[1].Value : "";
            var isEs = string.Equals(language, "es", StringComparison.OrdinalIgnoreCase);
            var syncHeader = isEs ? "Mov. Compi:" : "Sync Move:";
            var pwrText = !string.IsNullOrEmpty(val) ? (isEs ? $"Potencia +{val}" : $"Power +{val}") : (isEs ? "Potencia" : "Power");
            return BuildLabel([syncHeader, pwrText]);
        }

        if (t.Contains("Max Move", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Movimiento Dynamax", StringComparison.OrdinalIgnoreCase))
        {
            var mNum = NumberOnlyRegex.Match(t);
            var val = mNum.Success ? mNum.Groups[1].Value : "";
            var isEs = string.Equals(language, "es", StringComparison.OrdinalIgnoreCase);
            var maxHeader = isEs ? "Mov. Dyna:" : "Max Move:";
            var pwrText = !string.IsNullOrEmpty(val) ? (isEs ? $"Potencia +{val}" : $"Power +{val}") : (isEs ? "Potencia" : "Power");
            return BuildLabel([maxHeader, pwrText]);
        }

        // 3. Colon splitting
        if (t.Contains(": "))
        {
            var parts = t.Split(new[] { ": " }, 2, StringSplitOptions.RemoveEmptyEntries);
            var prefix = parts[0].Trim();
            var body = parts[1].Trim();

            // Case A: Prefix fits in Line 1 (<= 12 chars) e.g. "1st S-Move", "Ice Zone", "Ice Wish", "Normal-Z"
            if (prefix.Length + 1 <= 12)
            {
                var l1 = prefix.EndsWith(":") ? prefix : prefix + ":";
                if (body.Length <= 12)
                {
                    return BuildLabel([l1, body]);
                }

                var bodyWords = body.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                if (bodyWords.Length == 2)
                {
                    return BuildLabel([l1, Trunc(bodyWords[0], 11), Trunc(bodyWords[1], 11)]);
                }
                if (bodyWords.Length >= 3)
                {
                    if (bodyWords[0].Length + bodyWords[1].Length + 1 <= 12)
                    {
                        var l2 = bodyWords[0] + " " + bodyWords[1];
                        var l3 = string.Join(" ", bodyWords.Skip(2));
                        return BuildLabel([l1, Trunc(l2, 11), Trunc(l3, 11)]);
                    }
                    else
                    {
                        var l2 = bodyWords[0];
                        var l3 = string.Join(" ", bodyWords.Skip(1));
                        return BuildLabel([l1, Trunc(l2, 11), Trunc(l3, 11)]);
                    }
                }
                return BuildLabel([l1, Trunc(body.Substring(0, Math.Min(11, body.Length)), 11), Trunc(body.Substring(Math.Min(11, body.Length)), 11)]);
            }
            else
            {
                // Case B: Prefix is longer (e.g. "Frigid Storm Ice Punch", "We're All Incomplete", "Tera Starstorm")
                var pWords = prefix.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                if (pWords.Length == 2)
                {
                    var l1 = pWords[0];
                    var l2 = pWords[1].EndsWith(":") ? pWords[1] : pWords[1] + ":";
                    return BuildLabel([Trunc(l1, 11), Trunc(l2, 11), Trunc(body, 11)]);
                }
                else if (pWords.Length >= 3)
                {
                    string l1, l2;
                    if (pWords[0].Length + pWords[1].Length + 1 <= 12)
                    {
                        l1 = pWords[0] + " " + pWords[1];
                        l2 = string.Join(" ", pWords.Skip(2));
                    }
                    else
                    {
                        l1 = pWords[0];
                        l2 = string.Join(" ", pWords.Skip(1));
                    }
                    if (!l2.EndsWith(":")) l2 += ":";

                    if (body.Length <= 11)
                    {
                        return BuildLabel([Trunc(l1, 11), Trunc(l2, 11), body]);
                    }
                    else
                    {
                        var bWords = body.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                        if (bWords.Length >= 2)
                        {
                            var b1 = bWords[0];
                            var b2 = string.Join(" ", bWords.Skip(1));
                            return BuildLabel([Trunc(l1, 11), Trunc(b1, 11), Trunc(b2, 11)]);
                        }
                        return BuildLabel([Trunc(l1, 11), Trunc(l2, 11), Trunc(body, 11)]);
                    }
                }
            }
        }

        // 4. Plain text without colon
        if (t.Length <= 11)
        {
            return BuildLabel([t]);
        }

        var words = t.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (words.Length == 2)
        {
            return BuildLabel([Trunc(words[0], 11), Trunc(words[1], 11)]);
        }

        if (words.Length == 3)
        {
            if (words[0].Length + words[1].Length + 1 <= 11)
            {
                return BuildLabel([words[0] + " " + words[1], Trunc(words[2], 11)]);
            }
            if (words[1].Length + words[2].Length + 1 <= 11)
            {
                return BuildLabel([Trunc(words[0], 11), words[1] + " " + words[2]]);
            }
            return BuildLabel([Trunc(words[0], 11), Trunc(words[1], 11), Trunc(words[2], 11)]);
        }

        if (words.Length >= 4)
        {
            var l1 = words[0].Length + words[1].Length + 1 <= 11 ? words[0] + " " + words[1] : words[0];
            var rem = l1.Contains(" ") ? words.Skip(2).ToArray() : words.Skip(1).ToArray();
            if (rem.Length >= 2 && rem[0].Length + rem[1].Length + 1 <= 11)
            {
                var l2 = rem[0] + " " + rem[1];
                var l3 = string.Join(" ", rem.Skip(2));
                return BuildLabel([Trunc(l1, 11), Trunc(l2, 11), Trunc(l3, 11)]);
            }
            else
            {
                var l2 = rem.Length > 0 ? rem[0] : "";
                var l3 = rem.Length > 1 ? string.Join(" ", rem.Skip(1)) : "";
                return BuildLabel([Trunc(l1, 11), Trunc(l2, 11), Trunc(l3, 11)]);
            }
        }

        return BuildLabel([Trunc(t, 11)]);
    }

    private static string Trunc(string s, int maxLen)
    {
        s = s.Trim();
        if (s.Length <= maxLen) return s;
        return s.Substring(0, maxLen - 1) + ".";
    }

    private static FormattedTileLabel BuildLabel(IReadOnlyList<string> rawLines)
    {
        var validLines = rawLines.Where(l => !string.IsNullOrWhiteSpace(l)).Select(l => l.Trim()).ToList();
        if (validLines.Count == 0)
        {
            return new FormattedTileLabel(new List<FormattedTileLine>(), 8.0);
        }

        if (validLines.Count == 1)
        {
            var len = validLines[0].Length;
            var fontSize = len switch
            {
                <= 6 => 8.4,
                <= 9 => 7.8,
                <= 11 => 7.2,
                _ => 6.6
            };
            return new FormattedTileLabel(
            [
                new FormattedTileLine(validLines[0], 0.0)
            ], fontSize);
        }

        if (validLines.Count == 2)
        {
            var maxLen = Math.Max(validLines[0].Length, validLines[1].Length);
            var fontSize = maxLen switch
            {
                <= 7 => 7.5,
                <= 10 => 7.0,
                _ => 6.5
            };
            return new FormattedTileLabel(
            [
                new FormattedTileLine(validLines[0], -5.2),
                new FormattedTileLine(validLines[1], 5.5)
            ], fontSize);
        }

        // 3 lines
        return new FormattedTileLabel(
        [
            new FormattedTileLine(validLines[0], -9.5),
            new FormattedTileLine(validLines[1], 0.0),
            new FormattedTileLine(validLines[2], 9.5)
        ], 6.0);
    }

    public static string GetTileLabelSvg(string? rawTitle, long abilityId, string language, double cx, double cy, bool isLocked, bool isActive)
    {
        var label = FormatTile(rawTitle, abilityId, language);
        if (label.Lines.Count == 0) return string.Empty;

        var lockClass = isLocked ? " text-locked" : "";
        var activeClass = isActive ? " text-active" : "";
        var fs = label.FontSize.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);
        var cxStr = cx.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);
        var cyStr = cy.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);

        var sb = new System.Text.StringBuilder();
        sb.Append($"<text x=\"{cxStr}\" y=\"{cyStr}\" text-anchor=\"middle\" dominant-baseline=\"central\" class=\"hex-tile-label{lockClass}{activeClass}\" font-size=\"{fs}\" style=\"pointer-events: none; user-select: none;\">");
        foreach (var line in label.Lines)
        {
            var yStr = (cy + line.YOffset).ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);
            var encodedText = System.Net.WebUtility.HtmlEncode(line.Text);
            sb.Append($"<tspan x=\"{cxStr}\" y=\"{yStr}\">{encodedText}</tspan>");
        }
        sb.Append("</text>");
        return sb.ToString();
    }
}
