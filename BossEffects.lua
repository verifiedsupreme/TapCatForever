-- TapCatForever: back effects unlocked by big boss kills, with the one approved notice over the
-- cat. Six effects (storm, fire, frost, shadow, holy, nature) behind the cat. Each comes from
-- killing a specific real WoW boss (RealBosses.lua) or from beating a late Adventure final boss.
-- Only these unlocks show a short notice over the screen cat ("You unlocked Storm Aura", with the
-- effect playing behind the cat) that fades after a few seconds. Nothing else pops up.
-- Art: they use the existing effect drawings in their own colours for now. New drawings are
-- specified in tools/art_specs_adv/boss_effects.txt (listed under "Art to build" in notes/adv.md);
-- when the art track has built them, only the art field below changes.
local ADDON, TCF = ...

local sin, min, max = math.sin, math.min, math.max
local function c(r, g, b) return { r, g, b } end

-- { id, name, art, anim, colour, icon }
TCF.BOSS_EFFECTS = {
  { "fx_boss_storm",  "Storm Aura",          "fx_lightning", "flicker",  c(0.55, 0.85, 1.00), "Spell_Nature_Lightning" },
  { "fx_boss_fire",   "Firelord's Blaze",    "fx_flames",    "flicker",  c(1.00, 0.45, 0.10), "Spell_Fire_Fire" },
  { "fx_boss_frost",  "Frostwhisper Chill",  "fx_runes",     "spin",     c(0.62, 0.90, 1.00), "Spell_Frost_FrostNova" },
  { "fx_boss_shadow", "Shadowflame Shroud",  "fx_aura",      "pulse",    c(0.52, 0.20, 0.82), "Spell_Shadow_ShadowBolt" },
  { "fx_boss_holy",   "Crusader's Radiance", "fx_rays",      "spin",     c(1.00, 0.90, 0.50), "Spell_Holy_HolyBolt" },
  { "fx_boss_nature", "Verdant Wisps",       "fx_wisps",     "spinslow", c(0.40, 1.00, 0.45), "INV_Misc_Herb_10" },
}
for _, e in ipairs(TCF.BOSS_EFFECTS) do
  TCF.AddExtraItem({ id = e[1], name = e[2], slot = "effect", art = e[3], fxLayer = "back", fxAnim = e[4], rarity = 4,
    c1 = e[5], icon = e[6], source = "bosseffect" })
end

-- Adventure final bosses that unlock an effect: the boss's name exactly as TCF.TIERS has it
TCF.ADV_BOSS_EFFECTS = {
  ["Ossirian the Unscarred"] = "fx_boss_storm",
  ["Ragnaros"] = "fx_boss_fire",
  ["Kel'Thuzad"] = "fx_boss_frost",
  ["Nefarian"] = "fx_boss_shadow",
  ["C'Thun"] = "fx_boss_holy",
  ["Hakkar"] = "fx_boss_nature",
}

-- Gives a boss effect (if not owned) and shows the notice. Returns true when it was new.
function TCF:UnlockBossEffect(id, reason)
  local it = TCF.ITEMS[id]
  if not it or self.db.owned[id] then return false end
  self:GrantItem(it, reason)
  self:ShowEffectNotice(it)
  return true
end

-- called on every Adventure boss kill (Adventure.lua)
function TCF:AdvBossEffect(m)
  local id = m and m.final and TCF.ADV_BOSS_EFFECTS[m.name]
  if id then
    local t = self:AdvTier(self:CD().adv.tier)
    self:UnlockBossEffect(id, "Adventure: beat " .. m.name .. " in " .. t.name)
  end
end

