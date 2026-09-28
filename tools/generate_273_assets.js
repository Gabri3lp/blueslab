const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const pokemonDir = path.resolve(__dirname, '../src/BluesLab/wwwroot/img/pokemon');
const trainersDir = path.resolve(__dirname, '../src/BluesLab/wwwroot/img/trainers');

const POKEMON_DOWNLOADS = [
  { file: '006700_128.png', url: 'https://pomatools.site/assets/pokemon/pm0067_00_goriky_128.png' },
  { file: '018300_128.png', url: 'https://pomatools.site/assets/pokemon/pm0183_00_maril_128.png' },
  { file: '031900_128.png', url: 'https://pomatools.site/assets/pokemon/pm0319_00_samehader_128.png' },
  { file: '032300_128.png', url: 'https://pomatools.site/assets/pokemon/pm0323_00_bakuuda_128.png' },
  { file: '100100_128.png', url: 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/1001.png' },
  { file: '100200_128.png', url: 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/1002.png' },
  { file: '100300_128.png', url: 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/1003.png' },
  { file: '100400_128.png', url: 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/1004.png' }
];

const CARDS = [
  {
    outFile: '0196_11-1004_00.png',
    typeKey: 'fire',
    role: 'field',
    exRole: 'sprint',
    rarity: 5,
    hasEx: true,
    exclusivity: 997,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0196_10_fleurdelis_128.png',
    pokemonFile: '100400_128.png'
  },
  {
    outFile: '0195_10-1002_00.png',
    typeKey: 'ice',
    role: 'strike',
    exRole: 'tech',
    rarity: 5,
    hasEx: true,
    exclusivity: 997,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0195_00_ghetsis_128.png',
    pokemonFile: '100200_128.png'
  },
  {
    outFile: '0192_40-1003_00.png',
    typeKey: 'ground',
    role: 'support',
    exRole: 'field',
    rarity: 5,
    hasEx: true,
    exclusivity: 0,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0192_00_matsubusa_128.png',
    pokemonFile: '100300_128.png'
  },
  {
    outFile: '0193_40-1001_00.png',
    typeKey: 'grass',
    role: 'support',
    exRole: 'field',
    rarity: 5,
    hasEx: true,
    exclusivity: 0,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0193_00_aogiri_128.png',
    pokemonFile: '100100_128.png'
  },
  {
    outFile: '0221_00-0323_00.png',
    typeKey: 'ground',
    role: 'support',
    exRole: 'sprint',
    rarity: 5,
    hasEx: true,
    exclusivity: 0,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0221_00_homura_128.png',
    pokemonFile: '032300_128.png'
  },
  {
    outFile: '0224_00-0319_00.png',
    typeKey: 'water',
    role: 'sprint',
    exRole: 'tech',
    rarity: 5,
    hasEx: true,
    exclusivity: 0,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0224_00_izumi_128.png',
    pokemonFile: '031900_128.png'
  },
  {
    outFile: '0223_00-0319_00.png',
    typeKey: 'water',
    role: 'support',
    exRole: 'sprint',
    rarity: 5,
    hasEx: true,
    exclusivity: 0,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0223_00_ushio_128.png',
    pokemonFile: '031900_128.png'
  },
  {
    outFile: '0012_00-0067_00.png',
    typeKey: 'fighting',
    role: 'tech',
    exRole: null,
    rarity: 4,
    hasEx: true,
    exclusivity: 0,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0012_00_corni_128.png',
    pokemonFile: '006700_128.png'
  },
  {
    outFile: '0002_41-0183_00.png',
    typeKey: 'water',
    role: 'support',
    exRole: 'sprint',
    rarity: 5,
    hasEx: true,
    exclusivity: 0,
    trainerUrl: 'https://pomatools.site/assets/trainer/ch0002_41_kotone_128.png',
    pokemonFile: '018300_128.png'
  }
];

function buildCardHtml(card, pokemonDataUri) {
  const bgClass = 'bg_' + card.typeKey;
  const roleClass = 'role_' + card.role;
  const roleIconUrl = `https://pomatools.site/assets/images/icon_role_${card.role}.png`;

  let roleTabsHtml = '';
  if (!card.exRole) {
    roleTabsHtml = `
      <g id="role-tabs">
        <polygon points="110,375 122,327 210,327 222,375" class="${roleClass}" stroke="white" stroke-width="2"></polygon>
        <image href="${roleIconUrl}" x="143" y="328" width="46" height="46"></image>
      </g>`;
  } else {
    const exRoleClass = 'role_' + card.exRole;
    const exRoleIconUrl = `https://pomatools.site/assets/images/icon_role_${card.exRole}.png`;
    roleTabsHtml = `
      <g id="role-tabs">
        <polygon points="90,375 102,327 162,327 162,375" class="${roleClass}" stroke="white" stroke-width="2"></polygon>
        <polygon points="162,375 162,327 222,327 234,375" class="${exRoleClass}" stroke="white" stroke-width="2"></polygon>
        <image href="${roleIconUrl}" x="110" y="328" width="45" height="45"></image>
        <image href="${exRoleIconUrl}" x="171" y="328" width="45" height="45"></image>
      </g>`;
  }

  let exclusivityHtml = '';
  if (card.exclusivity === 997) {
    exclusivityHtml = `<image href="https://pomatools.site/assets/images/icon_exclusivity_masterex.png" x="-5" y="90" width="26" height="26"></image>`;
  }

  let rarityHtml = '';
  if (card.hasEx) {
    if (card.rarity === 5) {
      rarityHtml = `<image href="https://pomatools.site/assets/images/rarity_ex.png" x="-8" y="-25" width="85" height="85"></image>`;
    } else {
      rarityHtml = `<image href="https://pomatools.site/assets/images/rarity_ex_${card.rarity}.png" x="-8" y="-25" width="85" height="85"></image>`;
    }
  } else {
    rarityHtml = `<image href="https://pomatools.site/assets/images/rarity_${card.rarity}.png" x="-8" y="-12" width="60" height="60"></image>`;
  }

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: transparent; width: 128px; height: 128px; overflow: hidden; }
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
      <image href="${card.trainerUrl}" x="-25" y="-28" width="450" height="450" preserveAspectRatio="xMidYMid slice"></image>
    </g>

    <use href="#shape" class="${bgClass}" stroke="rgba(0,0,0,0.5)" stroke-width="1.2"></use>
    <use href="#shape" fill="rgba(0,0,0,0.06)" pointer-events="none"></use>

    <circle cx="300" cy="300" r="80" class="${bgClass}" stroke="rgba(0,0,0,0.5)" stroke-width="1.2"></circle>

    ${roleTabsHtml}

    <g clip-path="url(#poke-bg-clip)">
      <circle cx="300" cy="300" r="60" class="${bgClass}"></circle>
      <path d="M 240 322 L 360 278 L 400 278 L 400 400 L 200 400 Z" fill="rgba(255,255,255,0.3)"></path>
      <line x1="240" y1="322" x2="360" y2="278" stroke="rgba(0,0,0,0.2)" stroke-width="8"></line>
    </g>
    <circle cx="300" cy="300" r="12" fill="white" opacity="0.2"></circle>
    <circle cx="300" cy="300" r="8" class="${bgClass}" opacity="0.5"></circle>
    <image href="${pokemonDataUri}" x="240" y="240" width="120" height="120" preserveAspectRatio="xMidYMid slice" clip-path="url(#poke-bg-clip)"></image>
  </svg>

  ${exclusivityHtml}
  ${rarityHtml}
</svg>
</body>
</html>`;
}

(async () => {
  for (const pd of POKEMON_DOWNLOADS) {
    const dest = path.join(pokemonDir, pd.file);
    if (!fs.existsSync(dest)) {
      const resp = await fetch(pd.url);
      if (!resp.ok) throw new Error(`Failed to fetch ${pd.url}: ${resp.status}`);
      const buf = Buffer.from(await resp.arrayBuffer());
      fs.writeFileSync(dest, buf);
      console.log('Downloaded pokemon icon:', pd.file);
    }
  }

  // Resize 1001-1004 pokemon icons to 128x128 using Python Pillow
  execFileSync('python', [
    '-c',
    `from PIL import Image; import os; d=r'${pokemonDir}'; [Image.open(os.path.join(d,f)).resize((128,128), Image.Resampling.LANCZOS).save(os.path.join(d,f)) for f in ['100100_128.png','100200_128.png','100300_128.png','100400_128.png']]`
  ]);
  console.log('Resized 1001-1004 pokemon icons to 128x128');

  const tmpHtml = path.join(os.tmpdir(), 'card_273.html');
  for (const card of CARDS) {
    const pPath = path.join(pokemonDir, card.pokemonFile);
    const pokemonDataUri = 'data:image/png;base64,' + fs.readFileSync(pPath).toString('base64');
    const html = buildCardHtml(card, pokemonDataUri);
    fs.writeFileSync(tmpHtml, html, 'utf-8');
    const outPath = path.join(trainersDir, card.outFile);
    execFileSync(chromePath, [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--default-background-color=00000000',
      '--window-size=128,128',
      `--screenshot=${outPath}`,
      tmpHtml
    ]);
    console.log('Rendered composite trainer card:', card.outFile);
  }
  if (fs.existsSync(tmpHtml)) fs.unlinkSync(tmpHtml);
  console.log('All v2.73 image assets generated successfully!');
})();
