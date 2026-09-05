/**
 * generate_pomatools_trainer_cards.js
 * Generates composite Sync Pair avatar cards matching the exact pomatools.site SVG layout
 * with trainer portrait, Pokémon circle badge, rarity stars, role/ex-role badges, and exclusivity medals.
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const targetSrcDir = path.resolve(__dirname, '../src/BluesLab/wwwroot/img/trainers');
const targetOutDir = path.resolve(__dirname, '../output/wwwroot/img/trainers');

const TYPE_ASSET_KEYS = {
  0: "trainer", 1: "normal", 2: "fire", 3: "water", 4: "electric", 5: "grass",
  6: "ice", 7: "fighting", 8: "poison", 9: "ground", 10: "flying", 11: "psychic",
  12: "bug", 13: "rock", 14: "ghost", 15: "dragon", 16: "dark", 17: "steel", 18: "fairy"
};

const ROLE_NAME_MAP = {
  0: "role_strike", 1: "role_strike", 2: "role_support", 3: "role_tech", 4: "role_sprint", 5: "role_field", 6: "role_multi"
};

const ROLE_ICON_MAP = {
  0: "strike", 1: "strike", 2: "support", 3: "tech", 4: "sprint", 5: "field", 6: "multi"
};

function toBase64FromUrl(url) {
  // Can also use direct URL in headless chrome
  return url;
}

function generateCardHtml(pair) {
  const typeKey = TYPE_ASSET_KEYS[pair.type] || "normal";
  const bgClass = "bg_" + typeKey;
  
  const roleClass = ROLE_NAME_MAP[pair.role] || "role_strike";
  const roleIcon = ROLE_ICON_MAP[pair.role] || "strike";
  const roleIconUrl = `https://pomatools.site/assets/images/icon_role_${roleIcon}.png`;

  let roleTabsHtml = '';
  if (pair.exRole === -1 || pair.exRole === undefined) {
    roleTabsHtml = `
      <g id="role-tabs">
        <polygon points="110,375 122,327 210,327 222,375" class="${roleClass}" stroke="white" stroke-width="2"></polygon>
        <image href="${roleIconUrl}" x="143" y="328" width="46" height="46"></image>
      </g>`;
  } else {
    const exRoleClass = ROLE_NAME_MAP[pair.exRole] || "role_strike";
    const exRoleIcon = ROLE_ICON_MAP[pair.exRole] || "strike";
    const exRoleIconUrl = `https://pomatools.site/assets/images/icon_role_${exRoleIcon}.png`;
    roleTabsHtml = `
      <g id="role-tabs">
        <polygon points="90,375 102,327 162,327 162,375" class="${roleClass}" stroke="white" stroke-width="2"></polygon>
        <polygon points="162,375 162,327 222,327 234,375" class="${exRoleClass}" stroke="white" stroke-width="2"></polygon>
        <image href="${roleIconUrl}" x="110" y="328" width="45" height="45"></image>
        <image href="${exRoleIconUrl}" x="171" y="328" width="45" height="45"></image>
      </g>`;
  }

  let exclusivityHtml = '';
  if (pair.exclusivity === 996) {
    exclusivityHtml = `<image href="https://pomatools.site/assets/images/icon_exclusivity_master.png" x="-5" y="90" width="26" height="26"></image>`;
  } else if (pair.exclusivity === 997) {
    exclusivityHtml = `<image href="https://pomatools.site/assets/images/icon_exclusivity_masterex.png" x="-5" y="90" width="26" height="26"></image>`;
  } else if (pair.exclusivity === 998) {
    exclusivityHtml = `<image href="https://pomatools.site/assets/images/icon_exclusivity_arcsuit.png" x="-5" y="90" width="26" height="26"></image>`;
  } else if (pair.exclusivity === 999) {
    exclusivityHtml = `<image href="https://pomatools.site/assets/images/icon_exclusivity_academy.png" x="-5" y="90" width="26" height="26"></image>`;
  }

  let rarityHtml = '';
  if (pair.hasEx) {
    if (pair.rarity === 5) {
      rarityHtml = `<image href="https://pomatools.site/assets/images/rarity_ex.png" x="-8" y="-25" width="85" height="85"></image>`;
    } else {
      rarityHtml = `<image href="https://pomatools.site/assets/images/rarity_ex_${pair.rarity}.png" x="-8" y="-25" width="85" height="85"></image>`;
    }
  } else {
    rarityHtml = `<image href="https://pomatools.site/assets/images/rarity_${pair.rarity}.png" x="-8" y="-12" width="60" height="60"></image>`;
  }

  const trainerImgUrl = `https://pomatools.site/assets/trainer/${pair.actorId}_128.png`;
  const pokemonImgUrl = `https://pomatools.site/assets/pokemon/${pair.pokemonActorId}_128.png`;

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: transparent; width: 128px; height: 128px; overflow: visible; }
:root {
  --avatar-frame-normal: #8a8584;
  --avatar-frame-fire: #e44c4f;
  --avatar-frame-water: #3eacd8;
  --avatar-frame-electric: #c29e00;
  --avatar-frame-grass: #45924b;
  --avatar-frame-ice: #42b0b8;
  --avatar-frame-fighting: #d46d32;
  --avatar-frame-poison: #834da1;
  --avatar-frame-ground: #9a5533;
  --avatar-frame-flying: #507af1;
  --avatar-frame-psychic: #e36193;
  --avatar-frame-bug: #799438;
  --avatar-frame-rock: #8d7762;
  --avatar-frame-ghost: #9c6897;
  --avatar-frame-dragon: #0085a7;
  --avatar-frame-dark: #5b5a6b;
  --avatar-frame-steel: #69748b;
  --avatar-frame-fairy: #eb85aa;
}
.bg_normal { fill: var(--avatar-frame-normal); }
.bg_fire { fill: var(--avatar-frame-fire); }
.bg_water { fill: var(--avatar-frame-water); }
.bg_electric { fill: var(--avatar-frame-electric); }
.bg_grass { fill: var(--avatar-frame-grass); }
.bg_ice { fill: var(--avatar-frame-ice); }
.bg_fighting { fill: var(--avatar-frame-fighting); }
.bg_poison { fill: var(--avatar-frame-poison); }
.bg_ground { fill: var(--avatar-frame-ground); }
.bg_flying { fill: var(--avatar-frame-flying); }
.bg_psychic { fill: var(--avatar-frame-psychic); }
.bg_bug { fill: var(--avatar-frame-bug); }
.bg_rock { fill: var(--avatar-frame-rock); }
.bg_ghost { fill: var(--avatar-frame-ghost); }
.bg_dragon { fill: var(--avatar-frame-dragon); }
.bg_dark { fill: var(--avatar-frame-dark); }
.bg_steel { fill: var(--avatar-frame-steel); }
.bg_fairy { fill: var(--avatar-frame-fairy); }

.role_strike { fill: #e63945; }
.role_tech { fill: #11998e; }
.role_support { fill: #2193b0; }
.role_sprint { fill: #f37626; }
.role_field { fill: #834d9b; }
.role_multi { fill: #e8f347; }
</style>
</head>
<body>
<svg viewBox="0 0 128 128" width="128" height="128" class="avatar-svg" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="overflow: visible;">
  <defs>
    <path id="shape" fill-rule="evenodd" d="M28.78 40.5775C22.8292 40.5775 18.0052 45.4016 18.0052 51.3524L18.0052 313.792 52.4326 348.219 63.024 348.219 77.4925 333.751 255.552 333.751 255.552 348.219 315.818 348.219 348.245 315.792 348.245 290.233 328.248 290.233 328.248 221.524 348.245 201.527 348.245 149.598 328.247 129.6 328.247 77.0805 311.014 59.8473 190.628 59.8473 171.358 40.5775zM37 0 331 0 368 37 368 331 331 368 37 368 0 331 0 37z"></path>
    <path id="outline" d="M37 0 331 0 368 37 368 331 331 368 37 368 0 331 0 37z"></path>
    <clipPath id="clip"><use href="#outline"/></clipPath>
    <mask id="mask">
      <rect x="0" y="0" width="368" height="368" fill="white"></rect>
      <use href="#shape" fill="black"></use>
    </mask>
    <clipPath id="poke-bg-clip"><circle cx="300" cy="300" r="60"/></clipPath>
  </defs>

  <svg x="2" y="2" width="124" height="124" viewBox="0 0 368 368" preserveAspectRatio="xMidYMid meet" style="overflow: visible;">
    <g mask="url(#mask)" clip-path="url(#clip)">
      <rect x="0" y="0" width="368" height="368" class="${bgClass}"></rect>
      <image href="${trainerImgUrl}" x="-25" y="-28" width="450" height="450" preserveAspectRatio="xMidYMid slice"></image>
    </g>

    <use href="#shape" class="${bgClass}" stroke="rgba(0,0,0,0.5)" stroke-width="1.2"></use>
    <use href="#shape" fill="rgba(0,0,0,0.06)" pointer-events="none"></use>

    <circle cx="300" cy="300" r="80" class="${bgClass}" stroke="rgba(0,0,0,0.5)" stroke-width="1.2"></circle>

    ${roleTabsHtml}

    <!-- Pokemon circle -->
    <g clip-path="url(#poke-bg-clip)">
      <circle cx="300" cy="300" r="60" class="${bgClass}"></circle>
      <path d="M 240 322 L 360 278 L 400 278 L 400 400 L 200 400 Z" fill="rgba(255,255,255,0.3)"></path>
      <line x1="240" y1="322" x2="360" y2="278" stroke="rgba(0,0,0,0.2)" stroke-width="8"></line>
    </g>
    <circle cx="300" cy="300" r="12" fill="white" opacity="0.2"></circle>
    <circle cx="300" cy="300" r="8" class="${bgClass}" opacity="0.5"></circle>
    <image href="${pokemonImgUrl}" x="240" y="240" width="120" height="120" preserveAspectRatio="xMidYMid slice" clip-path="url(#poke-bg-clip)"></image>
  </svg>

  ${exclusivityHtml}
  ${rarityHtml}
</svg>
</body>
</html>`;
}

module.exports = { generateCardHtml };