-- "how to get it" lines for the Adventure source (the real-boss line comes from RealBosses.lua)
function TCF:BossEffectSourceLines(it)
  local out = {}
  for boss, id in pairs(TCF.ADV_BOSS_EFFECTS) do
    if id == it.id then
      local zone
      for _, t in ipairs(TCF.TIERS) do
        if t.bosses[#t.bosses][1] == boss then zone = t.name end
      end
      out[#out + 1] = string.format("Adventure: beat %s%s (the first kill unlocks it)", boss, zone and (" in " .. zone) or "")
    end
  end
  if it.source == "bosseffect" then
    out[#out + 1] = "A back effect: it plays behind your cat. Unlocking it shows a short notice over your cat"
  end
  return out
end

---------------------------------------------------------------- the notice over the cat
TCF.EFFECT_NOTICE = { LIFE = 5, FADE_IN = 0.35, FADE_OUT = 1.2 }

local function startNotice(self, n, it)
  local cat = self.cat
  local size = cat.size or 128
  n.item, n.age = it, 0
  n.fx:SetTexture(TCF.ART_PATH .. it.art)
  n.fx:SetVertexColor(it.c1[1], it.c1[2], it.c1[3])
  n.fx:SetSize(size * 1.45, size * 1.45)
  n.fx:ClearAllPoints(); n.fx:SetPoint("CENTER", cat.frame, "CENTER", 0, 0)
  n.fx:SetAlpha(0); n.fx:Show()
  n.text:SetText("|cffffffffYou unlocked|r\n" .. it.name)
  n.text:ClearAllPoints(); n.text:SetPoint("BOTTOM", cat.frame, "TOP", 0, size * 0.05)
  n.text:SetAlpha(0); n.text:Show()
  n:Show()
end

-- Shows "You unlocked <effect>" over the screen cat with the effect playing behind it, then
-- fades. Only for boss effects. Respects the "Popups on cat" setting and a hidden cat.
function TCF:ShowEffectNotice(it)
  local cat = self.cat
  if not it or not cat or not cat.frame or not self.db.ui.popups or self.db.ui.shown == false then return false end
  local n = self.effectNotice
  if not n then
    n = CreateFrame("Frame", nil, cat.frame)
    n.fx = cat.frame:CreateTexture(nil, "BACKGROUND", nil, -7)
    n.text = (cat.top or cat.frame):CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    n.text:SetShadowOffset(1, -1)
    if n.text.SetJustifyH then n.text:SetJustifyH("CENTER") end
    n.text:SetTextColor(1, 0.82, 0.2)
    n.queue = {}
    n:SetScript("OnUpdate", function(f, e)
      local N = TCF.EFFECT_NOTICE
      f.age = f.age + e
      local a = min(1, f.age / N.FADE_IN, max(0, (N.LIFE - f.age) / N.FADE_OUT))
      local t, anim = f.age, f.item and f.item.fxAnim
      local fxA = a
      if anim == "pulse" then fxA = a * (0.65 + 0.3 * sin(t * 2.2))
      elseif anim == "flicker" then fxA = a * (0.7 + 0.25 * sin(t * 9) * sin(t * 3.7)) end
      if anim == "spin" then f.fx:SetRotation(t * 0.35) elseif anim == "spinslow" then f.fx:SetRotation(t * 0.15) else f.fx:SetRotation(0) end
      f.fx:SetAlpha(max(0, fxA))
      f.text:SetAlpha(a)
      f.text:ClearAllPoints()
      f.text:SetPoint("BOTTOM", TCF.cat.frame, "TOP", 0, (TCF.cat.size or 128) * (0.05 + 0.06 * min(1, f.age / N.LIFE)))
      if f.age >= N.LIFE then
        f.fx:Hide(); f.text:Hide()
        local nextIt = table.remove(f.queue, 1)
        if nextIt then startNotice(TCF, f, nextIt) else f:Hide() end
      end
    end)
    n:Hide()
    self.effectNotice = n
  end
  if n:IsShown() and n.item then
    table.insert(n.queue, it)
  else
    startNotice(self, n, it)
  end
  if cat.SetFaceFor then cat:SetFaceFor("sparkle", 3) end
  self:PlaySound("rare")
  return true
end
