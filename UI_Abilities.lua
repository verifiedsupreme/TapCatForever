-- TapCatForever: Abilities page (learn class abilities with TapCoins)
local ADDON, TCF = ...

local KIND_TEXT = {
  nuke = "Attack", aoe = "Hits all enemies", dot = "Damage over time", heal = "Heal", shield = "Absorb shield",
  buff = "Damage buff", defense = "Defensive", stun = "Crowd control", execute = "Finisher", drain = "Drain",
  passive = "Passive", ward = "Passive defense",
}

TCF.UI.Builders.abilities = function(page, win)
  local U = TCF.UI
  local Text, Button, Panel = U.Text, U.Button, U.Panel
  local title = Text(page, "GameFontNormalLarge", nil, "LEFT"); title:SetPoint("TOPLEFT", 16, -14)
  local sub = Text(page, "GameFontDisableSmall", "Learned abilities are used automatically in Adventure (heals when hurt, area attacks on packs, finishers on low enemies).", "LEFT")
  sub:SetPoint("TOPLEFT", 16, -34); sub:SetWidth(530)
  local rows = {}
  for i = 1, 10 do
    local r = Panel(page, 528, 40, 0.85); r:SetPoint("TOP", 0, -56 - (i - 1) * 43)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(32, 32); r.icon:SetPoint("LEFT", 6, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.icon, "TOPRIGHT", 8, -1)
    r.desc = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.desc:SetPoint("BOTTOMLEFT", r.icon, "BOTTOMRIGHT", 8, 1); r.desc:SetWidth(330)
    r.kind = Text(r, "GameFontDisableSmall", nil, "RIGHT"); r.kind:SetPoint("TOPRIGHT", -112, -6)
    r.learn = Button(r, "Learn", 96, 22, function() if r.ab then TCF:LearnAbility(TCF.db.class, r.ab.key) end end)
    r.learn:SetPoint("RIGHT", -8, 0)
    rows[i] = r
  end
  return function(full)
    local class = TCF.db.class
    local cl = TCF.CLASS_BY_KEY[class]
    local level = TCF:CD(class).level
    title:SetText(cl.name .. " abilities")
    local list = TCF.ABILITIES[class]
    for i, r in ipairs(rows) do
      local a = list[i]
      r.ab = a
      if a then
        r:Show()
        local known = TCF:AbilityKnown(class, a.key)
        r.icon:SetTexture(TCF.Icon(a.icon)); r.icon:SetDesaturated(not known)
        r.name:SetText((known and "|cffffd100" or "|cffaaaaaa") .. a.name .. "|r  |cff888888(level " .. a.level .. ")|r")
        local cdText = a.cd > 0 and string.format("  |cff888888%ds cooldown|r", a.cd) or ""
        r.desc:SetText(a.desc .. cdText)
        r.kind:SetText(KIND_TEXT[a.kind] or "")
        local cost = TCF.AbilityCost(a.level)
        if known then
          r.learn:SetText("Known"); r.learn:SetEnabled(false)
        elseif level < a.level then
          r.learn:SetText("Level " .. a.level); r.learn:SetEnabled(false)
        else
          r.learn:SetText(U.coinStr(cost, 12)); r.learn:SetEnabled(TCF.db.coins >= cost)
        end
      else
        r:Hide()
      end
    end
  end
end
