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
    private static readonly Regex MovePowerRegex = new(@"^(.*?):\s*(?:Power|Potencia)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveMgrRegex = new(@"^(.*?):\s*(?:Move Gauge Refresh|Movimiento Llenabarras|Llenabarras|MGR)\s*\+?(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveMprRegex = new(@"^(.*?):\s*(?:MP Refresh|Recupera PM|Movimiento Recupera PM|MPR)\s*\+?(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveAccRegex = new(@"^(.*?):\s*(?:Accuracy|Precisión)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveHealerRegex = new(@"^(.*?):\s*(?:Master Healer|Efecto Curativo)\s*\+?(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex LearnMoveRegex = new(@"^(?:Learn Move|Aprender mov\.)(?::\s*|\s+)(.*)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private static readonly (string Pattern, string Replacement)[] EsReplacements =
    [
        (@"Inmunidad Golpes Críticos", "Vigilancia"),
        (@"Inmunidad Reducción Defensa", "Inm. Def ↓"),
        (@"Inmunidad Reducción Ataque", "Inm. Atq ↓"),
        (@"Inmunidad Reducción Velocidad", "Inm. Vel ↓"),
        (@"Inmunidad Reducción Def\. Esp\.", "Inm. DefEsp↓"),
        (@"Inmunidad Reducción At\. Esp\.", "Inm. AtqEsp↓"),
        (@"Inmunidad Retroceso", "Inm. Retro."),
        (@"Curación Problemas Estado", "Cura Estado"),
        (@"Inmunidad Problemas Estado", "Inm. Estado"),
        (@"Primeros Auxilios (\d+)", "1.os Aux $1"),
        (@"Regeneración Saludable", "Regen. Salud."),
        (@"Entrada Furor (\d+)", "Ent. Furor $1"),
        (@"Protección Arena", "Prot. Arena"),
        (@"Movimiento Aliado Curación.*", "Curac. Aliado"),
        (@"Aceleración Mov\. Compi", "Acel. Compi"),
        (@"Llenabarras en 1\.er Apuro (\d+)", "Apuro MGR $1"),
        (@"Daño Llenabarras (\d+)", "Daño MGR $1"),
        (@"Acierto Llenabarras (\d+)", "Acierto MGR $1")
    ];

    private static readonly (string Pattern, string Replacement)[] EnReplacements =
    [
        (@"Critical Strike (\d+)", "Crit Strike $1"),
        (@"Hostile Environment (\d+)", "Hostile Env $1"),
        (@"Bob and Weave", "Bob & Weave"),
        (@"Healthy Healing", "Healthy Heal"),
        (@"Natural Remedy", "Nat. Remedy"),
        (@"Quick Cure", "Quick Cure"),
        (@"Sand Shelter", "Sand Shelter"),
        (@"First Aid (\d+)", "First Aid $1")
    ];

    public static FormattedTileLabel FormatTile(string? rawTitle, long abilityId, string language)
    {
        if (string.IsNullOrWhiteSpace(rawTitle))
        {
            return new FormattedTileLabel(new List<FormattedTileLine>(), 8.0);
        }

        var t = rawTitle.Replace("\r", "").Replace("\n", " ").Trim();
        t = Regex.Replace(t, @"\[[^\]]+\]", "").Trim();
        while (t.Contains("  ")) t = t.Replace("  ", " ");

        var isEs = string.Equals(language, "es", StringComparison.OrdinalIgnoreCase);

        // 1. Stats (Matching clean names like Sp. Atk, Defense, Speed, HP)
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

        // 2. Sync Moves
        if (t.Contains("Sync Move", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Movimiento Compi", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Impact: Power", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Impacto: Potencia", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Beam: Power", StringComparison.OrdinalIgnoreCase))
        {
            var mNum = NumberOnlyRegex.Match(t);
            var val = mNum.Success ? mNum.Groups[1].Value : "";
            var syncHeader = isEs ? "Mov. Compi:" : "Sync Move:";
            var pwrText = !string.IsNullOrEmpty(val) ? (isEs ? $"Potencia +{val}" : $"Power +{val}") : (isEs ? "Potencia" : "Power");
            return BuildLabel([syncHeader, pwrText]);
        }

        // 3. Max / Dynamax Moves
        if (t.Contains("Max Move", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Movimiento Dynamax", StringComparison.OrdinalIgnoreCase))
        {
            var mNum = NumberOnlyRegex.Match(t);
            var val = mNum.Success ? mNum.Groups[1].Value : "";
            var maxHeader = isEs ? "Mov. Dyna:" : "Max Move:";
            var pwrText = !string.IsNullOrEmpty(val) ? (isEs ? $"Potencia +{val}" : $"Power +{val}") : (isEs ? "Potencia" : "Power");
            return BuildLabel([maxHeader, pwrText]);
        }

        // 4. Move Power Ups
        var mPwr = MovePowerRegex.Match(t);
        if (mPwr.Success)
        {
            var move = mPwr.Groups[1].Value.Trim();
            var pwrText = isEs ? $"Potencia +{mPwr.Groups[2].Value}" : $"Power +{mPwr.Groups[2].Value}";
            return WrapMoveTitle(move, pwrText);
        }

        // 5. Move Gauge Refresh
        var mMgr = MoveMgrRegex.Match(t);
        if (mMgr.Success)
        {
            var move = mMgr.Groups[1].Value.Trim();
            return WrapMoveTitle(move, $"MGR{mMgr.Groups[2].Value}");
        }

        // 6. MP Refresh
        var mMpr = MoveMprRegex.Match(t);
        if (mMpr.Success)
        {
            var move = mMpr.Groups[1].Value.Trim();
            return WrapMoveTitle(move, $"MPR{mMpr.Groups[2].Value}");
        }

        // 7. Accuracy
        var mAcc = MoveAccRegex.Match(t);
        if (mAcc.Success)
        {
            var move = mAcc.Groups[1].Value.Trim();
            var prefix = isEs ? "Prec" : "Acc";
            return WrapMoveTitle(move, $"{prefix} +{mAcc.Groups[2].Value}");
        }

        // 8. Master Healer
        var mHeal = MoveHealerRegex.Match(t);
        if (mHeal.Success)
        {
            var move = mHeal.Groups[1].Value.Trim();
            var healText = isEs ? $"Curativo {mHeal.Groups[2].Value}" : $"Healer {mHeal.Groups[2].Value}";
            return WrapMoveTitle(move, healText);
        }

        // 9. Learn move
        var mLrn = LearnMoveRegex.Match(t);
        if (mLrn.Success)
        {
            var learnText = isEs ? "Aprender:" : "Learn:";
            var move = mLrn.Groups[1].Value.Trim();
            return WrapMoveTitle(learnText, move);
        }

        // 10. Language specific replacements
        if (isEs)
        {
            foreach (var (pattern, replacement) in EsReplacements)
            {
                if (Regex.IsMatch(t, pattern, RegexOptions.IgnoreCase))
                {
                    t = Regex.Replace(t, pattern, replacement, RegexOptions.IgnoreCase);
                    break;
                }
            }
        }
        else
        {
            foreach (var (pattern, replacement) in EnReplacements)
            {
                if (Regex.IsMatch(t, pattern, RegexOptions.IgnoreCase))
                {
                    t = Regex.Replace(t, pattern, replacement, RegexOptions.IgnoreCase);
                    break;
                }
            }
        }

        // Fits nicely on 1 line
        if (t.Length <= 11)
        {
            return BuildLabel([t]);
        }

        // Colon-based splitting
        if (t.Contains(": "))
        {
            var colonParts = t.Split(new[] { ": " }, 2, StringSplitOptions.RemoveEmptyEntries);
            if (colonParts.Length == 2)
            {
                return WrapMoveTitle(colonParts[0], colonParts[1].Trim());
            }
        }

        // Multi-word wrapping into 2 or 3 lines
        var words = t.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (words.Length == 2)
        {
            return BuildLabel([words[0], words[1]]);
        }

        if (words.Length == 3)
        {
            if (words[0].Length + words[1].Length + 1 <= 12)
            {
                return BuildLabel([words[0] + " " + words[1], words[2]]);
            }
            if (words[1].Length + words[2].Length + 1 <= 12)
            {
                return BuildLabel([words[0], words[1] + " " + words[2]]);
            }
            return BuildLabel([words[0], words[1], words[2]]);
        }

        if (words.Length >= 4)
        {
            var l1 = words[0] + " " + words[1];
            var l2 = words[2];
            var l3 = string.Join(" ", words.Skip(3));
            if (l3.Length > 12) l3 = l3.Substring(0, 11) + ".";
            return BuildLabel([l1, l2, l3]);
        }

        // Single long word
        return BuildLabel([t.Substring(0, Math.Min(11, t.Length)) + "."]);
    }

    private static FormattedTileLabel WrapMoveTitle(string moveName, string bottomLine)
    {
        moveName = moveName.Trim();
        var words = moveName.Split(' ', StringSplitOptions.RemoveEmptyEntries);

        if (words.Length == 1)
        {
            var line1 = moveName.EndsWith(":") ? moveName : moveName + ":";
            return BuildLabel([line1, bottomLine]);
        }

        if (words.Length == 2)
        {
            var line1 = words[0];
            var line2 = words[1].EndsWith(":") ? words[1] : words[1] + ":";
            return BuildLabel([line1, line2, bottomLine]);
        }

        // 3+ words (e.g. "Rainbow Jewel TB" or "K Tera Starstorm")
        if (words[0].Length <= 3) // e.g. "K", "B"
        {
            var line1 = words[0] + " " + words[1];
            var line2 = string.Join(" ", words.Skip(2));
            if (!line2.EndsWith(":")) line2 += ":";
            return BuildLabel([line1, line2, bottomLine]);
        }
        else
        {
            var line1 = words[0];
            var line2 = string.Join(" ", words.Skip(1));
            if (!line2.EndsWith(":")) line2 += ":";
            return BuildLabel([line1, line2, bottomLine]);
        }
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
                <= 6 => 8.5,
                <= 9 => 8.0,
                <= 11 => 7.4,
                _ => 6.8
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
                <= 7 => 7.8,
                <= 10 => 7.3,
                _ => 6.7
            };
            return new FormattedTileLabel(
            [
                new FormattedTileLine(validLines[0], -5.5),
                new FormattedTileLine(validLines[1], 5.8)
            ], fontSize);
        }

        // 3 lines
        return new FormattedTileLabel(
        [
            new FormattedTileLine(validLines[0], -10.0),
            new FormattedTileLine(validLines[1], 0.0),
            new FormattedTileLine(validLines[2], 10.0)
        ], 6.4);
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
