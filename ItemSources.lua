-- TapCatForever: where every cosmetic came from (skins, effects, tap effects, hats...).
-- Each time one is granted (TCF:GrantItem, TCF:GrantSkin, the shops, achievements) Core.lua calls
-- TCF:NoteItemSource. Per character, like the cosmetics themselves:
--   charData.itemSources[id] = { first = { source, time }, last = { source, time } }
-- Item tooltips (Appearance tab, Compendium, loot notices) then say "Got it from: Heroic Cache,
-- 3 days ago". Items owned before this was tracked say so.
local ADDON, TCF = ...
local floor = math.floor

-- the reason texts the game passes, shortened to a source name
local REASONS = {
  { "^Found in an? (.+)$", "%1" },
  { "^Dropped by (.+) in (.+)$", "%1 (%2)" },
  { "^Found after (.+)$", "%1 (real dungeon run)" },
  { "^Your party brought it home from (.+)$", "Expedition: %1" },
  { "^Crafted$", "Crafting" },
  { "^Purchased$", "The Shop" },
}
function TCF.ItemSourceName(reason)
  if type(reason) ~= "string" or reason == "" then return "Found" end
  for _, r in ipairs(REASONS) do
    local s, n = reason:gsub(r[1], r[2])
    if n > 0 then return s end
  end
  return reason
end

local function store(self)
  local c = self.charData
  if type(c) ~= "table" then return nil end
  if type(c.itemSources) ~= "table" then c.itemSources = {} end
  return c.itemSources
end

-- Remembers where a cosmetic came from (the first time, and the latest copy).
function TCF:NoteItemSource(id, reason, when)
  local s = id and store(self)
  if not s then return end
  local e = { TCF.ItemSourceName(reason), floor(when or time()) }
  local rec = s[id]
  if type(rec) ~= "table" or type(rec.first) ~= "table" then s[id] = { first = e, last = e }
  else rec.last = e end
end

function TCF:ItemSourceRecord(id)
  local s = store(self)
  local rec = s and s[id]
  if type(rec) == "table" and type(rec.first) == "table" then return rec end
end

-- "just now", "5 minutes ago", "3 hours ago", "yesterday", "3 days ago", "2 months ago"
function TCF.TimeAgo(t, now)
  local d = (now or time()) - (tonumber(t) or 0)
  if d < 60 then return "just now" end
  if d < 3600 then local m = floor(d / 60); return m .. (m == 1 and " minute ago" or " minutes ago") end
  if d < 86400 then local h = floor(d / 3600); return h .. (h == 1 and " hour ago" or " hours ago") end
  if d < 2 * 86400 then return "yesterday" end
  if d < 60 * 86400 then return floor(d / 86400) .. " days ago" end
  if d < 730 * 86400 then return floor(d / (30 * 86400)) .. " months ago" end
  return floor(d / (365 * 86400)) .. " years ago"
end

-- the tooltip lines for an owned cosmetic: { text, ... }
function TCF:ItemSourceLines(id)
  if not (self.db and self.db.owned and self.db.owned[id]) then return {} end
  local rec = self:ItemSourceRecord(id)
  if not rec then return { "Got before this was tracked" } end
  local out = { string.format("Got it from: %s, %s", rec.first[1], TCF.TimeAgo(rec.first[2])) }
  local l = rec.last
  if type(l) == "table" and (l[1] ~= rec.first[1] or l[2] ~= rec.first[2]) then
    out[#out + 1] = string.format("Latest one from: %s, %s", l[1], TCF.TimeAgo(l[2]))
  end
  return out
end

-- every cosmetic tooltip says where it came from (wraps UI.lua's)
do
  local base = TCF.ItemTooltip
  if base then
    function TCF:ItemTooltip(tt, it, noSource)
      base(self, tt, it, noSource)
      if it and it.id then
        for _, line in ipairs(self:ItemSourceLines(it.id)) do tt:AddLine(line, 0.6, 0.8, 1, true) end
      end
    end
  end
end
