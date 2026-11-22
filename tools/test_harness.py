#!/usr/bin/env python3
"""Runs the addon against a mocked WoW API (Lua 5.1 via lupa) and exercises every feature."""
import os, re, sys, time
import lupa
try:
    from lupa import lua51 as L
except ImportError:
    L = lupa
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

MOCK = r'''
local frames = {}
_clock = 1000
function GetTime() return _clock end
date = os.date; time = os.time
-- WoW: Forever environment: modern API only, sandboxed Lua
C_AddOns = { GetAddOnMetadata = function() return "1.1.0" end }
GetAddOnMetadata = nil
function issecretvalue(v) return v == _SECRET end
_SECRET = setmetatable({}, { __eq = function() error("compared a secret value!") end })
C_Texture = { GetAtlasInfo = function(a) return a:match("^classicon%-") and {} or nil end }
function GetFileIDFromPath(p) if p:find("INV_Helmet_47") then return nil end return 12345 end
_settingsRegistered = false
Settings = { RegisterCanvasLayoutCategory = function(f, n) return { name = n } end,
             RegisterAddOnCategory = function(c) _settingsRegistered = true end }
BreakUpLargeNumbers = function(n) return tostring(n) end
local KNOWN_EVENTS = { ADDON_LOADED = 1, PLAYER_LOGIN = 1, PLAYER_REGEN_ENABLED = 1, GLOBAL_MOUSE_DOWN = 1,
  UNIT_SPELLCAST_SUCCEEDED = 1, PLAYER_ENTERING_WORLD = 1, ZONE_CHANGED_NEW_AREA = 1, ENCOUNTER_END = 1,
  LFG_COMPLETION_REWARD = 1, GROUP_ROSTER_UPDATE = 1, CHAT_MSG_ADDON = 1 } -- SENT left out on purpose to exercise the fallback
_inInstance = false
function UnitLevel() return 25 end
function UnitRace() return _race or "Orc", _race or "Orc", 2 end
_charName = "Kittyhawk"
-- group mock (party cats): _group = { party1 = { name, realm }, ... } or nil when alone
_group, _raid, _combat = nil, false, false
function IsInGroup() return _group ~= nil end
function IsInRaid() return _raid end
function GetNumGroupMembers() if not _group then return 0 end local n = 1 for _ in pairs(_group) do n = n + 1 end return n end
function UnitExists(u) return u == "player" or (_group and _group[u] ~= nil) or false end
function UnitName(u)
  if type(u) == "string" and (u:match("^party%d") or u:match("^raid%d")) then
    local g = _group and _group[u]
    if g then return g[1], g[2] end
    return nil
  end
  return _charName
end
function Ambiguate(full, ctx)
  local n, r = full:match("^([^%-]+)%-(.+)$")
  if r == "Forever" then return n end
  return full
end
_sent, _sendResult = {}, 0
C_ChatInfo = {
  RegisterAddonMessagePrefix = function(p) _prefix = p; return true end,
  SendAddonMessage = function(p, msg, ch) if _sendResult == 0 then table.insert(_sent, { p, msg, ch }) end; return _sendResult end,
}
function GetRealmName() return "Forever" end
function IsInInstance() if _inInstance then return true, _inInstance end return false, "none" end
function GetInstanceInfo() return "The Deadmines", _inInstance, 1, "Normal", 5, 0, false, 36 end
function UnitClass() return "Mage", "MAGE" end
function InCombatLockdown() return _combat end
function GetAddOnMetadata() return "1.0.0" end
function IsControlKeyDown() return _ctrl end
function IsShiftKeyDown() return false end
function GetCursorPosition() return 100, 100 end
function PlaySound() end
SOUNDKIT = { LOOTWINDOWCOINSOUND = 1, IG_QUEST_LIST_COMPLETE = 2 }
BackdropTemplateMixin = {}
UISpecialFrames = {}
tinsert = table.insert
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
unpack = unpack or table.unpack
CLASS_ICON_TCOORDS = setmetatable({}, { __index = function() return { 0, 0.25, 0, 0.25 } end })
SlashCmdList = {}
_chat = {}
DEFAULT_CHAT_FRAME = { AddMessage = function(_, m) table.insert(_chat, m) end }

local Obj = {}
local function noop() end
local methods = {}
function methods:SetScript(k, f) self.scripts[k] = f end
function methods:GetScript(k) return self.scripts[k] end
function methods:HookScript(k, f) self.scripts[k] = f end
function methods:Show() self.shown = true; if self.scripts.OnShow then self.scripts.OnShow(self) end end
function methods:Hide() self.shown = false end
function methods:SetShown(v) if v then self:Show() else self:Hide() end end
function methods:IsShown() return self.shown end
function methods:IsVisible() return self.shown end
function methods:GetPoint() return "BOTTOM", nil, "BOTTOM", 10, 200 end
function methods:GetWidth() return 140 end
function methods:GetHeight() return 140 end
function methods:GetCenter() return 50, 50 end
function methods:GetEffectiveScale() return 1 end
function methods:SetChecked(v) self.checked = v end
function methods:GetChecked() return self.checked end
function methods:SetText(t) self.text = t end
function methods:GetText() return self.text end
function methods:SetMinMaxValues(a, b) self.min, self.max = a, b end
function methods:SetValue(v) self.value = v; if self.scripts.OnValueChanged then self.scripts.OnValueChanged(self, v) end end
function methods:GetValue() return self.value end
function methods:SetTexture(path, ...) if type(path) == "string" then _textures[path] = true end; self.tex = path end
function methods:CreateTexture() return Obj.new("Texture") end
function methods:CreateFontString() return Obj.new("FontString") end
function methods:RegisterEvent(e) if not KNOWN_EVENTS[e] then error("Attempt to register unknown event " .. e) end self.events[e] = true end
function methods:RegisterUnitEvent(e) if not KNOWN_EVENTS[e] then error("Attempt to register unknown event " .. e) end self.events[e] = true end
function methods:SetPropagateKeyboardInput(v) self.prop = v end
function methods:EnableKeyboard(v) assert(self.prop, "keyboard enabled before propagation!"); self.kb = v end
_textures = {}

function Obj.new(kind, name)
  local o = setmetatable({ kind = kind, scripts = {}, events = {}, shown = true, name = name }, {
    __index = function(t, k) return methods[k] or (k:match("^%u") and noop or nil) end })
  o.shown = true
  table.insert(frames, o)
  if name then _G[name] = o end
  return o
end
function CreateFrame(kind, name, parent, template)
  local f = Obj.new(kind, name)
  return f
end
UIParent = CreateFrame("Frame", "UIParent")
Minimap = CreateFrame("Frame", "Minimap")
GameTooltip = CreateFrame("Frame", "GameTooltip")
_frames = frames
function _fire(event, ...)
  for _, f in ipairs(frames) do
    if f.events and f.events[event] and f.scripts.OnEvent then f.scripts.OnEvent(f, event, ...) end
  end
end
function _update(dt)
  _clock = _clock + dt
  for _, f in ipairs(frames) do if f.scripts.OnUpdate and f.shown then f.scripts.OnUpdate(f, dt) end end
end
'''

TEST = r'''
    local TCF = TapCatForever
    _fire("ADDON_LOADED", "TapCatForever")
    _fire("PLAYER_LOGIN")
    TCF.db.ui.chat = true; TCF.db.ui.sound = true  -- off by default; on here so the test exercises them
    -- loot rules watched for the whole run (checked in 12): chests never hold white gear, and a
    -- real legendary only ever comes out of a Heroic Cache or a Raider's Hoard
    _lootWatch = { bad = {}, chestGear = 0, legendaries = 0 }
    do
      local chestKey = {}
      for _, ch in ipairs(TCF.CHESTS) do chestKey[ch.name] = ch.key end
      local grant = TCF.GrantGear
      TCF.GrantGear = function(self, it, reason, reveal, key, ...)
        local w = _lootWatch
        local from = key or chestKey[reason]
        if from then
          w.chestGear = w.chestGear + 1
          if it.q < 2 then w.bad[#w.bad + 1] = "white gear from a chest: " .. it.name end
          if from == "dungeon" and it.q > 4 then w.bad[#w.bad + 1] = "a Dungeon Chest above Epic: " .. it.name end
        end
        if it.q == 5 and not it.crafted then
          w.legendaries = w.legendaries + 1
          if from ~= "heroic" and from ~= "raid" then w.bad[#w.bad + 1] = "a legendary from " .. tostring(reason) .. ": " .. it.name end
          if it.name:find("(", 1, true) then w.bad[#w.bad + 1] = "a placeholder legendary: " .. it.name end
        end
        return grant(self, it, reason, reveal, key, ...)
      end
    end
    assert(TCF.kbReady, "keyboard listener not set up")
    local kb = TapCatForeverKeyListener
    local keys = { "1", "2", "3", "Q", "E", "R", "F", "SPACE", "7", "8", "LSHIFT" }
    local n = 0
    for i = 1, 60000 do
      kb.scripts.OnKeyDown(kb, keys[i % #keys + 1])
      _update(0.06)
      n = n + 1
    end
    -- burst to test frenzy & cap
    for i = 1, 40 do kb.scripts.OnKeyDown(kb, "Q"); _update(0.01) end
    _fire("GLOBAL_MOUSE_DOWN", "LeftButton")
    _clock = _clock + 2
    local before = TCF.db.taps
    _fire("UNIT_SPELLCAST_SUCCEEDED", _SECRET)
    assert(TCF.db.taps == before + 1, "cast fallback did not count")
    assert(_settingsRegistered, "settings panel not registered")
    assert(TCF.Icon("INV_Helmet_47"):find("CatForm"), "icon fallback failed")
    for i = 1, 20 do _update(0.3) end
    print(string.format("taps=%d level=%d xp=%d coins=%d earned=%d frenzies=%d peak=%d drops=%d",
      TCF.db.taps, TCF:CD().level, TCF:CD().xp, TCF.db.coins, TCF.db.coinsEarned, TCF.db.stats.frenzies, TCF.db.stats.peakTPS, TCF.db.stats.drops))
    -- window and all tabs
    local shopFrom = #_frames
    assert(not TCF.window, "the window is built on first open")
    TCF:ToggleWindow()
    _shopScan = { shopFrom, #_frames }   -- the frames of the window, Shop page included (checked in 12)
    local win = TCF.window
    assert(win:IsShown())
    -- go through each slot of the wardrobe for every class
    for _, cl in ipairs(TCF.CLASSES) do
      TCF:SetClass(cl.key)
      for _, s in ipairs(TCF.SLOTS) do win.slot = s.key; win:RefreshWardrobe() end
    end
    -- money for testing
    TCF:AddCoins(200000)
    for i = 1, 60 do TCF:OpenChest("pouch") end
    for i = 1, 30 do TCF:OpenChest("strong") end
    for i = 1, 30 do TCF:OpenChest("heroic") end
    TCF.db.keys.strong = 2; TCF:OpenChest("strong", true); TCF:OpenChest("strong", true)
    assert(TCF.db.keys.strong == 0)
    TCF:BuildShop()
    print("shop stock:", #TCF.db.shop.stock)
    for _, id in ipairs(TCF.db.shop.stock) do TCF:BuyItem(id) end
    TCF:RerollShop(); TCF:RerollShop()
    -- equip everything owned
    for id in pairs(TCF.db.owned) do
      local it = TCF.ITEMS[id]
      if it.class then TCF:SetClass(it.class) end
      TCF:Equip(it)
    end
    -- hover all wardrobe cells
    for _, s in ipairs(TCF.SLOTS) do
      win.slot = s.key; win.page = 1; win:RefreshWardrobe()
    end
    -- hit every tab via its functions
    for tab = 1, #win.tabButtons do win:SelectTab(tab) end
    win.acScroll = 100; win:RefreshAchievements()
    for i = 1, 200 do _update(0.05) end
    -- pet the cat
    for i = 1, 105 do TCF.hud.scripts.OnMouseUp(TCF.hud, "LeftButton") end
    TCF.hud.scripts.OnDragStart(TCF.hud); TCF.hud.scripts.OnDragStop(TCF.hud)
    _ctrl = true; TCF.hud.scripts.OnMouseWheel(TCF.hud, 1); _ctrl = false
    for i = 1, 10 do _update(0.3) end
    -- slash commands
    for _, c in ipairs({ "", "bag", "show", "hide", "toggle", "lock", "unlock", "reset", "scale 1.5", "stats", "help" }) do SlashCmdList.TAPCATFOREVER(c) end
    TapCatForever_OnAddonCompartmentClick()
    -- minimap
    TapCatForeverMinimapButton.scripts.OnClick(TapCatForeverMinimapButton, "RightButton")
    TapCatForeverMinimapButton.scripts.OnDragStart(TapCatForeverMinimapButton)
    _update(0.1)
    local n, total = TCF:CountOwned()
    local ach = 0; for _ in pairs(TCF.db.achievements) do ach = ach + 1 end
    print(string.format("owned %d/%d, achievements %d/%d, level %d, chests %d, pets %d", n, total, ach, #TCF.ACHIEVEMENTS, TCF:CD().level, TCF.db.stats.chests, TCF.db.stats.pets))
    -- racial heritage: not given automatically; bought in the Shop
    assert(not TCF.db.owned.race_orc, "racial not given automatically")
    TCF:AddCoins(1000)
    assert(TCF:BuyRaceAccessory(), "buy orc tusks")
    assert(TCF.db.owned.race_orc and not TCF:BuyRaceAccessory(), "bought once")
    -- (auto-equip is checked on the fresh alt character below)
    -- racial toggle hides it; skins buy/equip/drop
    TCF:GetLoadout("WARRIOR").acc = "race_orc"
    assert(TCF:GetAppearance("WARRIOR").acc.id == "race_orc", "racial shown")
    TCF.db.ui.racial = false
    assert(TCF:GetAppearance("WARRIOR").acc == nil, "racial hidden")
    TCF.db.ui.racial = true
    TCF:AddCoins(20000)
    TCF.db.owned.skin_frostsaber = nil; TCF.db.owned.skin_zulian = nil  -- chests can drop skins at random
    assert(TCF:BuySkin("skin_frostsaber")); assert(TCF.db.look.skin == "skin_frostsaber")
    assert(not TCF:BuySkin("skin_zulian"), "drop-only skin can't be bought")
    TCF.cat:ApplyAppearance(TCF:GetAppearance())
    assert(TCF:GrantSkin("skin_zulian", "test"))
    TCF.db.look.skin = "skin_lion"; TCF.db.owned.skin_lion = 1; TCF.cat:ApplyAppearance(TCF:GetAppearance())
    TCF:Unequip("skin")
    assert(TCF.db.look.skin == nil)
    -- per-class levels: a fresh class starts at level 1
    local magelvl = TCF:CD("MAGE").level
    TCF:SetClass("ROGUE")
    assert(TCF:CD().level == 1 or TCF:CD().level < magelvl, "rogue should have its own level")
    TCF:SetClass("MAGE")
    -- key mapping: A = left, D = right
    local catobj = TCF.cat
    kb.scripts.OnKeyDown(kb, "A"); assert(catobj.lastSide == "L", "A should tap left")
    kb.scripts.OnKeyDown(kb, "D"); assert(catobj.lastSide == "R", "D should tap right")
    _fire("GLOBAL_MOUSE_DOWN", "LeftButton"); assert(catobj.lastSide == "L")
    _fire("GLOBAL_MOUSE_DOWN", "RightButton"); assert(catobj.lastSide == "R")
    -- Adventure: watch the tab and simulate 30 minutes of fighting
    win:SelectTab(2)
    TCF.advWatching = true
    local adv = TCF:CD().adv
    for i = 1, 20 do _update(0.25) end
    assert(adv.kills == 0, "no fighting before Start")
    TCF:AdvStart()
    for i = 1, 7200 do
      _update(0.25)
      if i % 4 == 0 then kb.scripts.OnKeyDown(kb, "Q") end
    end
    print(string.format("adventure: tier %d stage %d best %d kills %d bosses %d dps %.0f hp %.0f",
      adv.tier, adv.stage, adv.best, adv.kills, adv.bossKills, TCF:CombatStats().dps, TCF:CombatStats().hp))
    for i = 1, 5 do print("  log: " .. (TCF.advLog[i] or "")) end
    TCF:AdvStep(-1); TCF:AdvStep(1); TCF:AdvStep(50)
    -- quests: finish and claim
    TCF:EnsureQuests()
    local pouchBefore = TCF.db.keys.pouch
    for _, q in ipairs(TCF.db.quests.daily) do q.base = -1e9 end
    TCF.db.quests.weekly[1].base = -1e9
    win:SelectTab(7)
    for _, q in ipairs(TCF.db.quests.daily) do TCF:ClaimQuest(q) end
    TCF:ClaimQuest(TCF.db.quests.weekly[1])
    assert(TCF.db.keys.pouch == pouchBefore + 3, "daily quests should give pouches")
    TCF:ToggleBag(); TapCatForeverBag:Refresh()
    TCF:OpenChest("pouch", true)
    assert(TapCatForeverLootReveal:IsShown(), "loot reveal should show")
    -- loot queue: several drops at once, then OK to all
    -- (with the reel each chest spins in turn and its box takes the front; without it they queue)
    local anim = TCF.db.ui.chestAnim
    TCF.db.ui.chestAnim = false
    for k = 1, 5 do TCF:OpenChest("strong") end
    TCF.db.ui.chestAnim = anim
    for k = 1, 60 do _update(0.1) end   -- the pouch's reel above finishes; the five boxes queue behind it
    TapCatForeverLootReveal:UpdateQueue()
    assert(TapCatForeverLootReveal.okAll:IsShown(), "OK to all shows when more drops are waiting")
    TapCatForeverLootReveal.okAll.scripts.OnClick(TapCatForeverLootReveal.okAll)
    assert(not TapCatForeverLootReveal:IsShown(), "OK to all closes everything")
    TCF:OpenChest("pouch", true)
    TapCatForeverLootReveal.again.scripts.OnClick(TapCatForeverLootReveal.again)
    TapCatForeverLootReveal.equip.scripts.OnClick(TapCatForeverLootReveal.equip)
    for i = 1, 5 do TCF:OpenChest("strong") end
    for i = 1, 10 do TapCatForeverLootReveal.ok.scripts.OnClick(TapCatForeverLootReveal.ok) end
    TCF:ToggleBag()
    -- real dungeon run: enter, kill 3 bosses, leave after 6 minutes
    local dungeonBefore = TCF.db.keys.dungeon or 0
    _inInstance = "party"; _fire("PLAYER_ENTERING_WORLD")
    for i = 1, 3 do _fire("ENCOUNTER_END", 1, "Boss", 1, 5, 1) end
    _fire("ENCOUNTER_END", 2, "Boss", 1, 5, _SECRET)   -- secret success value must not error
    TCF.db.dungeonRun.start = TCF.db.dungeonRun.start - 400
    _inInstance = false; _fire("ZONE_CHANGED_NEW_AREA")
    assert((TCF.db.keys.dungeon or 0) == dungeonBefore + 1, "finishing a real dungeon gives a Dungeon Chest")
    -- group-finder completion while inside a raid
    local raidBefore = TCF.db.keys.raid or 0
    _inInstance = "raid"; _fire("PLAYER_ENTERING_WORLD"); _fire("LFG_COMPLETION_REWARD"); _fire("LFG_COMPLETION_REWARD")
    assert((TCF.db.keys.raid or 0) == raidBefore + 1, "raid completion once, a Raider's Hoard")
    _inInstance = false; _fire("PLAYER_ENTERING_WORLD")
    -- real gear: equip the best usable item in every slot, tooltips, selling
    TCF:SetClass("WARRIOR")
    TCF:CD().level = 60
    local equipped = 0
    for i = 1, 400 do
      local it = TCF:RollWorldLoot(math.random(1, 60), "WARRIOR")
      if it then TCF:GrantGear(it, "test") end
    end
    for id in pairs(TCF:Bag()) do
      local it = TCF.GEAR[id]
      if TCF:CanEquipGear(it, "WARRIOR") and (TCF:GearUpgrade(it) or 0) > 0 then if TCF:EquipGear(id) then equipped = equipped + 1 end end
      TCF:GearTooltip(GameTooltip, it)
    end
    local cs = TCF:CombatStats("WARRIOR")
    print(string.format("gear: owned %d kinds, equipped upgrades %d, power %d dps %.1f hp %d ilvl %d", (function() local n=0 for _ in pairs(TCF:Bag()) do n=n+1 end return n end)(), equipped, cs.power, cs.dps, cs.hp, cs.ilvl))
    local look = TCF:GetAppearance("WARRIOR")
    print("  gear look:", look.head and look.head.art, look.chest and look.chest.art, look.main and look.main.art, look.off and look.off.art)
    win:SelectTab(1); win.gearSlot = "HEAD"; win:Refresh(); win.gearSlot = nil; win:Refresh()
    local anyGear; for id in pairs(TCF:Bag()) do anyGear = TCF.GEAR[id]; break end
    TCF.UI.ShowTryOn(win, anyGear); TCF.UI.HideTryOn(win)
    -- 3D and pixel styles both render
    TCF.db.ui.cat3d = false; TCF:RefreshAll(); TCF.db.ui.cat3d = true; TCF:RefreshAll()
    TCF.cat:Tap("L"); for i = 1, 4 do _update(0.25) end
    for id in pairs(TCF:Bag()) do TCF:SellGear(id, true) end
    -- abilities: learn everything affordable
    TCF:AddCoins(50000)
    for _, cl in ipairs(TCF.CLASSES) do
      TCF:CD(cl.key).level = 60
      for _, a in ipairs(TCF.ABILITIES[cl.key]) do TCF:LearnAbility(cl.key, a.key) end
    end
    win:SelectTab(3)
    -- adventure in a raid with abilities, models and events
    TCF:AdvGoTo(23, 1); TCF:AdvStart(); win:SelectTab(2)
    for i = 1, 2400 do _update(0.25) end
    print("adventure raid: tier", TCF:CD().adv.tier, "stage", TCF:CD().adv.stage, "best", TCF:CD().adv.best)
    -- expeditions: send two parties, fast-forward, claim
    assert(TCF:StartExpedition("dm", { "MAGE", "ROGUE", "PRIEST" }))
    assert(TCF:StartExpedition("naxx", { "HUNTER", "DRUID", "SHAMAN" }))
    assert(not TCF:StartExpedition("elwynn", { "WARRIOR", "PALADIN", "WARLOCK" }), "max 2 expeditions")
    TCF:SetClass("MAGE"); for i = 1, 8 do _update(0.25) end
    assert(TCF.advRun.away, "mage should be away")
    win:SelectTab(4)
    for _, ex in ipairs(TCF.db.expeditions.active) do ex.finish = time() - 1 end
    TCF:ClaimExpedition(1); TCF:ClaimExpedition(1)
    assert(#TCF.db.expeditions.active == 0)
    -- professions: Mining by hand, then the tycoon, pickaxes, foremen
    local ps = TCF:ProfState()
    local fam = TCF:MainProf()   -- the test cat is a Mage: Tailoring (cloth spots)
    assert(fam == "cloth", "a Mage gathers cloth")
    for k = 1, 10 do _clock = _clock + 2; assert(TCF:MineClick(1), "gather by hand") end
    assert(not TCF:MineClick(1), "pickaxe has a cooldown")
    assert(ps.gold >= 2.4 and ps.gold < 4, "hand mining: a quarter of one mine's cycle per swing before you own any")
    assert(not TCF:MineClick(2), "the second spot needs one bought first")
    for k = 1, 10 do _clock = _clock + 2; TCF:MineClick(1) end  -- about 16 swings buys the first vein
    assert(TCF:BuyOp(fam, 1, 1), "buy the first spot")
    for k = 1, 3000 do
      kb.scripts.OnKeyDown(kb, "Q"); _update(0.25)
      if k % 4 == 0 then TCF:MineClick(1) end
      for i = 6, 1, -1 do TCF:BuyOp(fam, i, "max") end
      for i = 1, 6 do TCF:HireForeman(fam, i) end
      for _, u in ipairs(TCF.UPGRADES[fam]) do TCF:BuyUpgrade(u.id) end
    end
    local o = ps.ops[fam]
    print(string.format(fam .. " after ~12 min: gold %s lifetime %s spots %d/%d/%d/%d/%d/%d tool level %d skill %d",
      TCF.FormatBig(ps.gold), TCF.FormatBig(ps.lifetime), o[1].n, o[2].n, o[3].n, o[4].n, o[5].n, o[6].n, TCF:ToolLevel(fam), TCF:ProfSkill(fam)))
    assert(not TCF:ProfUnlocked("herbalism"), "herbalism needs renown")
    -- unlock everything for testing
    ps.renown, ps.renownEver, ps.gold = 200, 200, 1e12
    ps.lifetime = math.max(ps.lifetime, 1e17)   -- 1.5.3.4: Trade Gold earned unlocks (Renown alone doesn't)
    for _, p in ipairs(TCF.PROFESSIONS) do assert(TCF:ProfUnlocked(p.key), p.key .. " unlocked") end
    -- Herbalism: plant, water, harvest; gardener works offline
    assert(TCF:Plant(1, "peacebloom")); assert(not TCF:Plant(1, "peacebloom"), "plot busy")
    assert(not TCF:Plant(2, "dreamfoil"), "dreamfoil needs skill")
    for k = 1, 20 do TCF:PlotClick(1) end   -- watering (2 s each)
    assert(TCF:GardenState().plots[1].grown >= 40, "watering speeds growth")
    for k = 1, 100 do _update(0.25) end
    assert(TCF:PlotClick(1), "harvest"); assert((ps.mats.peacebloom or 0) > 0, "got peacebloom")
    TCF:BuyGardenUpgrade("gardener"); TCF:BuyPlot()
    TCF:Plant(1, "peacebloom"); TCF:Plant(2, "silverleaf")
    local pb = ps.mats.peacebloom
    ps.last = time() - 3600; TCF:ProfessionsTick(true)
    assert(ps.mats.peacebloom > pb + 30, "gardener harvested offline")
    -- First Aid: cloth -> bandages -> used in Adventure
    assert(TCF:BuyCloth("linen", 50))
    assert(TCF:QueueBandages("b_linen", 5))
    if TCF.advRun then TCF.advRun.bandageReady = 1e9 end  -- the fighting cat would drink one; count only what was made
    for k = 1, 120 do _update(0.25) end
    assert((ps.mats.b_linen or 0) >= 5, "bandages made: " .. tostring(ps.mats.b_linen))
    TCF:BuyAidUpgrade("medic")
    local run = TCF.advRun
    run.catHP = run.catMax * 0.2; run.t = 100; run.bandageReady = 0
    local before = run.catHP
    assert(TCF:UseBandage(run) and run.catHP > before, "cat uses a bandage when hurt")
    -- Fishing: the bobber
    TCF:FishCast(); assert(TCF.fishRun.state == "waiting")
    TCF:FishReel(); assert(TCF.fishRun.kind == "miss", "too soon scares the fish")
    TCF:FishCast(); TCF.fishRun.biteAt = 0; _update(0.25); _update(0.25)
    assert(TCF.fishRun.state == "bite", "bite"); TCF:FishReel()
    assert(TCF.fishRun.state == "result" and TCF.fishRun.kind ~= "miss", "caught a fish")
    TCF:BuyBuddy(); for k = 1, 600 do _update(0.25) end
    -- Cooking: experiment, discover, eat
    ps.mats.wolfmeat, ps.mats.mildspice, ps.mats.smallfish = 5, 5, 4
    TCF:PotAdd("wolfmeat"); TCF:PotAdd("mildspice")
    local text, r, found = TCF:CookPot()
    assert(found and r[1] == "d_wolf", "discovered spiced wolf meat: " .. tostring(text))
    TCF:PotAdd("smallfish"); TCF:PotAdd("mildspice"); TCF:PotAdd("wolfmeat")
    local t2 = TCF:CookPot(); assert(t2:find("Burnt"), "wrong combo burns")
    assert(TCF:EatDish("d_wolf")); assert(TCF:FoodBuff("dmg") > 1, "well fed")
    TCF:BuyCookUpgrade("chef"); TCF:CookState().chefRecipe = "d_wolf"
    ps.mats.wolfmeat, ps.mats.mildspice = 10, 10
    for k = 1, 400 do _update(0.25) end
    assert((ps.mats.d_wolf or 0) >= 3, "sous-chef cooked")
    -- crafting and every professions screen
    ps.mats.linen = (ps.mats.linen or 0) + 1000; assert(TCF:Craft(TCF.RECIPES[TCF:CraftProf()][1]), "craft the first Tailoring cosmetic")  -- (1.6: cosmetics cost more)
    for _, p in ipairs(TCF.PROFESSIONS) do
      win.profSel = p.key
      for _, v in ipairs({ "main", "upg", "craft", "renown" }) do win.profView = v; win:SelectTab(5); _update(0.2) end
    end
    ps.lifetime = 1e17
    assert(TCF:PrestigeTrade(), "sell the business")
    assert(ps.gold == 0 and ps.ops.mining[1].n == 0 and ps.ops.cloth[1].n == 0 and ps.ops.skinning[1].n == 0 and TCF:ProfUnlocked("cooking"), "reset keeps unlocks")
    print("renown after selling:", ps.renown)
    -- paperdoll click (right click unequips, left click jumps to the wardrobe)
    for tab = 1, #win.tabButtons do win:SelectTab(tab) end
    for i = 1, 20 do _update(0.25) end
    print("coins now", TCF.db.coins, "quests done", TCF.db.stats.questsDone, "dungeons", TCF.db.stats.dungeons, "raids", TCF.db.stats.raids)
    -- migration from v1 save (shared level)
    local old = TapCatForeverDB
    TapCatForeverDB = { level = 17, xp = 50, class = "PALADIN", taps = 5 }
    _fire("ADDON_LOADED", "TapCatForever")
    assert(TCF:CD("PALADIN").level == 17 and TCF:CD("WARRIOR").level == 1, "migration")
    TapCatForeverDB = old
    -- per-character data: a second character has its own gear, cosmetics, professions and levels
    _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")
    local coinsBefore = TCF.db.coins
    local mainOwned = 0; for _ in pairs(TCF.db.owned) do mainOwned = mainOwned + 1 end
    local mainLevel = TCF:CD("WARRIOR").level
    _charName = "Altcat"; _race = "Tauren"
    _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")
    assert(TCF.db.coins == coinsBefore, "TapCoins are shared: " .. tostring(coinsBefore) .. " -> " .. tostring(TCF.db.coins) .. " " .. tostring(_chat[#_chat]))
    assert(TCF:CD("WARRIOR").level == 1, "alt cats start at level 1")
    assert(not TCF.db.owned.race_tauren and not TCF.db.owned.race_orc, "alt has its own cosmetics")
    TCF:AddCoins(1000); assert(TCF:BuyRaceAccessory())
    assert(TCF:GetLoadout("MAGE").race == "race_tauren", "racial piece worn by the alt's cats (1.6: in its own slot)")
    -- only the selected class's cat adventures: others stay paused
    TCF:SetClass("MAGE"); TCF:AdvStart()
    for i = 1, 400 do _update(0.25) end
    local mageKills = TCF:CD("MAGE").adv.kills
    assert(mageKills > 0, "selected cat fights")
    local rogueKills = TCF:CD("ROGUE").adv.kills
    TCF:SetClass("ROGUE")
    for i = 1, 400 do _update(0.25) end
    assert(TCF:CD("ROGUE").adv.kills == rogueKills, "a cat that wasn't started stays home")
    assert(TCF:CD("MAGE").adv.kills == mageKills, "the mage pauses while another class is selected")
    TCF:SetClass("MAGE"); for i = 1, 200 do _update(0.25) end
    assert(TCF:CD("MAGE").adv.kills > mageKills, "the mage resumes when selected again")
    assert(not TCF.db.trade and TCF:ProfState().renown == 0 and TCF:ProfState("WARRIOR").renown == 0, "alt has its own professions")
    local altGear = 0; for _ in pairs(TCF:Bag()) do altGear = altGear + 1 end
    assert(altGear <= 9, "alt starts with just starter weapons")
    TCF:AddCoins(1)
    local coinsAlt = TCF.db.coins
    _charName = "Kittyhawk"; _race = nil
    _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")
    local back = 0; for _ in pairs(TCF.db.owned) do back = back + 1 end
    assert(back == mainOwned and TCF:CD("WARRIOR").level == mainLevel, "main character data intact")
    assert(TCF.db.coins == coinsAlt, "coins shared both ways")
    assert(rawget(TapCatForeverDB, "owned") == nil and TapCatForeverDB.chars.Altcat_Forever == nil, "per-char data lives under chars")
    print("characters:", (function() local n = 0 for _ in pairs(TapCatForeverDB.chars) do n = n + 1 end return n end)())
    -- re-login with existing saved data
    TCF.db = nil
    _fire("ADDON_LOADED", "TapCatForever")
    assert(TCF.db.taps > 0)
    ------------------------------------------------------------ class professions, crafted gear, party cats, loot notices
    -- (runs on a fresh character "Proftest" so the main character's data stays as it is)
    do
    local function check(c, m) if not c then error("check failed: " .. tostring(m), 2) end end
    local function near(a, b) return math.abs(a - b) <= 1e-9 * math.max(1, math.abs(a), math.abs(b)) end
    local function login(name) _charName = name; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN") end
    local function tipText(fn)
      local lines = {}
      GameTooltip.AddLine = function(_, t) lines[#lines + 1] = tostring(t) end
      GameTooltip.AddDoubleLine = function(_, a, b) lines[#lines + 1] = tostring(a) .. " " .. tostring(b) end
      fn()
      GameTooltip.AddLine, GameTooltip.AddDoubleLine = nil, nil
      return table.concat(lines, "\n")
    end
    local mainChar = _charName
    login("Proftest")
    check(TCF.db.class == "MAGE", "Proftest is a Mage")
    local ps = TCF:ProfState()
    -- 1. every class has its family, crafting skill and profession list
    local FAM = { WARRIOR = "mining", PALADIN = "mining", ROGUE = "skinning", DRUID = "skinning", HUNTER = "skinning",
      SHAMAN = "skinning", MAGE = "cloth", PRIEST = "cloth", WARLOCK = "cloth" }
    local CRAFT = { mining = "blacksmithing", skinning = "leatherworking", cloth = "tailoring" }
    local TAB = { mining = "Mining", skinning = "Skinning", cloth = "Tailoring" }
    local CRAFTNAME = { mining = "Blacksmithing", skinning = "Leatherworking", cloth = "Tailoring" }
    check(#TCF.CLASSES == 9 and #TCF.FAMILY_KEYS == 3, "9 classes, 3 families")
    for _, cl in ipairs(TCF.CLASSES) do
      local f = FAM[cl.key]
      check(f and TCF:MainProf(cl.key) == f, cl.key .. " -> " .. tostring(TCF:MainProf(cl.key)))
      check(TCF:CraftProf(cl.key) == CRAFT[f] and TCF.CRAFT_FAMILY[CRAFT[f]] == f, cl.key .. " crafts " .. tostring(TCF:CraftProf(cl.key)))
      local list = TCF:ProfList(cl.key)
      check(#list == 5 and list[1].key == f and list[1].name == TAB[f] and list[2].key == "herbalism" and list[3].key == "firstaid"
        and list[4].key == "fishing" and list[5].key == "cooking", cl.key .. " profession list")
      check(TCF.FAMILIES[f].craftName == CRAFTNAME[f] and TCF.PROF_BY_KEY[CRAFT[f]].name == CRAFTNAME[f], f .. " craft name")
      TCF:SetClass(cl.key)
      check(TCF:MainProf() == f and TCF:ProfUnlocked(f) and TCF:ProfUnlocked(CRAFT[f]), cl.key .. " current family is free")
    end
    TCF:SetClass("MAGE")
    -- 2. the three families use exactly the same numbers
    for i = 1, 6 do for _, k in ipairs(TCF.FAMILY_KEYS) do ps.ops[k][i].n = ({ 137, 55, 26, 9, 3, 1 })[i] end end
    for _, k in ipairs(TCF.FAMILY_KEYS) do ps.tools[k] = 17 end
    ps.upgrades.mining1_0, ps.upgrades.skinning1_0, ps.upgrades.cloth1_0 = true, true, true
    for _, k in ipairs(TCF.FAMILY_KEYS) do
      local F = TCF.FAMILIES[k]
      check(#F.ops == 9 and F.tab == TAB[k] and F.craft == CRAFT[k], k .. " family table")  -- (1.6: 9 spots)
      check(#TCF.UPGRADES[k] == #TCF.UPGRADES.mining, k .. " upgrade count")
      for j, u in ipairs(TCF.UPGRADES[k]) do
        local m = TCF.UPGRADES.mining[j]
        check(u.cost == m.cost and u.mult == m.mult and u.op == m.op and u.kind == m.kind, k .. " upgrade " .. j)
      end
      for i = 1, 6 do
        local mk = TCF.FAMILIES.mining.ops[i][2]
        check(TCF:OpCost(k, i, 1) == TCF:OpCost("mining", i, 1) and TCF:OpCost(k, i, 25) == TCF:OpCost("mining", i, 25)
          and TCF:OpRevenue(k, i) == TCF:OpRevenue("mining", i) and TCF:OpCycleTime(k, i) == TCF:OpCycleTime("mining", i)
          and TCF:OpMatsPerCycle(k, i) == TCF:OpMatsPerCycle("mining", i) and TCF:UpgradeMult(k, i) == TCF:UpgradeMult("mining", i)
          and TCF:OpMaxBuy(k, i) == TCF:OpMaxBuy("mining", i) and TCF:ToolGold(k, i) == TCF:ToolGold("mining", i)
          and TCF:ToolCycleShare(k, i) == TCF:ToolCycleShare("mining", i), k .. " spot " .. i .. " numbers")
        local mat = TCF.MAT_BY_KEY[F.ops[i][2]]
        check(mat and mat.value == TCF.MAT_BY_KEY[mk].value, k .. " material " .. i .. " sells like ore")
        if k ~= "mining" then check(type(F.ops[i][5]) == "number", k .. " spot " .. i .. " has a 3D model") end
      end
      for _, lv in ipairs({ 0, 15, 40 }) do
        check(TCF:ToolCost(k, lv) == TCF:ToolCost("mining", lv) and TCF:ToolCooldown(k, lv) == TCF:ToolCooldown("mining", lv)
          and TCF:ToolRolls(k, lv) == TCF:ToolRolls("mining", lv) and TCF:ToolMult(k, lv) == TCF:ToolMult("mining", lv), k .. " tool " .. lv)
      end
      check(near(TCF:GatherIncome(k), TCF:GatherIncome("mining")), k .. " income")
    end
    -- the same play for each family (same random numbers) earns exactly the same
    local results = {}
    for _, k in ipairs(TCF.FAMILY_KEYS) do
      TCF:CD().trade = nil
      local s = TCF:ProfState()
      math.randomseed(777)
      for step = 1, 2400 do
        _clock = _clock + 0.5
        if step % 4 == 0 then TCF:GatherClick(k, 1) end
        for i = 1, 6 do TCF:RunOp(k, i) end
        if step % 10 == 0 then
          for i = 6, 1, -1 do TCF:BuyOp(k, i, "max") end
          for i = 1, 6 do TCF:HireForeman(k, i) end
          for _, u in ipairs(TCF.UPGRADES[k]) do TCF:BuyUpgrade(u.id) end
        end
        TCF:ProfAdvance(0.5)
      end
      local mats = {}
      for i, o in ipairs(TCF.FAMILIES[k].ops) do mats[i] = s.mats[o[2]] or 0 end
      local n = {}
      for i = 1, 6 do n[i] = s.ops[k][i].n end
      results[k] = string.format("gold %.6f lifetime %.6f mats %s spots %s skill %d", s.gold, s.lifetime, table.concat(mats, "/"), table.concat(n, "/"), TCF:ProfSkill(k))
      for _, o in ipairs(TCF.FAMILY_KEYS) do if o ~= k then check(s.ops[o][1].n == 0, "only " .. k .. " was played") end end
    end
    math.randomseed((_seed or 1) + 1)   -- back to this run's own random numbers
    print("20 min of play per family: " .. results.mining)
    check(results.mining == results.skinning and results.mining == results.cloth,
      "families earn the same: " .. results.mining .. " | " .. results.skinning .. " | " .. results.cloth)
    -- 3. an old Mage save with Mining progress (before class professions) moves to Tailoring once
    TapCatForeverDB.chars["Oldmage-Forever"] = { class = "MAGE", trade = { gold = 500, lifetime = 1e6, renown = 3, renownEver = 3, prestiges = 1,
      ops = { mining = { { n = 120, p = 0.5, run = true, mgr = true }, { n = 30, p = 0, run = false, mgr = false }, { n = 4, p = 0, run = true, mgr = false } } },
      upgrades = { mining1_0 = true, mining_all0 = true }, milestones = { mining1_25 = true, mining1_100 = true },
      mats = { copper = 50, tin = 7, iron = 3, mithril = 2, thorium = 1, arcane = 2, linen = 10, peacebloom = 4, b_linen = 6 },
      last = time() - 7200, buy = 10, pick = { 3, 2 }, skill = { mining = 120, herbalism = 40 } } }
    login("Oldmage")
    local s = TCF:ProfState()
    check(s.famMoved, "migration flag")
    check(s.ops.cloth[1].n == 120 and s.ops.cloth[1].mgr and s.ops.cloth[2].n == 30 and s.ops.cloth[3].n == 4, "spots moved to Cloth Spots")
    check(s.ops.mining[1].n == 0 and s.ops.skinning[1].n == 0, "mining and skinning start fresh")
    check(TCF:ToolLevel("cloth") == 20 and TCF:ToolLevel() == 20 and TCF:ToolLevel("mining") == 0, "pickaxe level became the shears' level")
    check(s.upgrades.cloth1_0 and s.upgrades.cloth_all0 and not s.upgrades.mining1_0, "upgrades moved")
    check(s.milestones.cloth1_25 and s.milestones.cloth1_100 and not s.milestones.mining1_25, "milestones moved")
    check(TCF:ProfSkill("cloth") == 120 and s.skill.mining == nil and TCF:ProfSkill("herbalism") == 40, "gathering skill moved")
    for _, o in ipairs(TCF.FAMILIES.mining.ops) do check(s.mats[o[2]] == nil, "no ore left: " .. o[2]) end
    -- ore converts 1:1 by tier; the Tailor (Scavenger) on spot 1 also worked the 2 hours offline
    local ct = TCF:OpCycleTime("cloth", 1)
    local lo, hi = 60 + math.floor(0.5 + 7199 / ct) * TCF:OpMatsPerCycle("cloth", 1), 60 + math.floor(0.5 + 7205 / ct) * TCF:OpMatsPerCycle("cloth", 1)
    check(s.mats.linen >= lo and s.mats.linen <= hi, "linen: 10 + 50 copper + offline work, got " .. tostring(s.mats.linen) .. " want " .. lo .. ".." .. hi)
    check(s.mats.wool == 7 and s.mats.silk == 3 and s.mats.mageweave == 2 and s.mats.runecloth == 1 and s.mats.felcloth == 2, "ore became cloth by tier")
    check(s.mats.peacebloom == 4 and s.mats.b_linen == 6 and s.renown == 3 and s.gold > 500 and s.buy == 10, "other progress untouched")
    check(TCF:ProfList()[1].key == "cloth", "the old Mage sees Tailoring")
    login("Oldmage")   -- logging in again changes nothing
    s = TCF:ProfState()
    check(s.ops.cloth[1].n == 120 and s.ops.mining[1].n == 0 and s.mats.felcloth == 2, "migration runs once")
    -- the old shared trade became the Mage's own (1.5.1: every class has its own)
    check(TCF.db.trade == nil and TCF.db.tradeSplit and TCF:CD("MAGE").trade == s, "the old shared trade is now the Mage's")
    TCF:SetClass("WARRIOR"); s = TCF:ProfState()
    check(s ~= TCF:CD("MAGE").trade and s.gold == 0 and s.renown == 0 and s.ops.mining[1].n == 0 and s.ops.cloth[1].n == 0, "the Warrior has its own trade")
    check(TCF:CD("MAGE").trade.ops.cloth[1].n == 120 and TCF:CD("MAGE").trade.renown == 3, "the Mage keeps its spots and Renown")
    TCF:SetClass("MAGE"); check(TCF:ProfState().ops.cloth[1].n == 120, "switching back shows the Mage's spots")
    TapCatForeverDB.chars["Oldwar-Forever"] = { class = "WARRIOR", trade = { gold = 1, ops = { mining = { { n = 5, p = 0, run = false, mgr = false } } },
      mats = { copper = 9 }, pickLvl = 4, skill = { mining = 30 }, last = time() } }
    login("Oldwar"); s = TCF:ProfState()
    check(s.ops.mining[1].n == 5 and s.mats.copper == 9 and TCF:ToolLevel("mining") == 4 and TCF:ProfSkill("mining") == 30, "an old Warrior keeps Mining")
    TapCatForeverDB.chars["Oldrogue-Forever"] = { class = "ROGUE", trade = { gold = 1 } }
    login("Oldrogue"); s = TCF:ProfState()
    check(s.ops.skinning[6] and TCF:ToolLevel() == 0 and s.mats and s.upgrades, "a sparse old save is repaired")
    TapCatForeverDB.chars["Oldmage-Forever"], TapCatForeverDB.chars["Oldwar-Forever"], TapCatForeverDB.chars["Oldrogue-Forever"] = nil, nil, nil
    -- 4. every class has its own Trade Gold and professions (1.5.1)
    -- 4a. a 1.5.0 save with two families in use: the Mage keeps everything but the Mining, which
    -- goes to the character's most played Warrior or Paladin (the Warrior: level 12) with no gold
    do
      -- time stands still here, so a login a second later never adds a second of helper work
      local realTime = time
      local frozenT = realTime()
      time = function() return frozenT end
      local chestsPaid = {}
      local origAward = TCF.AwardChest
      TCF.AwardChest = function(self, key, src, ...) chestsPaid[#chestsPaid + 1] = key .. ":" .. tostring(src); return origAward(self, key, src, ...) end
      TapCatForeverDB.chars["Twofam-Forever"] = { class = "MAGE", keys = { strong = 2 },
        classData = { WARRIOR = { level = 12, xp = 5 }, PALADIN = { level = 3, xp = 900 }, MAGE = { level = 20, xp = 0 } },
        trade = { gold = 5000, lifetime = 9e6, renown = 7, renownEver = 7, prestiges = 1, famMoved = true, buy = 10, last = time(),
          ops = { cloth = { { n = 40, p = 0, run = true, mgr = true }, { n = 12, p = 0, run = true, mgr = true } },
                  mining = { { n = 30, p = 0.5, run = true, mgr = true }, { n = 8, p = 0, run = false, mgr = false } }, skinning = {} },
          tools = { cloth = 12, mining = 9, skinning = 0 },
          upgrades = { cloth1_0 = true, mining1_0 = true, mining_all0 = true },
          milestones = { mining1_25 = true, cloth1_25 = true },
          skill = { cloth = 80, tailoring = 40, mining = 60, blacksmithing = 25, herbalism = 30 },
          mats = { linen = 100, copper = 70, tin = 5, peacebloom = 9, b_linen = 3 },
          garden = { plots = {}, n = 5, up = { gardener = true } }, fish = { spot = 1, buddy = 1, bp = 0 } } }
      local keys0 = {}
      login("Twofam")
      -- (1.5.4: db.keys is a stand-in for the current cat's bag, so pairs() sees nothing; read every kind)
      for _, ch in ipairs(TCF.CHESTS) do keys0[ch.key] = TCF.db.keys[ch.key] or 0 end
      check(keys0.strong == 2, "the old chests are in the Mage's bag")
      local m, w = TCF:CD("MAGE").trade, TCF:CD("WARRIOR").trade
      check(TCF.db.trade == nil and TCF.db.tradeSplit and m and w and TCF:ProfState() == m, "split into the Mage's and the Warrior's trade")
      check(TCF:CD("PALADIN").trade == nil and TCF:CD("ROGUE").trade == nil, "nothing for the Paladin or a class that had no progress")
      check(m.gold == 5000 and m.lifetime == 9e6 and m.renown == 7 and m.renownEver == 7 and m.prestiges == 1 and m.buy == 10, "the Mage keeps gold and Renown")
      check(m.ops.cloth[1].n == 40 and m.ops.cloth[1].mgr and m.ops.cloth[2].n == 12 and m.tools.cloth == 12 and m.upgrades.cloth1_0
        and m.milestones.cloth1_25 and m.skill.cloth == 80 and m.skill.tailoring == 40 and m.skill.herbalism == 30, "the Mage keeps Tailoring")
      check(m.mats.linen == 100 and m.mats.peacebloom == 9 and m.mats.b_linen == 3 and m.mats.copper == nil and m.mats.tin == nil, "the Mage keeps its own materials")
      check(m.garden.n == 5 and m.garden.up.gardener and m.fish.buddy == 1, "the Mage keeps the garden and the fishing buddy")
      for i = 1, 6 do check(m.ops.mining[i].n == 0 and not m.ops.mining[i].mgr, "no Mining left on the Mage") end
      check(m.tools.mining == 0 and not m.upgrades.mining1_0 and not m.upgrades.mining_all0 and not m.milestones.mining1_25
        and m.skill.mining == nil and m.skill.blacksmithing == nil, "the Mage's Mining progress moved")
      check(w.gold == 0 and w.lifetime == 0 and w.renown == 0 and w.renownEver == 0, "the Warrior starts with no Trade Gold or Renown")
      check(w.ops.mining[1].n == 30 and w.ops.mining[1].mgr and w.ops.mining[2].n == 8 and w.tools.mining == 9 and w.upgrades.mining1_0
        and w.upgrades.mining_all0 and w.milestones.mining1_25 and w.skill.mining == 60 and w.skill.blacksmithing == 25, "the Warrior got Mining")
      check(w.mats.copper == 70 and w.mats.tin == 5 and w.mats.linen == nil and w.garden == nil and w.ops.cloth[1].n == 0, "the Warrior got the ore, nothing else")
      local nKeys = 0
      for _, cl in ipairs(TCF.CLASSES) do
        local t = TCF:CD(cl.key).trade
        if t then for k in pairs(t.milestones) do nKeys = nKeys + 1 end end
      end
      check(nKeys == 2 and #chestsPaid == 0, "milestones moved once each and no chest was paid: " .. nKeys .. " " .. #chestsPaid)
      check(TCF:GetStat("tradeGold") == 9e6 and TCF:GetStat("renown") == 7, "achievements count every cat's Trade Gold")
      login("Twofam")
      check(TCF:CD("MAGE").trade == m and m.ops.mining[1].n == 0 and w.ops.mining[1].n == 30 and m.gold == 5000, "the split runs once")
      -- a shared trade written again by 1.5.0 (playing an older version for a while) is added, not lost
      TCF.db.trade = { gold = 100, lifetime = 100, famMoved = true, ops = { cloth = { { n = 5, p = 0, run = false, mgr = false } },
        mining = { { n = 2, p = 0, run = false, mgr = false } } }, mats = { linen = 1, copper = 3 }, garden = { plots = {}, n = 7, up = { compost = true } } }
      check(TCF:ProfState() == m and TCF.db.trade == nil, "split again")
      check(m.gold == 5100 and m.lifetime == 9e6 + 100 and m.ops.cloth[1].n == 45 and m.mats.linen == 101, "added to the Mage")
      check(m.garden.n == 7 and m.garden.up.gardener and m.garden.up.compost, "garden upgrades kept from both")
      check(w.ops.mining[1].n == 32 and w.mats.copper == 73 and w.gold == 0, "the Mining part added to the Warrior")
      m.gold, m.lifetime, m.ops.cloth[1].n, m.mats.linen, m.garden.n, m.garden.up.compost = 5000, 9e6, 40, 100, 5, nil
      w.ops.mining[1].n, w.mats.copper = 30, 70
      -- 4b. milestone chests are once per cat: the Warrior's 25 was paid before the split
      TCF:SetClass("WARRIOR")
      check(TCF:ProfState() == w and TCF:MainProf() == "mining", "switched to the Warrior")
      w.ops.mining[1].n = 20; w.gold = 1e15
      check(TCF:BuyOp("mining", 1, 10) and w.ops.mining[1].n == 30 and #chestsPaid == 0, "no second chest for 25 Copper Veins")
      check(TCF:BuyOp("mining", 1, 80) and #chestsPaid == 1, "the Warrior earns its own chest at 100")
      TCF:SetClass("MAGE"); m.gold = 1e15; m.ops.cloth[1].n = 20
      check(TCF:BuyOp("cloth", 1, 40) and m.ops.cloth[1].n == 60 and #chestsPaid == 1, "the Mage's 25 was paid before the split")
      check(TCF:BuyOp("cloth", 1, 40) and #chestsPaid == 2, "the Mage earns its own chest at 100")
      for k, v in pairs(keys0) do check((TCF.db.keys[k] or 0) >= v, "chest keys kept") end
      TCF.AwardChest = origAward
      -- 4c. each class has its own gold, Renown and prices
      m.gold, w.gold, m.renown, w.renown = 1000, 50, 7, 0
      check(TCF:ProfState().gold == 1000 and near(TCF:EarnGold(100), 114) and near(m.gold, 1114) and w.gold == 50, "Trade Gold goes to the Mage")
      check(TCF:OpCost("cloth", 1, 1) ~= TCF:OpCost("mining", 1, 1), "prices count only this cat's own spots")
      TCF:SetClass("WARRIOR")
      check(TCF:ProfState().gold == 50 and TCF:EarnGold(100) == 100 and w.gold == 150 and near(m.gold, 1114), "Trade Gold goes to the Warrior")
      check(not TCF:ProfUnlocked("herbalism") and TCF:ProfList()[1].key == "mining", "the Warrior has its own Renown unlocks")
      -- the page shows the selected class's numbers
      local page = CreateFrame("Frame")
      local first = #_frames + 1
      local pw = { profSel = "mining", profView = "main", Refresh = function() end }
      local refreshPage = TCF.UI.Builders.professions(page, pw)
      local function shown(txt) for i = first, #_frames do local f = _frames[i]; if f.kind == "FontString" and f.text == txt then return true end end end
      refreshPage()
      check(shown("Warrior: Renown 0 (+0% gold)") and shown(TCF.GoldStr(150, 16)), "the page shows the Warrior's gold and Renown")
      TCF:SetClass("MAGE"); refreshPage()
      check(shown("Mage: Renown 7 (+14% gold)") and shown(TCF.GoldStr(1114, 16)), "switching class shows the Mage's numbers")
      -- 4d. offline: every cat's helpers worked, and each cat got its own gold
      m.last, w.last = time() - 3600, time() - 1800
      local mg, wg, wc, ml = m.gold, w.gold, w.mats.copper, m.mats.linen
      login("Twofam")
      check(w.gold > wg and m.gold > mg and w.mats.copper > wc and m.mats.linen > ml, "both cats' helpers worked offline")
      local wEarn = w.gold - wg
      TCF:SetClass("WARRIOR")
      local perCycle = TCF:OpRevenue("mining", 1) * (1 + 0.02 * w.renown)
      local cyc = TCF:OpCycleTime("mining", 1)
      check(wEarn >= perCycle * math.floor(1799 / cyc) - 1e-6 and wEarn <= perCycle * math.floor(1805 / cyc) + 1e-6, "the Warrior earned 30 minutes of its foreman: " .. wEarn)
      check(m.last >= time() - 1 and w.last >= time() - 1, "both cats are up to date")
      -- 4e. online: the cat you aren't playing keeps working, quietly, into its own trade
      TCF:SetClass("MAGE")
      w.renownEver = 60; w.lifetime = math.max(w.lifetime, 1e15); w.fish = { spot = 1, buddy = 1, bp = 0 }   -- Fishing learned (1.5.3.4: by Trade Gold earned)
      local odds = TCF.FISH_ODDS.buddyTreasure
      TCF.FISH_ODDS.buddyTreasure = 1
      local chat0, pouch0, toasts0 = #_chat, TCF:ChestsOf("pouch", "WARRIOR"), (TapCatForeverLootToasts and TapCatForeverLootToasts:IsShown())
      w.last = time() - 600
      mg, wg = m.gold, w.gold
      TCF.AwardChest = function() error("no chest pop-up for a cat you aren't playing") end
      TCF:ProfessionsTick(false, TCF.PROF_CATCHUP_EVERY)
      TCF.AwardChest = origAward
      TCF.FISH_ODDS.buddyTreasure = odds
      check(w.gold > wg and w.last == time(), "the Warrior's foreman worked while you played the Mage")
      check(#_chat == chat0, "no chat lines for the Warrior: " .. tostring(_chat[#_chat]))
      check(TCF:ChestsOf("pouch", "WARRIOR") >= pouch0 + 4, "the Warrior's fishing buddy found chests quietly (1.5.4: in the Warrior's own bag)")
      check(m.gold >= mg, "the Mage's own gold")
      -- the Mage's gold comes only from the Mage's own helpers
      local mOnly = m.gold
      w.last = time() - 600
      TCF:ProfCatchUp()
      check(m.gold == mOnly, "another cat's work never pays the Mage")
      -- 4f. a dish feeds the cat that ate it
      m.mats.d_wolf = 1
      check(TCF:EatDish("d_wolf") and TCF:FoodBuff("dmg") > 1 and TCF:FoodBuff("dmg", "WARRIOR") == 1, "the Mage is Well Fed, not the Warrior")
      TCF:SetClass("WARRIOR"); check(TCF:FoodBuff("dmg") == 1 and TCF:FoodBuff("dmg", "MAGE") > 1, "the Warrior isn't Well Fed")
      TCF:SetClass("MAGE")
      -- 4g. selling the business is per cat
      m.lifetime = 1e14
      check(TCF:PrestigeTrade() and m.gold == 0 and m.ops.cloth[1].n == 0 and w.ops.mining[1].n == 110 and w.gold > 0, "selling the Mage's business leaves the Warrior's")
      -- 4h. "Reset this character" clears every class's professions; "Reset ALL" clears every character
      TCF:ResetProgress("char")
      login("Twofam")
      for _, cl in ipairs(TCF.CLASSES) do
        local t = TCF:CD(cl.key).trade
        check(t == nil or (t.gold == 0 and t.renown == 0 and t.ops.mining[1].n == 0 and t.ops.cloth[1].n == 0), cl.key .. " professions reset")
      end
      check(TCF.db.trade == nil and TCF:ProfState().gold == 0, "reset: a fresh trade")
      local realDB = TapCatForeverDB
      TapCatForeverDB = { ui = {}, charsMigrated = true, chars = { ["Twofam-Forever"] = { class = "MAGE", classData = { MAGE = { trade = { gold = 5 } } } } } }
      TCF:ResetProgress("all")
      check(TapCatForeverDB.chars == nil and next(TapCatForeverDB.ui) == nil, "reset all clears every character")
      TapCatForeverDB = realDB
      TapCatForeverDB.chars["Twofam-Forever"] = nil
      time = realTime
      print(string.format("per-class trade: split, milestones, offline (Warrior +%s in 30 min), online, food, selling and reset checked", TCF.FormatBig(wEarn)))
    end
    -- 4i. a cat with First Aid keeps the cloth First Aid uses; the cloth spots still move
    do
      local function aidSave(renown, aid)
        return { class = "WARRIOR", classData = { MAGE = { level = 10, xp = 0 }, WARRIOR = { level = 20, xp = 0 } },
          trade = { gold = 10, lifetime = 10, renown = renown, renownEver = renown, famMoved = true, last = time(),
            ops = { cloth = { { n = 2, p = 0, run = false, mgr = false } }, mining = { { n = 4, p = 0, run = false, mgr = false } } },
            mats = { linen = 5000, runecloth = 3000, felcloth = 5, copper = 5, b_linen = 2 }, aid = aid } }
      end
      TapCatForeverDB.chars["Aidwar-Forever"] = aidSave(30, { up = { medic = true, contract = true } })
      login("Aidwar")
      local w, m = TCF:CD("WARRIOR").trade, TCF:CD("MAGE").trade
      check(TCF:ProfState() == w and w.mats.linen == 5000 and w.mats.runecloth == 3000 and w.mats.copper == 5 and w.mats.b_linen == 2, "the Warrior with First Aid keeps its cloth")
      check(w.aid and w.aid.up.medic and w.aid.up.contract and TCF:ProfUnlocked("firstaid"), "the Warrior keeps First Aid")
      check(m and m.ops.cloth[1].n == 2 and w.ops.cloth[1].n == 0 and m.mats.linen == nil and m.mats.runecloth == nil and m.mats.felcloth == 5, "the cloth spots and felcloth went to the Mage")
      TapCatForeverDB.chars["Aidwar-Forever"] = aidSave(5, nil)
      login("Aidwar")
      w, m = TCF:CD("WARRIOR").trade, TCF:CD("MAGE").trade
      check(w.mats.linen == nil and m.mats.linen == 5000 and m.mats.runecloth == 3000 and w.mats.copper == 5, "without First Aid the cloth goes with the cloth spots")
      TapCatForeverDB.chars["Aidwar-Forever"] = nil
    end
    -- 4j. 1.5.0 counted milestones over all families together: no chest is paid twice after the split
    do
      local paid = {}
      local origAward = TCF.AwardChest
      TCF.AwardChest = function(self, key, src, ...) paid[#paid + 1] = key; return origAward(self, key, src, ...) end
      local function msSave(nMining, nCloth, keys)
        return { class = "MAGE", classData = { MAGE = { level = 10, xp = 0 }, WARRIOR = { level = 10, xp = 0 } },
          trade = { gold = 0, lifetime = 0, famMoved = true, last = time(), milestones = keys,
            ops = { cloth = { { n = nCloth, p = 0, run = false, mgr = false } }, mining = { { n = nMining, p = 0, run = false, mgr = false } } } } }
      end
      TapCatForeverDB.chars["Msplit-Forever"] = msSave(200, 100, { mining1_25 = true, mining1_100 = true, cloth1_300 = true })
      login("Msplit")
      local m, w = TCF:CD("MAGE").trade, TCF:CD("WARRIOR").trade
      check(w.ops.mining[1].n == 200 and w.milestones.mining1_300 and w.milestones.mining1_25 and w.milestones.mining1_100, "the Warrior had the 300 chest with the Mage's cloth")
      check(m.milestones.cloth1_300 and m.milestones.cloth1_25 and m.milestones.cloth1_100 and not m.milestones.mining1_25, "the Mage had every chest the shared spots crossed")
      TCF:SetClass("WARRIOR"); w.gold = 1e15
      check(TCF:BuyOp("mining", 1, 100) and w.ops.mining[1].n == 300 and #paid == 0, "no second heroic chest at 300: " .. table.concat(paid, ","))
      TCF:SetClass("MAGE"); m.gold = 1e15
      check(TCF:BuyOp("cloth", 1, 250) and #paid == 0, "no second chest for the Mage either")
      TapCatForeverDB.chars["Msplit-Forever"] = msSave(24, 1, { cloth1_25 = true })
      login("Msplit")
      w = TCF:CD("WARRIOR").trade
      check(w.milestones.mining1_25 and not w.milestones.mining1_100, "24 Copper Veins and 1 cloth spot: the Warrior had the 25 chest")
      TCF:SetClass("WARRIOR"); w.gold = 1e15
      check(TCF:BuyOp("mining", 1, 1) and #paid == 0 and TCF:BuyOp("mining", 1, 75) and #paid == 1 and paid[1] == "strong", "the Warrior's next chest is its own 100")
      TCF.AwardChest = origAward
      TapCatForeverDB.chars["Msplit-Forever"] = nil
    end
    -- 4k. switching class back and forth never counts idle time twice (time() is whole seconds)
    do
      TapCatForeverDB.chars["Clock-Forever"] = { class = "MAGE", classData = { MAGE = { level = 5, xp = 0 }, WARRIOR = { level = 5, xp = 0 } } }
      login("Clock")
      local m = TCF:ProfState()
      TCF:SetClass("WARRIOR"); local w = TCF:ProfState(); TCF:SetClass("MAGE")
      m.ops.cloth[1].n, m.ops.cloth[1].mgr = 1, true
      w.ops.mining[1].n, w.ops.mining[1].mgr = 1, true
      local realTime, origAdvance = time, TCF.ProfAdvance
      local counted = {}
      TCF.ProfAdvance = function(self, dt, offline)
        local s = self:ProfState(); counted[s] = (counted[s] or 0) + dt
        return origAdvance(self, dt, offline)
      end
      for _, phase in ipairs({ 0.1, 0.4, 0.6, 0.9 }) do
        local t = realTime() + 100 + phase
        time = function() return math.floor(t) end
        m.last, w.last = math.floor(t), math.floor(t)
        counted[m], counted[w] = 0, 0
        for k = 1, 400 do
          t = t + 0.25
          TCF:ProfessionsTick(false, 0.25)
          if k % 2 == 0 then TCF:SetClass(TCF.db.class == "MAGE" and "WARRIOR" or "MAGE") end
        end
        TCF:ProfCatchUp()
        check(counted[m] >= 98.5 and counted[m] <= 101 and counted[w] >= 98.5 and counted[w] <= 101,
          string.format("100 seconds of switching every half second: Mage %.2f s, Warrior %.2f s", counted[m], counted[w]))
      end
      time = realTime
      TCF.ProfAdvance = origAdvance
      -- 4l. a /reload: every cat's helpers get the time it took, without a "While you were away" line
      TCF:SetClass("MAGE")
      m.last, w.last = time() - 20, time() - 20
      local mg, wg, chat0 = m.gold, w.gold, #_chat
      login("Clock")
      check(m.gold > mg and w.gold > wg and m.last >= time() - 1 and w.last >= time() - 1, "both cats' helpers worked during a short reload")
      local away = false
      for i = chat0 + 1, #_chat do if tostring(_chat[i]):find("While you were away") then away = true end end
      check(not away, "no away line after a short reload")
      TapCatForeverDB.chars["Clock-Forever"] = nil
    end
    login("Proftest")
    TCF:SetClass("MAGE")
    -- 5. recipes: gear recipes for every craft, cosmetics flagged cosmetic
    local famMats = {}
    for _, k in ipairs(TCF.FAMILY_KEYS) do famMats[k] = {} for _, o in ipairs(TCF.FAMILIES[k].ops) do famMats[k][o[2]] = true end end
    local crafted = {}
    for _, k in ipairs(TCF.FAMILY_KEYS) do
      local ck = CRAFT[k]
      check(TCF.RECIPES[ck] and TCF.RECIPES[k] == TCF.RECIPES[ck], ck .. " recipe list")
      local gear, cos, skins, last = 0, 0, 0, 0
      for _, r in ipairs(TCF.RECIPES[ck]) do
        check(r.prof == ck, "recipe prof")
        if r.gear then
          local it = TCF.GEAR[r.gear]
          check(it and it.crafted == ck and it.craftSkill == r.skill and not r.cosmetic, ck .. " gear recipe " .. tostring(r.gear))
          check(r.skill >= 1 and r.skill <= 300 and r.skill >= last, ck .. " gear recipes sorted by skill")
          for m in pairs(r.mats) do check(famMats[k][m], ck .. " recipe uses its own family's materials: " .. m) end
          last = r.skill; gear = gear + 1; crafted[it] = true
        else
          check(r.item and TCF.ITEMS[r.item] and r.cosmetic == true, ck .. " cosmetic recipe flagged cosmetic: " .. tostring(r.item))
          for m in pairs(r.mats) do check(famMats[k][m], ck .. " cosmetic uses its own family's materials: " .. m) end
          if TCF.ITEMS[r.item].slot == "skin" then skins = skins + 1 else cos = cos + 1 end
          local tip = tipText(function() TCF:ItemTooltip(GameTooltip, TCF.ITEMS[r.item]) end)
          check(tip:find("Cosmetic only (no stats)", 1, true), r.item .. " tooltip says cosmetic only")
        end
      end
      check(gear >= 30 and cos >= 5 and skins >= 1, string.format("%s: %d gear, %d cosmetics, %d skins", ck, gear, cos, skins))
      -- a new recipe at least every 25 skill points
      local prev = 0
      for _, r in ipairs(TCF.RECIPES[ck]) do if r.gear then check(r.skill - prev <= 25, ck .. " gap before skill " .. r.skill); prev = r.skill end end
    end
    for key, list in pairs(TCF.RECIPES) do for _, r in ipairs(list) do if r.item then check(r.cosmetic, key .. " cosmetic flag " .. r.item) end end end
    -- crafted gear is never loot
    local nCrafted = 0
    for _, it in ipairs(TCF.GEAR_LIST) do if it.crafted then nCrafted = nCrafted + 1; check(it.tier == 0 and it.boss == 0 and it.dc == 0, "crafted loot fields") end end
    local function noCrafted(list, where) for _, it in ipairs(list or {}) do check(not it.crafted, it.name .. " is crafted but in " .. where) end end
    for k, l in pairs(TCF.WORLD_POOL) do noCrafted(l, "WORLD_POOL") end
    for k, l in pairs(TCF.TIER_POOL) do noCrafted(l, "TIER_POOL") end
    for _, t in pairs(TCF.BOSS_LOOT) do for _, l in pairs(t) do noCrafted(l, "BOSS_LOOT") end end
    local origGrant = TCF.GrantGear
    local looted = 0
    TCF.GrantGear = function(self, it, reason, ...)
      if reason ~= "Crafted" then check(not it.crafted, "crafted gear dropped as loot: " .. it.name .. " (" .. tostring(reason) .. ")") end
      looted = looted + 1
      return origGrant(self, it, reason, ...)
    end
    for _, cl in ipairs(TCF.CLASSES) do
      for k = 1, 60 do
        local it = TCF:RollWorldLoot(math.random(1, 60), cl.key); check(not (it and it.crafted), "world roll gave crafted gear")
        local ti = math.random(#TCF.TIERS)
        local b = TCF:RollBossLoot(ti, math.random(#TCF.TIERS[ti].bosses), cl.key); check(not (b and b.crafted), "boss roll gave crafted gear")
      end
    end
    TCF:AddCoins(100000); TCF.openingAll = true
    for k = 1, 40 do TCF:OpenChest("strong"); TCF:OpenChest("heroic") end
    TCF.openingAll = nil
    print(string.format("crafted gear: %d items, never in loot pools; %d chest drops checked", nCrafted, looted))
    -- 6. crafting gear: a Mage crafts a Tailoring item into the Mage's bag; skill-ups WoW style
    ps = TCF:ProfState()
    local r1
    for _, r in ipairs(TCF.RECIPES.tailoring) do if r.gear and r.skill == 1 then r1 = r; break end end
    check(r1, "a Tailoring gear recipe at skill 1")
    local it1 = TCF.GEAR[r1.gear]
    for m, n in pairs(r1.mats) do ps.mats[m] = n * 60 end
    local mageBag, warBag = TCF:Bag("MAGE"), TCF:Bag("WARRIOR")
    local had, warHad = mageBag[it1.id] or 0, warBag[it1.id] or 0
    local skill0, gather0 = TCF:ProfSkill("tailoring"), TCF:ProfSkill("cloth")
    check(skill0 == 1, "Tailoring starts at 1")
    local toasts = 0
    local origToast = TCF.ShowLootToast
    TCF.ShowLootToast = function(self, ...) toasts = toasts + 1; return origToast(self, ...) end
    if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
    check(TCF:Craft(r1), "craft " .. it1.name)
    check(TCF:Bag("MAGE")[it1.id] == had + 1 and (TCF:Bag("WARRIOR")[it1.id] or 0) == warHad, "crafted gear goes to the current class's bag")
    check(toasts == 1 and not (TapCatForeverLootReveal and TapCatForeverLootReveal:IsShown()), "crafted gear: a small notice, no loot box")
    check(TCF:ProfSkill("tailoring") == 2 and TCF:ProfSkill("cloth") == gather0 and TCF:ProfSkill("blacksmithing") == 1, "Tailoring skill-up")
    -- (1.6 skill-up curve: a point every craft only while less than 5 above the recipe)
    for k = 2, 5 do TCF:Craft(r1) end
    check(TCF:ProfSkill("tailoring") == 6, "orange recipe: a point every craft, got " .. TCF:ProfSkill("tailoring"))
    for k = 1, 30 do TCF:Craft(r1) end
    local sk = TCF:ProfSkill("tailoring")
    check(sk > 6 and sk < 36, "yellow/green recipe: some crafts give no point, got " .. sk)
    local locked
    for _, r in ipairs(TCF.RECIPES.tailoring) do if r.gear and r.skill > sk then locked = r; break end end
    check(TCF:CraftBlocked(locked) == "Needs Tailoring " .. locked.skill .. ".", "locked recipe text: " .. tostring(TCF:CraftBlocked(locked)))
    for m, n in pairs(locked.mats) do ps.mats[m] = n end
    check(not TCF:Craft(locked), "can't craft above your skill")
    local bsr
    for _, r in ipairs(TCF.RECIPES.blacksmithing) do if r.gear then bsr = r; break end end
    for m, n in pairs(bsr.mats) do ps.mats[m] = n end
    check((TCF:CraftBlocked(bsr) or ""):find("Warrior or Paladin", 1, true) and not TCF:Craft(bsr), "a Mage can't make Blacksmithing gear")
    local tip = tipText(function() TCF:GearTooltip(GameTooltip, it1) end)
    check(tip:find("Crafted by Tailoring (skill " .. r1.skill .. ")", 1, true) and not tip:find("World drop", 1, true), "crafted gear tooltip: " .. tip)
    -- crafted gear sells for Trade Gold, never TapCoins
    local v, cur = TCF:GearSellValue(it1)
    check(cur == "gold" and v >= 1 and TCF:GearSellText(it1):find("Trade Gold$"), "crafted gear is priced in Trade Gold")
    local coins0, gold0 = TCF.db.coins, ps.gold
    local c, g = TCF:SellGear(it1.id)
    check(c == 0 and near(g, ps.gold - gold0) and g >= v and TCF.db.coins == coins0, "sold for Trade Gold only: " .. tostring(c) .. " " .. tostring(g))
    check(_chat[#_chat]:find("Trade Gold", 1, true) and not _chat[#_chat]:find("TapCoins", 1, true), "sell line: " .. _chat[#_chat])
    local found
    for _, it in ipairs(TCF.WORLD_POOL[1] or TCF.GEAR_LIST) do if not it.crafted and it.q == 2 then found = it; break end end
    check(select(2, TCF:GearSellValue(found)) == "coins", "found gear still sells for TapCoins")
    -- Sell junk pays TapCoins for found gear and Trade Gold for crafted gear
    local bag = TCF:Bag()
    local junkFound
    for _, it in ipairs(TCF.GEAR_LIST) do
      if not it.crafted and it.q == 2 and it.slot ~= "2H" and it.slot ~= "MH" and it.slot ~= "1H" and TCF:GearUsable(it, "MAGE") then junkFound = it; break end
    end
    bag[it1.id] = (bag[it1.id] or 0) + 4; bag[junkFound.id] = (bag[junkFound.id] or 0) + 4
    local junk, jn, jc, jg = TCF:JunkGear()
    check(jn >= 6 and jc > 0 and jg > 0 and junk[it1.id] and junk[junkFound.id], "junk has found and crafted gear: " .. jn .. " " .. jc .. " " .. jg)
    coins0, gold0 = TCF.db.coins, ps.gold
    local sc, sg = TCF:SellJunk()
    check(sc == jc and TCF.db.coins == coins0 + jc, "junk TapCoins: " .. tostring(sc) .. " vs " .. jc)
    check(near(sg, ps.gold - gold0) and sg >= jg, "junk Trade Gold: " .. tostring(sg) .. " vs " .. jg)
    check(_chat[#_chat]:find("TapCoins and", 1, true) and _chat[#_chat]:find("Trade Gold", 1, true), "junk line: " .. _chat[#_chat])
    check(select(2, TCF:JunkGear()) == 0, "nothing left to sell")
    -- a hunter with a melee weapon but no bow gets its bow once
    do
      local hcd, heq = TCF:CD("HUNTER"), TCF:GearEquipped("HUNTER")
      local saveR, saveM = heq.RANGED, heq.MAINHAND
      heq.RANGED = nil; heq.MAINHAND = 1317; hcd.hunterBow = nil
      TCF:FixStarterWeapons()
      check(heq.RANGED and TCF.GEAR[heq.RANGED].sub == "bow", "hunter gets its bow")
      heq.RANGED, heq.MAINHAND = saveR, saveM
    end
    -- 7. loot notices: gear found while playing goes to the bag; a slim line only while the window is open
    toasts = 0
    if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
    if not TCF.window then TCF:CreateWindow() end
    TCF.window:Show()
    TCF:GrantGear(found, "Adventure")
    TCF:GrantGear(TCF:RollWorldLoot(20, "MAGE") or found, "Quest")
    check(toasts == 2 and TapCatForeverLootToasts and TapCatForeverLootToasts:IsShown(), "non-chest gear: notices")
    check(not (TapCatForeverLootReveal and TapCatForeverLootReveal:IsShown()), "non-chest gear: no loot box")
    local named = false
    for _, f in ipairs(_frames) do if f.kind == "FontString" and type(f.text) == "string" and f.text:find(found.name, 1, true) == 1 and f.shown then named = true end end
    check(named, "the notice names the item")
    do
      TCF.window:Hide()
      local shownBefore = 0
      for _, f in ipairs(_frames) do if f.kind == "Button" and f.item and f.shown then shownBefore = shownBefore + 1 end end
      for _, f in ipairs(_frames) do if f.kind == "Button" and f.item then f:Hide() end end
      TCF:GrantGear(found, "Adventure")
      local cos
      for _, it in ipairs(TCF.ITEM_LIST) do if it.source == "loot" then cos = it; break end end
      if cos then TCF:GrantItem(cos, "Lucky find while tapping") end
      local shown = 0
      for _, f in ipairs(_frames) do if f.kind == "Button" and f.item and f.shown then shown = shown + 1 end end
      check(shown == 0, "window closed: no notice anywhere (not over the cat)")
      TCF.window:Show()
    end
    TCF:AwardChest("pouch", "test")   -- earning a chest key is not opening it
    check(not (TapCatForeverLootReveal and TapCatForeverLootReveal:IsShown()), "a chest key alone shows no loot box")
    -- opening a chest by hand: the reel plays (your own click), no small notice
    do
      local chance, skinRoll = TCF.CHEST_GEAR_CHANCE, TCF.RollSkinSource
      TCF.CHEST_GEAR_CHANCE, TCF.RollSkinSource = 1, function() end
      TCF.db.ui.chestAnim = true
      local gotGear = false
      for k = 1, 20 do
        if gotGear then break end
        TCF.db.keys.pouch = (TCF.db.keys.pouch or 0) + 1
        toasts = 0
        TCF:OpenChest("pouch", true)
        if TCF.lastChest and TCF.lastChest.gear then
          gotGear = true
          -- 1.5.3.1: every chest opened by hand spins the reel; a green gets the slim line after it
          check(toasts == 0 and TapCatForeverReel and TapCatForeverReel:IsShown(), "chest gear: the reel plays")
          if TCF.lastChest.gear.q < 3 and TCF.reel then
            TCF.reel:Finish()
            check(toasts == 0, "green chest gear: the loot box after the reel, no slim line")
          end
        end
        if TapCatForeverReel then TapCatForeverReel:Hide() end
        if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
      end
      check(gotGear, "a chest gave gear")
      TCF.CHEST_GEAR_CHANCE, TCF.RollSkinSource = chance, skinRoll
    end
    TCF.ShowLootToast = origToast
    TCF.GrantGear = origGrant
    -- 8. starter weapons: every class starts with a weapon of its own kind
    for _, cl in ipairs(TCF.CLASSES) do
      local w = TCF:StarterWeapon(cl.key)
      check(w and w.q == 2 and w.req <= 10 and not w.crafted and TCF:GearUsable(w, cl.key), cl.key .. " starter weapon")
      local okSub = false
      for _, sub in ipairs(TCF.STARTER_WEAPONS[cl.key]) do if sub == w.sub then okSub = true end end
      check(okSub, cl.key .. " starter weapon kind " .. tostring(w.sub))
      local eq = TCF:GearEquipped(cl.key)
      check(eq[w.slot == "RANGED" and "RANGED" or "MAINHAND"] == w.id and (TCF:Bag(cl.key)[w.id] or 0) >= 1, cl.key .. " starts holding " .. w.name)
    end
    -- 9. fishing view: the dock builds with and without the Fishing Buddy
    ps.renownEver = math.max(ps.renownEver, 200); ps.lifetime = math.max(ps.lifetime, 1e17)   -- everything learned (1.5.3.4: by Trade Gold earned)
    local fs = TCF:FishState()
    local function buddyLabelShown(from, name)
      for i = from, #_frames do local f = _frames[i]; if f.kind == "FontString" and f.text == name and f.shown then return true end end
      return false
    end
    local function buildPage(buddy)
      fs.buddy = buddy
      local first = #_frames + 1
      local page = CreateFrame("Frame")
      local w = { profSel = "fishing", profView = "main", Refresh = function() end, preview = TCF.window and TCF.window.preview }
      local refresh = TCF.UI.Builders.professions(page, w)
      check(type(refresh) == "function", "professions page builder returns its refresh")
      refresh(); for k = 1, 8 do for i = first, #_frames do local f = _frames[i]; if f.scripts.OnUpdate and f.shown then f.scripts.OnUpdate(f, 0.2) end end end
      return first, refresh, page
    end
    local first, refresh = buildPage(0)
    check(not buddyLabelShown(first, TCF.BUDDY_LEVELS[1].name), "no buddy on the dock before hiring")
    fs.buddy = 1; refresh()
    check(buddyLabelShown(first, TCF.BUDDY_LEVELS[1].name), "the buddy appears once hired")
    first = buildPage(2)
    check(buddyLabelShown(first, TCF.BUDDY_LEVELS[2].name), "a page built with a level 2 buddy shows him")
    TCF:FishCast(); TCF.fishRun.biteAt = 0; fs.bp = TCF.BUDDY_LEVELS[2].every - 0.1
    for k = 1, 8 do _update(0.25) end
    -- the buddy's catch pop belongs to one cat: switching to another cat's buddy is not a catch
    do
      local cls0 = TCF.db.class
      TCF:SetClass("MAGE")
      local mf = TCF:FishState()
      mf.buddy, mf.bp = 1, 40
      local first = #_frames + 1
      local page = CreateFrame("Frame")
      local refresh = TCF.UI.Builders.professions(page, { profSel = "fishing", profView = "main", Refresh = function() end, preview = TCF.window and TCF.window.preview })
      local function step(n) for _ = 1, n do for i = first, #_frames do local f = _frames[i]; if f.scripts.OnUpdate and f.shown then f.scripts.OnUpdate(f, 0.2) end end end end
      local function popShown() for i = first, #_frames do local f = _frames[i]; if f.kind == "FontString" and f.text == "|cffffffff+1 fish|r" and f.shown then return true end end return false end
      refresh(); step(2)
      mf.bp = 5; step(1)
      check(popShown(), "a catch shows +1 fish")
      mf.bp = 40; step(10)
      check(not popShown(), "the pop goes away")
      TCF:SetClass("PRIEST")
      local ps2 = TCF:ProfState(); ps2.renownEver = math.max(ps2.renownEver, 200); ps2.lifetime = math.max(ps2.lifetime, 1e17)
      local pf = TCF:FishState(); pf.buddy, pf.bp = 1, 5
      check(pf ~= mf, "the Priest has its own fishing buddy")
      refresh(); step(1)
      check(not popShown(), "switching to the Priest's buddy is not a catch")
      TCF:SetClass(cls0)
    end
    -- 10. party cats
    _sent = {}
    local xpAlone = TCF:FoodBuff("xp")
    check(TCF:PartyBonus() == 1 and TCF:PartyCount() == 0, "alone: no bonus")
    _fire("GROUP_ROSTER_UPDATE"); check(#_sent == 0, "no hello while alone")
    _group = { party1 = { "Alice", nil }, party2 = { "Bob", "Other Realm" } }
    _fire("GROUP_ROSTER_UPDATE")
    check(#_sent == 1 and _sent[1][1] == _prefix and _sent[1][2]:match("^H1;MAGE;%d+;") and _sent[1][3] == "PARTY" and #_sent[1][2] <= 240, "hello on joining")
    local function msg(text, sender, ch, prefix) _fire("CHAT_MSG_ADDON", prefix or _prefix, text, ch or "PARTY", sender) end
    TCF:SetClass("WARRIOR"); local aliceText = "H1;" .. TCF:PartyPayload("WARRIOR"); TCF:SetClass("MAGE")
    msg(aliceText, "Alice-Forever")
    check(TCF:PartyCount() == 1 and near(TCF:PartyTapMult(), 1.2), "fake hello counted: +20%")
    local row = TapCatForeverPartyCats
    check(row and row:IsShown() and row.cells[1]:IsShown() and not row.cells[2]:IsShown(), "one small cat shown")
    for k = 1, 22 do _update(0.5) end
    check(#_sent == 2 and _sent[2][2]:match("^U1;"), "hello answered after the 10 s gap")
    msg("U1;ROGUE;12;fur_snow;;;h=nonexistent_hat", "Bob-OtherRealm")
    check(TCF:PartyCount() == 2 and near(TCF:PartyTapMult(), 1.3) and row.cells[2]:IsShown(), "second friend: +30%")
    for _, t in ipairs({ "garbage", "H1;NOTACLASS;5;;;;", "H1;MAGE;abc;;;;", "H1;MAGE;0;;;;", "H1;MAGE;5;fur|cffff;;;", "H2;MAGE;5;;;;",
      "H1;MAGE;5;;;;" .. string.rep("h=x,", 80), "" }) do msg(t, "Mallory-Forever") end
    msg("H1;MAGE;5;;;;", "Eve-Forever", "WHISPER"); msg("H1;MAGE;5;;;;", "Eve-Forever", "GUILD")
    msg("H1;MAGE;5;;;;", "Eve-Forever", "PARTY", "OtherAddon"); msg("H1;MAGE;5;;;;", "Proftest-Forever")
    msg("H1;MAGE;5;;;;", _SECRET); msg(_SECRET, "Eve-Forever")
    _fire("CHAT_MSG_ADDON", _SECRET, "H1;MAGE;5;;;;", "PARTY", "Eve-Forever")
    check(TCF:PartyCount() == 2, "malformed, secret and foreign messages are ignored")
    -- your own messages never add your own cat, however the sender name arrives
    for _, me in ipairs({ _charName, _charName .. "-Forever", _charName:lower() .. "-forever", _charName .. "-For ever" }) do msg("U1;MAGE;5;;;;", me) end
    check(TCF:PartyCount() == 2 and TCF.PartyIsMe(_charName .. "-Forever") and TCF.PartyIsMe(_charName .. "-Otherrealm") and not TCF.PartyIsMe("Someone-Forever"), "your own cat is never in the row (1.5.3.6: your name alone decides)")
    local g0 = ps.gold
    local got = TCF:EarnGold(100)
    check(near(got, 100 * (1 + 0.02 * ps.renown)), "Trade Gold is not boosted: " .. tostring(got))
    check(near(TCF:FoodBuff("xp"), xpAlone), "food XP buff unchanged by the party")
    -- two friends: each tap counts 1.3, 10 taps -> 13 on the tap counter, 1.3x the cat XP
    do
      local taps0, xp0, lvl0 = TCF.db.taps, TCF:CD().xp, TCF:CD().level
      for k = 1, 10 do _clock = _clock + 0.5; TCF:Tap() end
      check(TCF.db.taps - taps0 == 13, "party of 2 friends: 10 taps count as 13 (" .. (TCF.db.taps - taps0) .. ")")
      if TCF:CD().level == lvl0 then check(near(TCF:CD().xp - xp0, 10 * 1.3 * xpAlone), "party: 1.3x cat XP from taps") end
    end
    local coinsP = TCF.db.coins; TCF:AddCoins(10); check(TCF.db.coins == coinsP + 10, "direct TapCoin awards are not boosted")
    _group.party3 = { _SECRET, nil }
    _fire("GROUP_ROSTER_UPDATE"); check(TCF:PartyCount() == 2, "a secret roster name prunes nobody")
    _group.party3 = nil; _group.party2 = nil
    -- 1.5.3.6: a cat only leaves the row when it is missing twice, a few seconds apart (no blinking)
    _fire("GROUP_ROSTER_UPDATE"); check(TCF:PartyCount() == 2, "Bob missing once: still shown")
    for k = 1, 8 do _update(0.5) end
    _fire("GROUP_ROSTER_UPDATE"); check(TCF:PartyCount() == 1 and not row.cells[2]:IsShown(), "Bob left: pruned")
    _raid, _group = true, {}
    for i, n in ipairs({ "Alice", "Cara", "Dan", "Fay", "Gus", "Hal" }) do _group["raid" .. i] = { n, nil }; msg("U1;HUNTER;" .. (10 + i) .. ";;;;", n .. "-Forever", "RAID") end
    _fire("GROUP_ROSTER_UPDATE")
    check(TCF:PartyCount() == 6 and near(TCF:PartyTapMult(), 1.5), "six friends: capped at +50% (four count): " .. TCF:PartyTapMult())
    check(row.cells[4]:IsShown() and row.more:IsShown() and row.more:GetText() == "+2", "4 small cats and +2")
    check(TCF:PartyBonus() == TCF:PartyTapMult(), "old name still answers")
    _group, _raid = nil, false
    _fire("GROUP_ROSTER_UPDATE")
    check(TCF:PartyCount() == 0 and TCF:PartyBonus() == 1 and not row:IsShown(), "left the group: no bonus, no row")
    check(TCF:PartyTestInject(3) == nil, "fake party cats need test mode")
    TCF.db.ui.testMode = true
    check(TCF:PartyTestInject(3) == 3 and row:IsShown() and row.cells[3]:IsShown() and near(TCF:PartyTapMult(), 1.4), "3 fake cats: +40%")
    check(TCF:PartyTestInject(0) == 0 and not row:IsShown() and TCF:PartyBonus() == 1, "fakes cleared")
    TCF.db.ui.testMode = nil
    -- back to the main character
    TapCatForeverDB.chars["Proftest-Forever"] = nil
    login(mainChar)
    -- 10b. test mode off clears fake party cats
    do
      TCF.db.ui.testMode = true
      TCF:PartyTestInject(2)
      check(TCF:PartyCount() == 2, "fakes while in test mode")
      SlashCmdList.TAPCATFOREVER("testmode")   -- turns it off
      check(not TCF.db.ui.testMode and TCF:PartyCount() == 0 and TCF:PartyTapMult() == 1, "test mode off: fake cats gone")
    end
    -- 10b2. the Settings page: every control inside the 560 x 494 page, nothing overlapping, every
    -- setting and button still there and working
    do
      local win = TCF.window
      local L = win.settingsLayout
      check(L and #L > 30, "Settings layout recorded: " .. tostring(L and #L))
      for i, a in ipairs(L) do
        check(a.x >= 8 and a.y >= 8 and a.x + a.w <= 552 and a.y + a.h <= 486,
          "Settings: " .. a.kind .. " " .. a.label .. " stays inside the page: " .. a.x .. "," .. a.y .. " " .. a.w .. "x" .. a.h)
        for j = i + 1, #L do
          local b = L[j]
          local apart = a.x + a.w <= b.x or b.x + b.w <= a.x or a.y + a.h <= b.y or b.y + b.h <= a.y
          check(apart, "Settings: " .. a.kind .. " " .. a.label .. " overlaps " .. b.kind .. " " .. b.label)
        end
      end
      local byLabel, headings = {}, {}
      for _, a in ipairs(L) do
        if a.kind == "button" then byLabel[a.label] = a end
        if a.kind == "heading" then headings[a.label] = true end
      end
      for _, h in ipairs({ "Cat and display", "Chat and sounds", "Help and info", "Position", "Progress" }) do
        check(headings[h], "Settings heading: " .. h)
      end
      local help = { "Welcome tour", "Patch notes", "Send feedback", "Compendium" }
      for _, n in ipairs(help) do
        local a = byLabel[n]
        check(a and a.w == byLabel["Welcome tour"].w and a.y == byLabel["Welcome tour"].y, "Help and info buttons: one row, one size: " .. n)
      end
      for _, n in ipairs({ "Reset position", "Minimap icon", "Reset this character", "Reset ALL progress" }) do
        check(byLabel[n] and byLabel[n].frame.scripts.OnClick, "Settings button works: " .. n)
      end
      check(byLabel["Reset this character"].y > byLabel["Compendium"].y and byLabel["Reset ALL progress"].frame:GetText():find("ff5555", 1, true)
        and byLabel["Reset this character"].frame:GetText():find("ff5555", 1, true), "the reset buttons are red, at the bottom")
      -- every setting from before still has its checkbox, and each one flips its setting
      local want = { "shown", "locked", "clickThrough", "catOnly", "mouse", "showLevel", "showXP", "showTaps", "showCoins",
                     "popups", "sound", "racial", "chat", "chestAnim", "textAbove" }
      local have = {}
      for _, cb in ipairs(win.settingsChecks) do have[cb.key] = cb end
      check(#win.settingsChecks == #want, "Settings checkboxes: " .. #win.settingsChecks)
      local ui = TCF.db.ui
      for _, k in ipairs(want) do
        local cb = have[k]
        check(cb, "Settings checkbox for " .. k)
        local old = ui[k]
        cb:SetChecked(not old); cb.scripts.OnClick(cb)
        check(ui[k] == (not old), "the " .. k .. " checkbox flips its setting")
        ui[k] = old
      end
      win:SelectTab(win.TAB_SETTINGS)
      -- minimap button: shows what it will do, and flips the setting
      local mm = byLabel["Minimap icon"].frame
      local hid = ui.minimap.hide
      check(mm:GetText() == (hid and "Show minimap icon" or "Hide minimap icon"), "minimap button label: " .. tostring(mm:GetText()))
      mm.scripts.OnClick(mm)
      check(ui.minimap.hide == not hid and mm:GetText() == (hid and "Hide minimap icon" or "Show minimap icon"), "minimap button flips: " .. tostring(mm:GetText()))
      mm.scripts.OnClick(mm)
      check(ui.minimap.hide == hid, "minimap button flips back")
      -- Compendium button opens and closes it
      local cb = byLabel["Compendium"].frame
      cb.scripts.OnClick(cb); check(TCF.compendium and TCF.compendium:IsShown(), "Settings Compendium button opens it")
      cb.scripts.OnClick(cb); check(not TCF.compendium:IsShown(), "and closes it")
      -- sliders still set their values
      local sc = ui.scale; ui.scale = 1.25; win:RefreshSettings(); check(ui.scale == 1.25, "cat size slider keeps the value"); ui.scale = sc
      -- test mode: the shortcuts take the help line's place
      local info = win.settingsInfo
      ui.testMode = true; win:RefreshSettings()
      check(info.testBox:IsShown() and not info.help:IsShown(), "test mode: shortcuts shown, help line hidden")
      ui.testMode = nil; win:RefreshSettings()
      check(not info.testBox:IsShown() and info.help:IsShown(), "normal: help line shown, no shortcuts")
      check(info.note:GetText():find("Play with friends", 1, true), "party note: " .. tostring(info.note:GetText()))
    end
    -- 10c. starter weapon fix only touches the old starter; two-handers clear the off hand
    do
      local function oldStarter(class)
        local best
        for _, it in ipairs(TCF.WORLD_POOL[0] or {}) do
          if it.q == 2 and not it.crafted and it.req <= 5 and (it.slot == "MH" or it.slot == "1H" or it.slot == "2H" or (class == "HUNTER" and it.slot == "RANGED"))
            and TCF:GearUsable(it, class) and (not best or it.id < best.id) then best = it end
        end
        return best
      end
      local class = "MAGE"
      local eq, cd, bag = TCF:GearEquipped(class), TCF:CD(class), TCF:Bag(class)
      local saveEq = {}; for k, v in pairs(eq) do saveEq[k] = v end
      local new, old = TCF:StarterWeapon(class), oldStarter(class)
      local off
      for id, g in pairs(TCF.GEAR) do if g.slot == "HOLD" and TCF:GearUsable(g, class) then off = g; break end end
      -- a weapon the player chose is left alone
      local chosen
      for id, g in pairs(TCF.GEAR) do if g.sub == "dagger" and g.req <= 10 and TCF:GearUsable(g, class) and (not old or g.id ~= old.id) then chosen = g; break end end
      if chosen and off then
        for k in pairs(eq) do eq[k] = nil end
        eq.MAINHAND, eq.OFFHAND = chosen.id, off.id; bag[chosen.id] = 1; bag[off.id] = 1
        cd.starterFixed = nil; TCF:FixStarterWeapons()
        check(eq.MAINHAND == chosen.id and eq.OFFHAND == off.id, "starter fix leaves a chosen weapon alone")
      end
      -- wearing the old starter: swapped; a two-handed one with an off-hand item worn (the
      -- player's choice) only goes into the bag
      if old and new and old.id ~= new.id and off then
        for k in pairs(eq) do eq[k] = nil end
        eq.MAINHAND = old.id; bag[old.id] = 1
        local hadOff = old.slot ~= "2H" and off.id
        if hadOff then eq.OFFHAND = off.id; bag[off.id] = 1 end
        cd.starterFixed = nil; TCF:FixStarterWeapons()
        if new.slot == "2H" and hadOff then
          check(eq.MAINHAND == old.id and eq.OFFHAND == off.id and (bag[new.id] or 0) >= 1, "a two-handed starter waits in the bag beside a worn off-hand")
        else
          check(eq.MAINHAND == new.id, "starter fix swaps the old starter")
        end
        check((bag[old.id] or 0) >= 1, "old starter stays in the bag")
      end
      for k in pairs(eq) do eq[k] = nil end
      for k, v in pairs(saveEq) do eq[k] = v end
    end
    -- ===== Gear section (1.5.3, gear builder): starter weapons differ per class, the one-time
    -- swap off the 1.5.0-1.5.2 starter, and spare copies of a worn one-hander in Sell junk =====
    do
      local starters, seen, wantFirst = TCF:StarterWeapons(), {}, { PRIEST = "staff", SHAMAN = "axe", WARLOCK = "dagger", MAGE = "staff", DRUID = "staff" }
      for _, cl in ipairs(TCF.CLASSES) do
        local w = starters[cl.key]
        check(w and TCF:StarterWeapon(cl.key) == w, cl.key .. " has a starter weapon")
        check(not seen[w.id], cl.key .. " starter " .. w.name .. " is also " .. tostring(seen[w.id]) .. "'s")
        seen[w.id] = cl.key
        check(not w.suffix and w.q == 2 and w.req <= 10 and TCF:GearUsable(w, cl.key), cl.key .. " starter is a plain green it can use: " .. w.name)
        check(not wantFirst[cl.key] or w.sub == wantFirst[cl.key], cl.key .. " starter kind " .. w.sub)
      end
      check(starters.SHAMAN.sub ~= "mace" and starters.PRIEST.sub == "staff", "no hammer for shamans, a staff for priests")
      check(starters.MAGE.id ~= starters.PRIEST.id and starters.MAGE.id ~= starters.DRUID.id and starters.PRIEST.id ~= starters.DRUID.id, "three different staves")
      -- what 1.5.0 to 1.5.2 gave each class (read from the 1.5.2 release)
      local OLD = { WARRIOR = 18957, PALADIN = 3223, HUNTER = 8180, ROGUE = 4947, PRIEST = 3223, SHAMAN = 3223, MAGE = 9514, WARLOCK = 9603, DRUID = 9603 }
      local saved = {}
      for _, cl in ipairs(TCF.CLASSES) do
        local cd, eq, bag = TCF:CD(cl.key), TCF:GearEquipped(cl.key), TCF:Bag(cl.key)
        local s = { eq = {}, bag = {}, f1 = cd.starterFixed, f2 = cd.starterFixed2, hb = cd.hunterBow }
        for k, v in pairs(eq) do s.eq[k] = v end
        for k, v in pairs(bag) do s.bag[k] = v end
        saved[cl.key] = s
      end
      local function offFor(class)
        for _, g in ipairs(TCF.GEAR_LIST) do
          if (g.slot == "HOLD" or g.sub == "shield") and not g.crafted and TCF:GearUsable(g, class) then return g end
        end
      end
      -- every cat still wearing its old starter (with an off-hand item beside a one-hander)
      local swapped = 0
      for _, cl in ipairs(TCF.CLASSES) do
        local class = cl.key
        local cd, eq, bag = TCF:CD(class), TCF:GearEquipped(class), TCF:Bag(class)
        for k in pairs(eq) do eq[k] = nil end
        for k in pairs(bag) do bag[k] = nil end
        local old, off = TCF.GEAR[OLD[class]], offFor(class)
        bag[old.id] = 1
        eq[old.slot == "RANGED" and "RANGED" or "MAINHAND"] = old.id
        if old.slot ~= "2H" and old.slot ~= "RANGED" and off then eq.OFFHAND = off.id; bag[off.id] = 1 end
        cd.starterFixed, cd.hunterBow, cd.starterFixed2 = true, true, nil
      end
      -- what the swap must do: keep the old one when a two-hander would push out a worn off-hand
      -- item, or when the new one is weaker (except shamans: no more hammers)
      local keepOld = {}
      for _, cl in ipairs(TCF.CLASSES) do
        local class, new = cl.key, starters[cl.key]
        local eq = TCF:GearEquipped(class)
        keepOld[class] = (new.slot == "2H" and eq.OFFHAND ~= nil)
          or (class ~= "SHAMAN" and (TCF:GearUpgrade(new, class) or 0) < 0)
      end
      check(keepOld.PRIEST and keepOld.WARLOCK and not keepOld.SHAMAN and not keepOld.DRUID,
        "a priest with a held item and a warlock (a staff is stronger than the new dagger) keep theirs")
      TCF:FixStarterWeapons()
      for _, cl in ipairs(TCF.CLASSES) do
        local class = cl.key
        local cd, eq, bag = TCF:CD(class), TCF:GearEquipped(class), TCF:Bag(class)
        local old, new = TCF.GEAR[OLD[class]], starters[class]
        check(cd.starterFixed2, class .. " starter swap flag set")
        if new.id == old.id then
          check(eq[new.slot == "RANGED" and "RANGED" or "MAINHAND"] == new.id and bag[new.id] == 1, class .. " keeps its starter, nothing added")
        elseif keepOld[class] then
          check(eq.MAINHAND == old.id and bag[new.id] == 1 and bag[old.id] == 1, class .. " keeps " .. old.name .. " on, the new one in the bag")
          if old.slot ~= "2H" and offFor(class) then
            check(eq.OFFHAND == offFor(class).id, class .. ": the off-hand item stays")
          end
        else
          swapped = swapped + 1
          check(eq.MAINHAND == new.id and bag[new.id] == 1, class .. " gets its new starter " .. new.name .. ", has " .. tostring(eq.MAINHAND))
          check(bag[old.id] == 1, class .. " keeps " .. old.name .. " in the bag")
          if new.slot == "2H" then
            check(eq.OFFHAND == nil, class .. ": a two-handed starter clears the off hand")
          elseif old.slot ~= "2H" and offFor(class) then
            check(eq.OFFHAND == offFor(class).id, class .. ": the off-hand item stays beside a one-hander")
          end
        end
      end
      check(swapped == 2, "shaman and druid swap: " .. swapped)
      check(TCF:GearEquipped("HUNTER").RANGED == starters.HUNTER.id and starters.HUNTER.sub == "bow", "the hunter keeps its bow")
      -- once only: a cat that later puts the old weapon back on keeps it
      local peq = TCF:GearEquipped("PRIEST")
      peq.MAINHAND = OLD.PRIEST
      TCF:FixStarterWeapons()
      check(peq.MAINHAND == OLD.PRIEST, "the swap runs once")
      -- a weapon the player chose is left alone
      local scd, seq, sbag = TCF:CD("SHAMAN"), TCF:GearEquipped("SHAMAN"), TCF:Bag("SHAMAN")
      local chosen
      for _, g in ipairs(TCF.GEAR_LIST) do
        if g.sub == "mace" and g.slot == "1H" and g.id ~= OLD.SHAMAN and not g.crafted and TCF:GearUsable(g, "SHAMAN") then chosen = g; break end
      end
      for k in pairs(seq) do seq[k] = nil end
      for k in pairs(sbag) do sbag[k] = nil end
      seq.MAINHAND, sbag[chosen.id], sbag[OLD.SHAMAN] = chosen.id, 1, 1
      scd.starterFixed2 = nil; TCF:FixStarterWeapons()
      check(seq.MAINHAND == chosen.id and not sbag[starters.SHAMAN.id], "a chosen weapon is left alone")
      -- Sell junk: a dual-wielder keeps two copies of its worn one-hander, a third is spare
      local wsw = starters.WARRIOR
      local wcd, weq2, wbag2 = TCF:CD("WARRIOR"), TCF:GearEquipped("WARRIOR"), TCF:Bag("WARRIOR")
      for k in pairs(weq2) do weq2[k] = nil end
      for k in pairs(wbag2) do wbag2[k] = nil end
      weq2.MAINHAND, wbag2[wsw.id] = wsw.id, 2
      check(not TCF:JunkGear("WARRIOR")[wsw.id], "two copies of a worn one-hander: none are junk for a dual-wielder")
      wbag2[wsw.id] = 3
      check(TCF:JunkGear("WARRIOR")[wsw.id] == 1, "a third copy of a worn one-hander is junk")
      -- put every class back as it was
      for _, cl in ipairs(TCF.CLASSES) do
        local cd, eq, bag, s = TCF:CD(cl.key), TCF:GearEquipped(cl.key), TCF:Bag(cl.key), saved[cl.key]
        for k in pairs(eq) do eq[k] = nil end
        for k in pairs(bag) do bag[k] = nil end
        for k, v in pairs(s.eq) do eq[k] = v end
        for k, v in pairs(s.bag) do bag[k] = v end
        cd.starterFixed, cd.starterFixed2, cd.hunterBow = s.f1, s.f2, s.hb
      end
    end
    -- ===== end of Gear section =====
    -- 10d. Sell junk: gear the class can't use is junk; hand items are kept while a two-hander is worn
    do
      local class = TCF.db.class
      local bag, eq = TCF:Bag(class), TCF:GearEquipped(class)
      local unusable
      for id, g in pairs(TCF.GEAR) do if not g.crafted and not TCF:GearUsable(g, class) then unusable = g; break end end
      if unusable then
        bag[unusable.id] = 1
        local junk = TCF:JunkGear(class)
        check(junk[unusable.id] == 1, "gear the class can't use is junk")
        bag[unusable.id] = nil
      end
      local staff, oneH
      for id, g in pairs(TCF.GEAR) do
        if not g.crafted and TCF:GearUsable(g, class) then
          if g.slot == "2H" and not staff then staff = g end
          if g.slot == "1H" and not oneH then oneH = g end
        end
      end
      if staff and oneH then
        local saveMH, saveOH = eq.MAINHAND, eq.OFFHAND
        eq.MAINHAND, eq.OFFHAND = staff.id, nil; bag[staff.id] = (bag[staff.id] or 0) + 1
        bag[oneH.id] = 1
        local junk = TCF:JunkGear(class)
        check(not junk[oneH.id], "a one-hander isn't junk while a two-hander is worn")
        bag[oneH.id] = nil
        eq.MAINHAND, eq.OFFHAND = saveMH, saveOH
      end
    end
    -- 10e. first zone clear: a few hundred TapCoins, a quarter for later classes
    do
      local saved = TCF.db.zonesCleared
      TCF.db.zonesCleared = nil
      check(TCF:AdvClearCoins(1) == 200 and TCF:AdvClearCoins(2) == 250 and TCF:AdvClearCoins(#TCF.TIERS) == 200 + 50 * (#TCF.TIERS - 1), "zone clear coins scale by zone")
      TCF.db.zonesCleared = { [TCF.TIERS[2].key] = true }
      check(TCF:AdvClearCoins(2) == 62, "another class clearing Westfall gets a quarter")
      TCF.db.zonesCleared = saved
    end
    -- 10f. hovering gear shows what the cat wears in that slot beside it
    do
      local class = TCF.db.class
      local eq, bag = TCF:GearEquipped(class), TCF:Bag(class)
      local a, b
      for id, g in pairs(TCF.GEAR) do
        if g.slot == "HEAD" and not g.crafted and TCF:GearUsable(g, class) and g.req <= TCF:CD(class).level then
          if not a then a = g elseif not b and g.id ~= a.id then b = g end
        end
      end
      if a and b then
        local saveHead = eq.HEAD
        bag[a.id] = (bag[a.id] or 0) + 1; bag[b.id] = (bag[b.id] or 0) + 1
        eq.HEAD = a.id
        GameTooltip:SetOwner(UIParent, "ANCHOR_RIGHT"); TCF:GearTooltip(GameTooltip, b)
        check(TapCatForeverCompareTip1 and TapCatForeverCompareTip1:IsShown(), "hovering gear shows the worn item beside it")
        TapCatForeverCompareTip1:Hide()
        GameTooltip:SetOwner(UIParent, "ANCHOR_RIGHT"); TCF:GearTooltip(GameTooltip, a)
        check(not TapCatForeverCompareTip1:IsShown(), "no comparison when hovering the worn item itself")
        eq.HEAD = saveHead
      end
    end
    -- 10g. Equip best (Gear page): a level 30 cat with about 60 usable items in its bag puts on what
    -- raises its Power; a second run changes nothing; nothing above its level or that it can't use is
    -- worn; never a two-hander together with an off-hand
    do
      local class = TCF.db.class
      local cd, eq, bag = TCF:CD(class), TCF:GearEquipped(class), TCF:Bag(class)
      local saveLevel, saveEq, saveBag = cd.level, {}, {}
      for k, v in pairs(eq) do saveEq[k] = v end
      for k, v in pairs(bag) do saveBag[k] = v end
      cd.level = 30
      -- only the weapon it holds now, then about 60 usable items up to level 30 (a few per slot,
      -- two-handers and off-hands among them), a few above its level and a few it can't use
      local keep = eq.MAINHAND
      for k in pairs(eq) do eq[k] = nil end
      for k in pairs(bag) do bag[k] = nil end
      if keep then eq.MAINHAND = keep; bag[keep] = 1 end
      local perSlot, usable, high, unusable = {}, 0, {}, {}
      local nHigh, nBad, n2H, nOH = 0, 0, 0, 0
      for _, it in ipairs(TCF.GEAR_LIST) do
        if not it.crafted and it.req >= 5 then
          local ok = TCF:GearUsable(it, class)
          if ok and it.req <= 30 and (perSlot[it.slot] or 0) < 4 and usable < 60 then
            perSlot[it.slot] = (perSlot[it.slot] or 0) + 1; usable = usable + 1
            bag[it.id] = (bag[it.id] or 0) + 1
            if it.slot == "2H" then n2H = n2H + 1 end
            if it.slot == "HOLD" or it.slot == "OH" or it.sub == "shield" then nOH = nOH + 1 end
          elseif ok and it.req >= 45 and nHigh < 5 and not bag[it.id] then
            nHigh = nHigh + 1; high[it.id] = true; bag[it.id] = 1
          elseif not ok and it.req <= 30 and nBad < 5 and not bag[it.id] then
            nBad = nBad + 1; unusable[it.id] = true; bag[it.id] = 1
          end
        end
      end
      check(usable >= 55 and n2H > 0 and nOH > 0 and nHigh == 5 and nBad == 5, string.format("Equip best test bag: %d usable (%d two-handers, %d off-hands), %d above level, %d unusable", usable, n2H, nOH, nHigh, nBad))
      local function worn() local t = {}; for k, v in pairs(eq) do t[k] = v end; return t end
      local function same(a, b) for k, v in pairs(a) do if b[k] ~= v then return false end end; for k, v in pairs(b) do if a[k] ~= v then return false end end; return true end
      local chat0 = #_chat
      local p0 = TCF:CombatStats(class).power
      local n1, g1 = TCF:EquipBestGear(class)
      local p1 = TCF:CombatStats(class).power
      check(n1 > 0 and p1 > p0 and g1 == p1 - p0, string.format("Equip best raises Power: %d pieces, %d -> %d", n1, p0, p1))
      check(#_chat == chat0 + 1 and _chat[#_chat]:find("Equipped your best gear", 1, true) and not _chat[#_chat]:find("!", 1, true), "Equip best: one plain chat line")
      for slot, id in pairs(eq) do
        local it = TCF.GEAR[id]
        check(it and (it.req <= 30 or id == keep) and TCF:GearUsable(it, class) and not high[id] and not unusable[id], "Equip best wore " .. slot .. " " .. tostring(it and it.name))
        check(TCF.GearEquippedCount(eq, id) <= (bag[id] or 0), "Equip best wears only copies it has: " .. it.name)
      end
      local mh = eq.MAINHAND and TCF.GEAR[eq.MAINHAND]
      check(not (mh and mh.slot == "2H" and eq.OFFHAND), "Equip best never wears a two-hander with an off-hand")
      local snap = worn()
      local n2, g2 = TCF:EquipBestGear(class)
      check(n2 == 0 and g2 == 0 and same(eq, snap) and TCF:CombatStats(class).power == p1, "Equip best again changes nothing")
      check(_chat[#_chat]:find("already wearing your best gear", 1, true) and not _chat[#_chat]:find("!", 1, true), "Equip best again: " .. _chat[#_chat])
      -- a strong two-hander and a weaker one-hander with an off-hand: whichever it picks, never both
      for k in pairs(eq) do eq[k] = nil end
      for k in pairs(bag) do bag[k] = nil end
      local staff, oneH, off
      for _, it in ipairs(TCF.GEAR_LIST) do
        if not it.crafted and it.req <= 30 and TCF:GearUsable(it, class) then
          if it.slot == "2H" and (not staff or it.ilvl > staff.ilvl) then staff = it end
          if it.slot == "1H" and (not oneH or it.ilvl > oneH.ilvl) then oneH = it end
          if (it.slot == "HOLD" or it.slot == "OH" or it.sub == "shield") and (not off or it.ilvl > off.ilvl) then off = it end
        end
      end
      if staff and oneH and off then
        bag[staff.id], bag[oneH.id], bag[off.id] = 1, 1, 1
        eq.MAINHAND, eq.OFFHAND = oneH.id, off.id
        TCF:EquipBestGear(class)
        mh = eq.MAINHAND and TCF.GEAR[eq.MAINHAND]
        check(not (mh and mh.slot == "2H" and eq.OFFHAND), "two-hander or one-hander and off-hand, never both")
        eq.MAINHAND, eq.OFFHAND = staff.id, nil
        TCF:EquipBestGear(class)
        mh = eq.MAINHAND and TCF.GEAR[eq.MAINHAND]
        check(not (mh and mh.slot == "2H" and eq.OFFHAND), "starting from the two-hander too")
      end
      for k in pairs(eq) do eq[k] = nil end
      for k in pairs(bag) do bag[k] = nil end
      for k, v in pairs(saveEq) do eq[k] = v end
      for k, v in pairs(saveBag) do bag[k] = v end
      cd.level = saveLevel
    end
    -- 10h. Craft all: materials for 7 make 7 with one chat line and the crafting skill rises; at most
    -- 50 at once; a cosmetic recipe makes at most 1
    do
      local ps = TCF:ProfState()
      local craft = TCF:CraftProf()
      local saveMats, saveSkill = {}, ps.skill[craft]
      for k, v in pairs(ps.mats) do saveMats[k] = v end
      local r
      for _, rr in ipairs(TCF.RECIPES[craft]) do
        if rr.gear and rr.skill >= 100 and rr.skill <= 250 and TCF:RecipeUsable(rr) then r = rr; break end
      end
      check(r, "a gear recipe for Craft all")
      ps.skill[craft] = r.skill   -- orange: every craft gives a point
      for m, need in pairs(r.mats) do ps.mats[m] = need * 7 end
      local it = TCF:RecipeItem(r)
      local bag = TCF:Bag()
      local had = bag[it.id] or 0
      check(TCF:CraftCount(r) == 7, "materials for 7: CraftCount " .. TCF:CraftCount(r))
      -- notices: crafted gear gets one only while the window is open. Count the notices that are
      -- really drawn (LootToast.lua asks ChestCoinsText once per notice), one level below the
      -- ShowLootToast that CraftAll swaps out, so the check sees what the player would see.
      if not TCF.window then TCF:CreateWindow() end
      local winWasShown = TCF.window:IsShown()
      TCF.window:Show()
      local toasts0 = 0
      local origCoinsText = TCF.ChestCoinsText
      TCF.ChestCoinsText = function(...) toasts0 = toasts0 + 1; return origCoinsText(...) end
      for m, need in pairs(r.mats) do ps.mats[m] = need * 8 end
      check(TCF:Craft(r) and toasts0 == 1, "one Craft with the window open draws a notice (" .. toasts0 .. "), so the next check can fail")
      ps.skill[craft], toasts0 = r.skill, 0
      local had1 = bag[it.id] or 0
      local chat0 = #_chat
      local made = TCF:CraftAll(r)
      TCF.ChestCoinsText = origCoinsText
      if not winWasShown then TCF.window:Hide() end
      check(made == 7 and (bag[it.id] or 0) == had1 + 7, "Craft all made " .. made)
      -- (1.6 skill-up curve: the first 5 always give a point, the next ones half the time)
      check(#_chat == chat0 + 1 and _chat[#_chat]:find("Crafted 7 x", 1, true) and _chat[#_chat]:find("skill +" .. (ps.skill[craft] - r.skill), 1, true) and not _chat[#_chat]:find("!", 1, true),
        "Craft all: one chat line: " .. tostring(_chat[#_chat]))
      check(toasts0 == 0, "Craft all: no notice per item")
      check(ps.skill[craft] >= r.skill + 5 and ps.skill[craft] <= r.skill + 7, "Craft all: the crafting skill rises (" .. ps.skill[craft] .. ")")
      for m in pairs(r.mats) do check(ps.mats[m] == 0, "Craft all used the materials") end
      check(TCF:CraftCount(r) == 0 and TCF:CraftAll(r) == 0 and #_chat == chat0 + 1, "nothing left: nothing made, nothing said")
      for m, need in pairs(r.mats) do ps.mats[m] = need * 80 end
      check(TCF:CraftCount(r) == TCF.CRAFT_ALL_MAX and TCF.CRAFT_ALL_MAX == 50, "at most 50 at once")
      bag[it.id] = had > 0 and had or nil
      -- a cosmetic recipe: one at most, whatever the materials
      local cr
      for _, rr in ipairs(TCF.RECIPES[craft]) do
        if rr.cosmetic and (rr.skill or 1) <= r.skill then cr = rr; break end
      end
      if cr then
        local cit = TCF.ITEMS[cr.item]
        local owned = TCF.db.owned[cit.id]
        TCF.db.owned[cit.id] = nil
        for m, need in pairs(cr.mats) do ps.mats[m] = need * 5 end
        check(TCF:CraftCount(cr) == 1, "a cosmetic recipe counts 1: " .. TCF:CraftCount(cr))
        check(TCF:CraftAll(cr) == 1 and TCF.db.owned[cit.id], "Craft all makes the cosmetic once")
        for m, need in pairs(cr.mats) do check(ps.mats[m] == need * 4, "and uses one set of materials") end
        check(TCF:CraftCount(cr) == 0, "then it can't be made again")
        TCF.db.owned[cit.id] = owned
      end
      for k in pairs(ps.mats) do ps.mats[k] = nil end
      for k, v in pairs(saveMats) do ps.mats[k] = v end
      ps.skill[craft] = saveSkill
      print(string.format("Equip best and Craft all (%s, cosmetic %s): all checks passed", r.skill and (craft .. " " .. r.skill) or craft, cr and cr.item or "none"))
    end
    -- 11. What's new strip and Patch notes
    do
      local realVersion = TCF.version
      -- the newest version; a fix release (no highlight) shows its big update's news
      local hl
      for _, n in ipairs(TCF.NEWS) do if n.highlight then hl = n; break end end
      TCF.version = TCF.NEWS[1].version
      check(hl and TCF:CurrentNews() == hl, "current version has news")
      TCF.db.newsSeen, TCF.db.newsShows = nil, nil
      if not TCF.window then TCF:CreateWindow() end
      TCF.window:Hide(); TCF.window:Show(); TCF:CheckNews()
      check(TapCatForeverNewsStrip and TapCatForeverNewsStrip:IsShown(), "strip shows after a big update")
      check(TapCatForeverNewsStrip.text:GetText():find("What's new in", 1, true), "strip text")
      TCF:MarkNewsSeen()
      check(not TapCatForeverNewsStrip:IsShown() and not TCF:NewsPending(), "dismissed: gone")
      TCF:CheckNews(); check(not TapCatForeverNewsStrip:IsShown(), "stays gone after dismissing")
      TCF.db.newsSeen, TCF.db.newsShows = nil, nil
      for k = 1, 3 do TCF:CheckNews() end
      check(not TCF:NewsPending(), "gone after being shown 3 times")
      TCF:ShowPatchNotes()
      check(TapCatForeverPatchNotes and TapCatForeverPatchNotes:IsShown() and TapCatForeverPatchNotes.body:GetText():find("Version " .. TCF.NEWS[1].version, 1, true), "patch notes open on the newest version")
      TapCatForeverPatchNotes:ShowVersion(#TCF.NEWS)
      check(TapCatForeverPatchNotes.body:GetText():find("Version " .. TCF.NEWS[#TCF.NEWS].version, 1, true), "older versions readable")
      TapCatForeverPatchNotes:Hide()
      SlashCmdList.TAPCATFOREVER("news")
      check(TapCatForeverPatchNotes:IsShown(), "/tcf news opens the notes")
      TapCatForeverPatchNotes:Hide()
      TCF.version = realVersion
    end
    -- 11. chests (1.5.1): real legendaries, the raid-only Raider's Hoard, blue in the pouch at every level
    do
      local hoard = TCF.CHEST_BY_KEY.raid
      check(hoard and not hoard.cost and hoard.gearOnly and hoard.raidLoot and (hoard.legendary or 0) > 0, "Raider's Hoard: never sold, always raid gear")
      local coins0 = TCF.db.coins
      check(TCF:OpenChest("raid") == nil and TCF.db.coins == coins0, "a Raider's Hoard can't be bought")
      -- legendaries: real ones only (no placeholder copies), one for every class
      local legs = TCF:Legendaries()
      check(#legs >= 6, "legendaries in the loot pools: " .. #legs)
      for _, it in ipairs(legs) do check(it.q == 5 and not it.crafted and not it.name:find("(", 1, true), "real legendary: " .. it.name) end
      for _, cl in ipairs(TCF.CLASSES) do
        local it = TCF:RollLegendary(cl.key)
        check(it and it.q == 5 and TCF:GearUsable(it, cl.key), cl.key .. " can get a legendary")
      end
      -- odds shown in tooltips add up and match the rules
      for _, ch in ipairs(TCF.CHESTS) do
        local sum = 0
        for _, o in ipairs(TCF:ChestOdds(ch)) do sum = sum + o[2] end
        check(math.abs(sum - 100) < 1e-6, ch.key .. " odds add up: " .. sum)
      end
      -- only real Classic legendaries: Blizzard's placeholder Ashbringer and Burning Crusade's
      -- Andonisus are known but never drop, and a class gets the ones made for it
      check(TCF.GEAR[22736] and TCF.GEAR[22736].retired and TCF.GEAR[50442] and TCF.GEAR[50442].retired,
        "Andonisus and the Ashbringer placeholder never drop")
      for _, it in ipairs(legs) do check(it.id ~= 22736 and it.ilvl <= 92, "a Classic legendary: " .. it.name) end
      for _, list in pairs(TCF.WORLD_POOL) do for _, it in ipairs(list) do check(it.id ~= 22736, "Andonisus is not world loot") end end
      for _, it in ipairs(TCF:LegendariesFor("MAGE")) do check(it.name:find("^Atiesh"), "a Mage's legendaries are Atiesh: " .. it.name) end
      for k = 1, 60 do
        local it = TCF:RollLegendary("MAGE")
        check(it and it.name:find("^Atiesh"), "a Mage's Legendary roll gives Atiesh: " .. tostring(it and it.name))
      end
      -- the Heroic Cache's skin odds only show while there is a shop skin left to find
      do
        local owned, added = TCF.db.owned, {}
        local function heroicOdds()
          local sum, skinLine = 0, false
          for _, o in ipairs(TCF:ChestOdds(TCF.CHEST_BY_KEY.heroic)) do
            sum = sum + o[2]
            if o[1]:find("skin", 1, true) then skinLine = true end
          end
          return sum, skinLine
        end
        local hadSkins = #TCF:UnownedShopSkins() > 0
        local _, skinBefore = heroicOdds()
        check(skinBefore == hadSkins, "Heroic Cache skin odds show while a shop skin is left")
        for _, it in ipairs(TCF:UnownedShopSkins()) do owned[it.id] = true; added[#added + 1] = it.id end
        local sum, skinLine = heroicOdds()
        for _, id in ipairs(added) do owned[id] = nil end
        check(not skinLine and math.abs(sum - 100) < 1e-6, "no cat skin odds once every shop skin is owned: " .. sum)
      end
      -- earning a chest: its name in the colour of its usual gear, a/an, no exclamation marks
      do
        local printed, origPrint = {}, TCF.Print
        TCF.Print = function(_, msg) printed[#printed + 1] = msg end
        local k1, k2 = TCF.db.keys.raid or 0, TCF.db.keys.strong or 0
        TCF:AwardChest("raid", "Test"); TCF:AwardChest("strong", "Test")
        TCF.Print = origPrint
        TCF.db.keys.raid, TCF.db.keys.strong = k1, k2
        check(printed[1] and printed[1]:find("a |c" .. TCF.RARITY[4].hex .. "Raider's Hoard", 1, true) and not printed[1]:find("!", 1, true),
          "a Raider's Hoard is announced in Epic purple: " .. tostring(printed[1]))
        check(printed[2] and printed[2]:find("an |c" .. TCF.RARITY[2].hex .. "Adventurer's Strongbox", 1, true) and not printed[2]:find("!", 1, true),
          "an Adventurer's Strongbox is announced in green: " .. tostring(printed[2]))
      end
      -- the Compendium: where legendaries come from, and the Hoard never holds cosmetics
      do
        local thunder = TCF.GEAR[19019]
        local how = table.concat(TCF:HowToGet(thunder), " / ")
        check(how:find("1 in 500 Heroic Caches", 1, true) and how:find("1 in 100 Raider's Hoards", 1, true) and not how:find("World drop", 1, true),
          "a legendary's Compendium lines: " .. how)
        how = table.concat(TCF:HowToGet(TCF.GEAR[50442]), " / ")
        check(how:find("Removed: a leftover test item", 1, true) and not how:find("random bonus", 1, true), "a placeholder is gone: " .. how)
        local epicLoot
        for _, it in ipairs(TCF.ITEM_LIST) do if it.source == "loot" and it.rarity == 4 then epicLoot = it; break end end
        if epicLoot then
          how = table.concat(TCF:HowToGet(epicLoot), " / ")
          check(how:find("Heroic Cache", 1, true) and not how:find("Raider's Hoard", 1, true), "a Hoard never holds cosmetics: " .. how)
        end
      end
      local tip = tipText(function() TCF:ChestOddsTooltip(GameTooltip, TCF.CHEST_BY_KEY.heroic, true) end)
      check(tip:find("Legendary gear|r 0.2%", 1, true), "Heroic Cache shows its real Legendary odds: " .. tip)
      tip = tipText(function() TCF:ChestOddsTooltip(GameTooltip, hoard) end)
      check(tip:find("Epic gear|r 99%", 1, true) and tip:find("Legendary gear|r 1%", 1, true) and not tip:find("Cosmetic", 1, true), "Raider's Hoard odds: " .. tip)
      -- opening Raider's Hoards: always gear, Epic raid boss loot (or a real legendary) the class can use
      local skinRoll = TCF.RollSkinSource
      TCF.RollSkinSource = function() end
      TCF:SetClass("WARRIOR")
      local cd = TCF:CD()
      local oldLevel, oldTier, oldBest = cd.level, cd.adv.tier, cd.adv.best
      cd.level = 60
      local raids, firstRaid = {}, nil
      for ti, t in ipairs(TCF.TIERS) do if t.raid then raids[ti] = true; firstRaid = firstRaid or ti end end
      local hoards0 = TCF.db.stats.hoards or 0
      TCF.db.keys.raid = 150
      TCF.openingAll = true
      local nLeg = 0
      for k = 1, 150 do
        local g = TCF:OpenChest("raid", true)
        local lc = TCF.lastChest
        check(lc and lc.gear and lc.gear == g, "Raider's Hoard holds gear")
        check(g.q == 5 or (g.q == 4 and g.tier == firstRaid and g.boss > 0), "a new cat's Hoard is Epic boss loot from the first raid: " .. g.name .. " tier " .. tostring(g.tier))
        check(TCF:GearUsable(g, "WARRIOR"), "Hoard gear fits the class: " .. g.name)
        if g.q == 5 then nLeg = nLeg + 1 end
      end
      check(TCF.db.keys.raid == 0 and (TCF.db.stats.hoards or 0) == hoards0 + 150, "hoards counted")
      TCF:CheckAchievements()
      check(TCF.db.achievements.hoard1, "opening a Raider's Hoard earns Spoils of the Raid")
      -- a cat deep in the raids gets loot from every raid it has reached
      cd.adv.tier, cd.adv.best = #TCF.TIERS, #TCF.TIERS * 100 + 1
      local seenTier = {}
      for k = 1, 300 do
        local g = TCF:ChestGear(hoard, 4)
        check(g and g.q == 4 and raids[g.tier], "raid epic")
        seenTier[g.tier] = true
      end
      local nSeen = 0
      for _ in pairs(seenTier) do nSeen = nSeen + 1 end
      check(nSeen >= 4, "Hoards from many raids once they are reached: " .. nSeen)
      -- the Heroic Cache: a real legendary when its tiny roll hits
      local heroic = TCF.CHEST_BY_KEY.heroic
      local leg0 = heroic.legendary
      heroic.legendary = 1
      TCF.db.keys.heroic = (TCF.db.keys.heroic or 0) + 5
      local gotLeg, skins = 0, 0
      for k = 1, 5 do
        local g = TCF:OpenChest("heroic", true)
        if TCF.lastChest and TCF.lastChest.gear and TCF.lastChest.gear.q == 5 then gotLeg = gotLeg + 1 end
        -- the Heroic Cache's own small skin chance comes before the Legendary roll (that made this flaky)
        if TCF.lastChest and TCF.lastChest.skin then skins = skins + 1 end
      end
      heroic.legendary = leg0
      check(gotLeg >= 4 - skins and gotLeg + skins >= 4, "a hit Legendary roll gives a real legendary: " .. gotLeg .. " (skins " .. skins .. ")")
      TCF.openingAll = nil
      -- the loot box celebrates a legendary, and only a legendary
      local lr = TCF.lootReveal or TCF:CreateLootReveal()
      lr:ShowGear(legs[1], true, "Heroic Cache", "heroic")
      check(lr.legendRays:IsShown() and lr.legendGlow:IsShown() and lr.status:GetText():find("Legendary", 1, true), "legendary celebration")
      for i = 1, 5 do _update(0.1) end
      lr:ShowGear(TCF:RollRaidEpic("WARRIOR"), true, "Raider's Hoard", "raid")
      check(not lr.legendRays:IsShown() and not lr.legendGlow:IsShown(), "no celebration for an Epic")
      lr:Hide()
      -- the reel for a Hoard shows raid epics
      TCF.db.ui.chestAnim = true
      TCF.db.keys.raid = 1
      TCF.forceReveal = true
      TCF:OpenChest("raid", true)
      TCF.forceReveal = nil
      check(TapCatForeverReel and TapCatForeverReel:IsShown(), "the Hoard reel plays")
      for i = 1, 40 do _update(0.1) end
      if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
      -- the Cat Treat Pouch's blue roll finds blue at every level (level 9 has none of its own)
      for _, lvl in ipairs({ 1, 5, 9, 14, 23, 37, 52, 60 }) do
        cd.level = lvl
        cd.adv.tier, cd.adv.best = 1, 0
        for k = 1, 15 do
          -- 1.5.3.1: blue when there is a blue within 3 levels of the cat, else one quality lower
          local g = TCF:ChestGear(TCF.CHEST_BY_KEY.pouch, 3)
          local want = #TCF:ChestGearPool(nil, lvl, 3) > 0 and 3 or 2
          check(g and g.q == want and (g.req or 0) <= lvl + 3, "a blue pouch roll at level " .. lvl .. ": " .. (g and (g.name .. " q" .. g.q .. " req " .. (g.req or 0)) or "nothing"))
        end
      end
      cd.level, cd.adv.tier, cd.adv.best = oldLevel, oldTier, oldBest
      -- Treasure Bag: room for every kind of chest, the Hoard included; the Shop sells only 3
      for _, ch in ipairs(TCF.CHESTS) do TCF.db.keys[ch.key] = 1 end
      -- rebuild the bag with sizes and points recorded (the mock frames don't keep them)
      local origCF = CreateFrame
      CreateFrame = function(...)
        local f = origCF(...)
        f.SetSize = function(s, w, h) s.w, s.h = w, h end
        f.SetPoint = function(s, ...) s.pt = { ... } end
        return f
      end
      if TCF.bag then TCF.bag:Hide() end
      TCF.bag = nil
      local okBag, bag = pcall(TCF.CreateBag, TCF)
      CreateFrame = origCF
      check(okBag, "Treasure Bag builds: " .. tostring(bag))
      bag:Show(); bag:Refresh()
      local shown, lowest = 0, 0
      for _, r in ipairs(bag.rows) do
        if r:IsShown() then shown = shown + 1; lowest = math.min(lowest, r.pt[3] - r.h) end
      end
      check(shown == #TCF.CHESTS and #TCF.CHESTS == 5, "Treasure Bag shows 5 kinds of chest: " .. shown)
      check(-lowest + 14 + 22 + 4 <= bag.h, "the 5th row clears the Open everything button: " .. lowest .. " " .. tostring(bag.h))
      -- rows never overlap: each starts below the one above it
      local prevBottom
      for _, r in ipairs(bag.rows) do
        if prevBottom then check(r.pt[3] <= prevBottom, "Treasure Bag rows don't overlap: " .. r.pt[3] .. " " .. prevBottom) end
        prevBottom = r.pt[3] - r.h
      end
      for i, ch in ipairs(TCF.CHESTS) do
        if ch.key == "raid" or ch.key == "dungeon" then
          tip = tipText(function() bag.rows[i].scripts.OnEnter(bag.rows[i]) end)
          check(tip:find(ch.name, 1, true), ch.name .. " row tooltip: " .. tip)
        end
      end
      TCF:OpenAllChests()
      bag:Hide()
      for _, ch in ipairs(TCF.CHESTS) do check((TCF.db.keys[ch.key] or 0) == 0, "opened every chest: " .. ch.key) end
      if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
      tip = tipText(function() bag.rows[1].all.scripts.OnEnter(bag.rows[1].all) end)
      check(tip:find("Open all Cat Treat Pouches", 1, true), "All button plural: " .. tip)
      -- opening a batch of Hoards where the first shown is a Legendary ends on the legendary sound
      do
        local legChance, sounds, origSound = TCF.CHEST_BY_KEY.raid.legendary, {}, TCF.PlaySound
        TCF.CHEST_BY_KEY.raid.legendary = 1
        TCF.db.keys.raid = 3
        TCF.PlaySound = function(_, kind) sounds[#sounds + 1] = kind end
        TCF:OpenAllChests("raid")
        TCF.PlaySound, TCF.CHEST_BY_KEY.raid.legendary = origSound, legChance
        if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
        check(sounds[#sounds] == "legendary", "a batch with a Legendary ends on the legendary sound: " .. table.concat(sounds, ","))
      end
      -- the raid expedition tooltips name their Hoard chance
      do
        local first = #_frames + 1
        local page = CreateFrame("Frame")
        local okE, errE = pcall(TCF.UI.Builders.expeditions, page, { party = {}, Refresh = function() end })
        check(okE, "expeditions page builds: " .. tostring(errE))
        local naxxTip
        for i = first, #_frames do
          local f = _frames[i]
          if f.exp == TCF.EXPEDITION_BY_KEY.naxx and f.scripts.OnEnter then naxxTip = tipText(function() f.scripts.OnEnter(f) end) end
        end
        check(naxxTip and naxxTip:find("Also a 25% chance of a Raider's Hoard.", 1, true), "Naxxramas tooltip shows its Hoard chance: " .. tostring(naxxTip))
      end
      -- sources: Adventure raid bosses and raid clears, raid expeditions
      local paid = {}
      local origAward = TCF.AwardChest
      TCF.AwardChest = function(self, key, src, ...) paid[#paid + 1] = key; return origAward(self, key, src, ...) end
      local zg = firstRaid
      cd.adv.tier, cd.adv.stage = zg, 1
      cd.adv.chestClock = 1e6
      -- (adv track: first kills now give their own chests, so these are repeat kills)
      cd.adv.cleared[TCF.AdvStageCode(zg, 1)], cd.adv.cleared[TCF.AdvStageCode(2, 1)] = true, true
      TCF:AdvMobKilled({ name = "High Priest Venoxis", boss = 1, level = 63 })
      cd.adv.tier, cd.adv.stage = 2, 1
      cd.adv.chestClock = 1e6
      TCF:AdvMobKilled({ name = "Slark", boss = 1, level = 12 })
      check(paid[1] == "raid" and paid[2] == "pouch", "raid bosses drop a Raider's Hoard, zone bosses a Pouch: " .. table.concat(paid, ","))
      -- trash kills ask Gear.lua for a small find when it has one
      local found = {}
      local origFind = TCF.TrashSmallFind
      TCF.TrashSmallFind = function(self, m, t) found[#found + 1] = { m, t } end
      TCF:AdvMobKilled({ name = "Riverpaw Gnoll", level = 11 })
      check(#found == 1 and found[1][1].name == "Riverpaw Gnoll" and found[1][2] == TCF.TIERS[2], "trash kill calls TrashSmallFind(m, t)")
      TCF.TrashSmallFind = nil
      TCF:AdvMobKilled({ name = "Riverpaw Gnoll", level = 11 })   -- and works without it
      TCF.TrashSmallFind = origFind
      paid = {}
      local st = TCF.db.expeditions or { active = {} }
      TCF.db.expeditions = st
      local mc = TCF.EXPEDITION_BY_KEY.mc
      local h0 = mc.hoard
      mc.hoard = 1
      table.insert(st.active, { key = "mc", members = { "WARRIOR", "MAGE", "PRIEST" }, start = 0, finish = 0, power = 1e9, chance = 1 })
      TCF:ClaimExpedition(#st.active)
      mc.hoard = h0
      local gotHoard = false
      for _, k in ipairs(paid) do if k == "raid" then gotHoard = true end end
      check(gotHoard, "a raid expedition can bring home a Raider's Hoard: " .. table.concat(paid, ","))
      check(TCF.EXPEDITION_BY_KEY.sm.hoard == nil, "only raid expeditions bring Hoards")
      TCF.AwardChest = origAward
      TCF.RollSkinSource = skinRoll
      print(string.format("chests: Raider's Hoard ok (%d legendaries in 150), %d legendaries, %d raids reached", nLeg, #legs, nSeen))
    end
    -- 12. more gear (1.5.1): legendaries only from the big chests, the Raider's Hoard, white gear,
    -- random-suffix greens, small finds in Adventure, and the pages that show them
    -- (a function of its own: Lua 5.1 allows 200 locals per function)
    ;(function()
      local hoard, heroic = TCF.CHEST_BY_KEY.raid, TCF.CHEST_BY_KEY.heroic
      -- 12a. what the loot watch (set up at the start) saw over the whole run
      check(#_lootWatch.bad == 0, "loot rules broken during the run: " .. table.concat(_lootWatch.bad, "; ", 1, math.min(6, #_lootWatch.bad)))
      check(_lootWatch.chestGear >= 100, "gear from chests during the run: " .. _lootWatch.chestGear)
      login("Lootcheck")
      TCF.db.ui.chat = true
      TCF:SetClass("WARRIOR")
      local cd = TCF:CD()
      local adv = cd.adv
      cd.level = 60
      local skinChance, skinRoll, gearChance = TCF.CHEST_SKIN_CHANCE, TCF.RollSkinSource, TCF.CHEST_GEAR_CHANCE
      TCF.CHEST_SKIN_CHANCE, TCF.RollSkinSource = 0, function() end
      TCF.openingAll = true
      if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
      local function openMany(key, n)
        local got = {}
        TCF.db.keys[key] = (TCF.db.keys[key] or 0) + n
        for k = 1, n do
          TCF:OpenChest(key, true)
          local lc = TCF.lastChest
          got[#got + 1] = lc and lc.gear or false
        end
        return got
      end
      local function gname(g) return g and (g.name .. " (q" .. g.q .. ", id " .. g.id .. ")") or "a cosmetic" end

      -- 12b. real legendaries: only a Heroic Cache or a Raider's Hoard holds one, and only real ones
      local real = {}
      for _, it in ipairs(TCF:Legendaries()) do real[it] = true end
      check(heroic.legendary >= 0.001 and heroic.legendary <= 0.005, "Heroic Cache Legendary chance about 1 in 500: " .. heroic.legendary)
      check(hoard.legendary >= 0.005 and hoard.legendary <= 0.02, "Raider's Hoard Legendary chance about 1 in 100: " .. hoard.legendary)
      for _, cl in ipairs(TCF.CLASSES) do
        for k = 1, 80 do
          local it = TCF:RollLegendary(cl.key)
          check(it and real[it], cl.key .. " Legendary roll gave something that is not a real legendary: " .. gname(it))
        end
      end
      local leg0, hleg0 = heroic.legendary, hoard.legendary
      heroic.legendary, hoard.legendary = 1, 1   -- force the Legendary roll
      for _, cl in ipairs(TCF.CLASSES) do
        TCF:SetClass(cl.key); TCF:CD().level = 60
        for _, key in ipairs({ "heroic", "raid" }) do
          for _, g in ipairs(openMany(key, 3)) do
            check(g and g.q == 5 and real[g] and TCF:GearUsable(g, cl.key), key .. " with its Legendary roll forced, " .. cl.key .. " got " .. gname(g))
          end
        end
      end
      -- no Legendary roll: even the top rarity roll of every chest is an Epic, never a Legendary
      heroic.legendary, hoard.legendary = 0, 0
      local origRarity = TCF.RollRarity
      TCF.RollRarity = function() return 5 end
      TCF:SetClass("WARRIOR"); cd = TCF:CD(); adv = cd.adv
      for _, ch in ipairs(TCF.CHESTS) do
        if ch.key ~= "heroic" and ch.key ~= "raid" then check((ch.legendary or 0) == 0, ch.key .. " has no Legendary roll") end
        for _, g in ipairs(openMany(ch.key, 40)) do
          check((not g and not ch.gearOnly) or (g and g.q == 4), ch.name .. " top rarity roll gave " .. gname(g))
        end
      end
      TCF.RollRarity = origRarity
      heroic.legendary, hoard.legendary = leg0, hleg0
      -- natural odds: plenty of Pouches and Strongboxes, not one Legendary
      for _, key in ipairs({ "pouch", "strong" }) do
        for _, g in ipairs(openMany(key, 300)) do check(not g or g.q <= 4, key .. " gave a Legendary: " .. gname(g)) end
      end

      -- 12c. the Raider's Hoard: never in the Shop, always in the Treasure Bag, and where it comes from
      local shopNames = {}
      for i = _shopScan[1] + 1, _shopScan[2] do
        local f = _frames[i]
        if f.kind == "FontString" and type(f.text) == "string" then shopNames[f.text] = true end
      end
      for _, ch in ipairs(TCF.CHESTS) do
        check((shopNames[ch.name] and true or false) == (ch.cost ~= nil), ch.name .. (ch.cost and " is sold in the Shop" or " is not in the Shop"))
      end
      check(not hoard.cost, "the Raider's Hoard has no price")
      local inSources = false
      for _, line in ipairs(TCF.CHEST_SOURCES) do if line:find("^Raider's Hoard") then inSources = true end end
      check(inSources and TCF.CHEST_BAG_TEXT and TCF.CHEST_BAG_TEXT.raid, "Treasure Bag texts list the Raider's Hoard")
      TCF.db.keys.raid = 1
      if TCF.bag then TCF.bag:Hide() end
      TCF.bag = nil
      local bag = TCF:CreateBag(); bag:Show(); bag:Refresh()
      local hoardRow = false
      for i, r in ipairs(bag.rows) do if r.chest and r.chest.key == "raid" and r:IsShown() then hoardRow = true end end
      check(hoardRow, "the Treasure Bag shows a row for the Raider's Hoard")
      bag:Hide()
      TCF.db.keys.raid = 0
      local paid = {}
      local origAward = TCF.AwardChest
      TCF.AwardChest = function(self, key, src, ...) paid[#paid + 1] = key .. "@" .. tostring(src); return origAward(self, key, src, ...) end
      local firstRaid
      for ti, t in ipairs(TCF.TIERS) do if t.raid and not firstRaid then firstRaid = ti end end
      local function firstClear(ti)
        local t = TCF.TIERS[ti]
        local stage = TCF:AdvStages(ti)
        adv.tier, adv.stage = ti, stage
        adv.cleared[TCF.AdvStageCode(ti, stage)] = nil
        TCF:AdvMobKilled({ name = t.bosses[#t.bosses][1], boss = #t.bosses, final = true, level = 61 })
        return paid[#paid] or ""
      end
      check(firstClear(firstRaid):find("^raid@"), "the first clear of a raid gives a Raider's Hoard: " .. table.concat(paid, ", "))
      check(firstClear(1):find("^strong@"), "the first clear of a zone gives a Strongbox: " .. table.concat(paid, ", "))
      adv.tier, adv.stage, adv.chestClock = firstRaid, 1, 1e6
      TCF:AdvMobKilled({ name = TCF.TIERS[firstRaid].bosses[1][1], boss = 1, level = 63 })
      check(paid[#paid]:find("^raid@"), "an Adventure raid boss's chest is a Raider's Hoard: " .. paid[#paid])
      local nHoardTrips = 0
      for _, e in ipairs(TCF.EXPEDITIONS) do
        local t = e.tier and TCF.TIERS[e.tier]
        if e.hoard then
          nHoardTrips = nHoardTrips + 1
          check(t and t.raid and e.hoard > 0 and e.hoard <= 0.5, e.key .. ": only raid expeditions bring Raider's Hoards, at a fair rate: " .. e.hoard)
        end
      end
      check(nHoardTrips >= 3, "raid expeditions with a Raider's Hoard chance: " .. nHoardTrips)
      TCF.AwardChest = origAward
      adv.tier, adv.stage = 1, 1

      -- 12d. white gear: in the world pools only, plain armor or damage, never from a chest
      local whites, whiteBand = 0, {}
      local BONUS = { "str", "agi", "sta", "int", "spi", "sp", "heal", "ap", "rap", "def", "critr", "hitr", "crit", "hit", "mp5", "dodger" }
      for b, list in pairs(TCF.WORLD_POOL) do
        for _, it in ipairs(list) do
          if it.q == 1 then
            whites = whites + 1; whiteBand[b] = (whiteBand[b] or 0) + 1
            local st = TCF.GearStats(it)
            check(not it.crafted and it.tier == 0 and it.boss == 0 and ((st.arm or 0) > 0 or (st.dps or 0) > 0), "white world gear " .. it.name)
            for _, k in ipairs(BONUS) do check(not st[k], "white gear has no bonus stats: " .. it.name .. " " .. k) end
          end
        end
      end
      check(whites >= 500 and (whiteBand[0] or 0) >= 20 and (whiteBand[1] or 0) >= 20 and (whiteBand[2] or 0) >= 20, "white gear in the world pools: " .. whites)
      for _, l in pairs(TCF.TIER_POOL) do for _, it in ipairs(l) do check(it.q >= 2, "white gear in a zone pool: " .. it.name) end end
      for _, bl in pairs(TCF.BOSS_LOOT) do for _, l in pairs(bl) do for _, it in ipairs(l) do check(it.q >= 2, "white gear in boss loot: " .. it.name) end end end
      for _, cl in ipairs({ "WARRIOR", "MAGE", "ROGUE" }) do
        TCF:SetClass(cl); cd = TCF:CD(); adv = cd.adv
        for _, lvl in ipairs({ 1, 3, 6, 9, 14 }) do
          cd.level = lvl; adv.tier, adv.best = 1, 0
          for _, ch in ipairs(TCF.CHESTS) do
            for r = 1, 5 do
              for k = 1, 3 do local g = TCF:ChestGear(ch, r); check(not g or g.q >= 2, ch.key .. " rarity " .. r .. " at level " .. lvl .. " gave " .. gname(g)) end
            end
          end
          for _, g in ipairs(openMany("pouch", 12)) do check(not g or g.q >= 2, "a level " .. lvl .. " Pouch gave " .. gname(g)) end
          local w = TCF:RollWorldLoot(lvl, cl, { 0, 0, 0, common = 1 })
          check(w and w.q == 1, "a white world roll at level " .. lvl .. " gives white gear: " .. gname(w))
          for k = 1, 20 do
            local g = TCF:RollWorldLoot(lvl, cl)
            check(not g or g.q >= 2, "an ordinary world roll gave white gear: " .. gname(g))
          end
        end
      end

      -- 12e. random-suffix greens: names, stats and ids that never change
      local SUF = { "of the Monkey", "of the Bear", "of the Eagle", "of the Owl", "of the Tiger", "of the Falcon", "of the Wolf",
        "of the Boar", "of the Gorilla", "of the Whale", "of Strength", "of Agility", "of Stamina", "of Intellect", "of Spirit",
        "of Healing", "of Fiery Wrath", "of Power", "of Marksmanship", "of Defense" }
      local SUF_STATS = { { "agi", "sta" }, { "str", "sta" }, { "sta", "int" }, { "int", "spi" }, { "str", "agi" }, { "agi", "int" },
        { "agi", "spi" }, { "str", "spi" }, { "str", "int" }, { "sta", "spi" }, { "str" }, { "agi" }, { "sta" }, { "int" }, { "spi" },
        { "heal" }, { "sp" }, { "ap" }, { "rap" }, { "def" } }
      check(TCF.SUFFIX_ID_BASE == 10000000, "suffix id base")
      for k, name in ipairs(SUF) do check(TCF.GEAR_SUFFIXES[k] == name, "suffix " .. k .. " is still " .. name .. " (saved ids depend on it): " .. tostring(TCF.GEAR_SUFFIXES[k])) end
      local inPool = {}
      for _, l in pairs(TCF.WORLD_POOL) do for _, it in ipairs(l) do inPool[it] = true end end
      for _, l in pairs(TCF.TIER_POOL) do for _, it in ipairs(l) do inPool[it] = true end end
      for _, bl in pairs(TCF.BOSS_LOOT) do for _, l in pairs(bl) do for _, it in ipairs(l) do inPool[it] = true end end end
      local nSuf, nRetired, seenId, perBase = 0, 0, {}, {}
      for _, it in ipairs(TCF.GEAR_LIST) do
        check(not seenId[it.id] and TCF.GEAR[it.id] == it, "gear id used once: " .. it.id); seenId[it.id] = true
        if it.suffix then
          nSuf = nSuf + 1
          local b = TCF.GEAR[it.base]
          check(it.id == TCF.SUFFIX_ID_BASE + it.base * 100 + it.suffix and it.suffix >= 1 and it.suffix <= 99, "suffix id scheme: " .. it.id)
          check(b and b.retired and not b.suffix and it.name == b.name .. " " .. SUF[it.suffix], "suffix name: " .. it.name)
          check(it.q == 2 and it.icon == b.icon and it.ilvl == b.ilvl and it.req == b.req and it.slot == b.slot and it.sub == b.sub
            and it.cls == b.cls and not it.crafted and not it.retired, "a suffix item copies its base: " .. it.name)
          local st, bst = TCF.GearStats(it), TCF.GearStats(b)
          check(st.arm == bst.arm and st.dps == bst.dps and st.min == bst.min, "a suffix item keeps its base's armor and damage: " .. it.name)
          for _, k in ipairs(SUF_STATS[it.suffix]) do
            check((st[k] or 0) > (bst[k] or 0), it.name .. " has its suffix's " .. k)
          end
          check(inPool[it], "suffix item drops: " .. it.name)
          perBase[it.base] = (perBase[it.base] or 0) + 1
        else
          check(it.id < 100000, "a real item id: " .. it.id)
        end
        if it.retired then nRetired = nRetired + 1; check(not inPool[it], "a random-suffix base no longer drops: " .. it.name) end
      end
      local nBase, nSingle = 0, 0
      for id, n in pairs(perBase) do
        nBase = nBase + 1
        check(n >= 1 and n <= 4, "1 to 4 suffixes per base: " .. TCF.GEAR[id].name .. " " .. n)
        if n == 1 then nSingle = nSingle + 1 end
      end
      check(nSingle <= 5, "almost every base has 2 to 4 suffixes; with one: " .. nSingle)
      check(nSuf >= 4000 and nBase >= 1500 and nRetired >= nBase, string.format("suffix items %d on %d bases (%d retired)", nSuf, nBase, nRetired))
      -- pinned ids: a saved "Bandit Cinch of the Monkey" must stay one forever
      local cinch, sword = TCF.GEAR[10977501], TCF.GEAR[10072702]
      check(cinch and cinch.name == "Bandit Cinch of the Monkey" and cinch.base == 9775 and cinch.slot == "WAIST", "pinned id 10977501: " .. gname(cinch))
      check(sword and sword.name == "Notched Shortsword of the Bear" and sword.base == 727, "pinned id 10072702: " .. gname(sword))
      -- the party look: suffix and white gear round-trip, and an unknown suffix shows its base
      TCF:SetClass("WARRIOR"); cd = TCF:CD(); adv = cd.adv; cd.level = 60
      local wbag, weq = TCF:Bag("WARRIOR"), TCF:GearEquipped("WARRIOR")
      for k in pairs(weq) do weq[k] = nil end
      local function pick(test)
        for _, it in ipairs(TCF.GEAR_LIST) do if test(it) and TCF:GearUsable(it, "WARRIOR") then return it end end
      end
      local sMain = pick(function(it) return it.suffix and it.slot == "1H" and it.sub == "sword" end)
      local sHead = pick(function(it) return it.suffix and it.slot == "HEAD" end)
      local wChest = pick(function(it) return it.q == 1 and inPool[it] and it.slot == "CHEST" and it.sub == "mail" end)
      -- exactly one copy of each (the 400 random warrior drops above can hold more, and a third
      -- copy of the worn one-hander is rightly junk for a dual-wielder: that made 12f flaky)
      for _, it in ipairs({ sMain, sHead, wChest }) do wbag[it.id] = 1 end
      check(TCF:EquipGear(sMain.id, "MAINHAND", "WARRIOR") and TCF:EquipGear(sHead.id, "HEAD", "WARRIOR") and TCF:EquipGear(wChest.id, "CHEST", "WARRIOR"), "equip suffix and white gear")
      local payload = TCF:PartyPayload("WARRIOR")
      -- suffix gear is sent as its base (it draws the same, and older versions know the base)
      check(payload and #payload <= 240 and payload:find("#" .. sMain.base, 1, true) and not payload:find("#" .. sMain.id, 1, true)
        and payload:find("#" .. wChest.id, 1, true), "party payload: " .. tostring(payload))
      local kind, pclass, plevel, look = TCF.PartyParse("H1;" .. payload)
      check(kind == "H1" and pclass == "WARRIOR" and plevel == 60, "party header")
      check(look.main and look.main.id == "gear:" .. sMain.base, "a suffix weapon arrives as its base: " .. tostring(look.main and look.main.id))
      check(look.head and look.head.id == "gear:" .. sHead.base, "a suffix helmet arrives as its base: " .. tostring(look.head and look.head.id))
      check(look.chest and look.chest.id == "gear:" .. wChest.id, "a white chest round-trips: " .. tostring(look.chest and look.chest.id))
      local own = TCF:GetAppearance("WARRIOR")
      local function same(a, b)
        return a and b and a.art == b.art and a.c1[1] == b.c1[1] and a.c1[2] == b.c1[2] and a.c1[3] == b.c1[3]
          and a.c2[1] == b.c2[1] and a.c2[2] == b.c2[2] and a.c2[3] == b.c2[3]
      end
      check(same(own.main, look.main) and same(own.head, look.head) and own.chest and own.chest.id == look.chest.id,
        "a friend sees the same drawing for suffix and white gear")
      -- every suffix version of a held off-hand draws like its base (shape and colours)
      local orb
      for _, it in ipairs(TCF.GEAR_LIST) do if it.suffix and it.slot == "HOLD" then orb = it; break end end
      if orb then
        local proxy = setmetatable({ GearEquipped = function() return { OFFHAND = orb.id } end }, { __index = TCF })
        local proxyB = setmetatable({ GearEquipped = function() return { OFFHAND = orb.base } end }, { __index = TCF })
        local a, b = TCF.GearAppearance(proxy, "MAGE"), TCF.GearAppearance(proxyB, "MAGE")
        check(same(a.off, b.off), "a suffix off-hand draws like its base: " .. gname(orb))
      end
      check(TCF.GearModelId(sMain.id) == sMain.base and TCF.GearModelId(sMain.base) == sMain.base
        and TCF.GearModelId(TCF.SUFFIX_ID_BASE + sMain.base * 100 + 99) == sMain.base, "3D models use the base item id")
      local newer = TCF.SUFFIX_ID_BASE + sMain.base * 100 + 99
      local _, _, _, look2 = TCF.PartyParse("H1;WARRIOR;60;;;;m=#" .. newer)
      check(look2 and look2.main and look2.main.id == "gear:" .. sMain.base, "an unknown suffix shows its base: " .. tostring(look2 and look2.main and look2.main.id))

      -- 12f. sell, junk, tooltip, compare and notice for white and suffix gear
      local function tipLines(fn)
        local lines = {}
        GameTooltip.AddLine = function(_, t, r, g, b) lines[#lines + 1] = { tostring(t), r, g, b } end
        GameTooltip.AddDoubleLine = function(_, a, b2) lines[#lines + 1] = { tostring(a) .. " " .. tostring(b2) } end
        local ok, err = pcall(fn)
        GameTooltip.AddLine, GameTooltip.AddDoubleLine = nil, nil
        check(ok, "tooltip: " .. tostring(err))
        local text = {}
        for i, l in ipairs(lines) do text[i] = l[1] end
        return lines, table.concat(text, "\n")
      end
      local sChest = pick(function(it) return it.suffix and it.slot == "CHEST" and it.sub == "mail" and it.ilvl >= wChest.ilvl + 5 and it.ilvl <= wChest.ilvl + 25 end)
      check(sChest, "a mail suffix chest above " .. wChest.name)
      check(TCF.GearLink(wChest):find("|cffffffff[" .. wChest.name .. "]", 1, true) and TCF.GearLink(sChest):find("|cff1eff00[", 1, true), "link colours")
      local lines, tip = tipLines(function() TCF:GearTooltip(GameTooltip, wChest, "WARRIOR") end)
      check(lines[1][1] == wChest.name and lines[1][2] == 1 and lines[1][3] == 1 and lines[1][4] == 1, "white tooltip title is white")
      check(tip:find(" Armor", 1, true) and tip:find("World drop", 1, true) and not tip:find("\n%+%d+ %a") and not tip:find("Equip:", 1, true), "white tooltip: " .. tip)
      lines, tip = tipLines(function() TCF:GearTooltip(GameTooltip, sChest, "WARRIOR") end)
      local want = ({ str = "Strength", agi = "Agility", sta = "Stamina", int = "Intellect", spi = "Spirit" })[SUF_STATS[sChest.suffix][1]]
      check(lines[1][1] == sChest.name and math.abs(lines[1][2] - 0.12) < 0.01, "suffix tooltip title is green")
      check(tip:find(" Armor", 1, true) and (not want or tip:find("%+%d+ " .. want)) and (want or tip:find("Equip:", 1, true)), "suffix tooltip: " .. tip)
      -- compare: the white against the worn suffix chest, the suffix chest against an empty slot
      weq.CHEST = nil
      _, tip = tipLines(function() TCF:GearCompareLines(GameTooltip, sChest, "WARRIOR") end)
      check(tip:find("empty Chest slot", 1, true) and tip:find("+", 1, true), "compare with an empty slot: " .. tip)
      wbag[sChest.id] = 1   -- one copy, whatever the random drops above gave
      check(TCF:EquipGear(sChest.id, "CHEST", "WARRIOR"), "equip the suffix chest")
      _, tip = tipLines(function() TCF:GearCompareLines(GameTooltip, wChest, "WARRIOR") end)
      check(tip:find("Instead of", 1, true) and tip:find(sChest.name, 1, true) and tip:find("Power", 1, true), "compare a white with a worn suffix piece: " .. tip)
      check((TCF:GearUpgrade(wChest, "WARRIOR") or 0) < 0, "the white is worse than the suffix piece")
      _, tip = tipLines(function() TCF:GearTooltip(GameTooltip, wChest, "WARRIOR") end)   -- with the side-by-side compare
      check(tip:find("Compared with what you're wearing", 1, true), "a white's full tooltip compares: " .. tip)
      -- sell: whites are worth a little, suffix greens a little more
      local vw, cw = TCF:GearSellValue(wChest)
      local vs, cs = TCF:GearSellValue(sChest)
      check(cw == "coins" and cs == "coins" and vw >= 1 and vw <= math.max(1, math.floor(wChest.ilvl * 0.05)) and vs > vw, "sell values " .. vw .. " " .. vs)
      wbag[wChest.id] = (wbag[wChest.id] or 0) + 1
      local coins0 = TCF.db.coins
      local paidC = TCF:SellGear(wChest.id)
      check(paidC == vw and TCF.db.coins == coins0 + vw and _chat[#_chat]:find(wChest.name, 1, true), "sell a white: " .. tostring(_chat[#_chat]))
      -- junk: unworn whites worse than the worn piece are junk, the worn suffix piece is not
      weq.CHEST = sChest.id
      wbag[wChest.id] = (wbag[wChest.id] or 0) + 2
      local junk = TCF:JunkGear("WARRIOR")
      check((junk[wChest.id] or 0) >= 2 and not junk[sMain.id] and not junk[sChest.id], "junk: whites yes, worn suffix gear no")
      TCF:SellJunk()
      check(not wbag[wChest.id] and weq.CHEST == sChest.id and wbag[sChest.id] and wbag[sChest.id] >= 1, "Sell junk sold the whites and kept what is worn")
      -- the small notice for a found piece: names it, says when it fills an empty slot
      weq.CHEST = nil
      TCF:Bag("WARRIOR")[sChest.id] = nil
      if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
      if not TCF.window then TCF:CreateWindow() end
      TCF.window:Show()
      local toastFrom = #_frames
      TCF:GrantGear(wChest, "Found on Kobold Vermin")
      TCF:GrantGear(sHead, "Found on Kobold Vermin")
      local nameShown, emptyShown = false, false
      for _, f in ipairs(_frames) do
        if f.kind == "FontString" and type(f.text) == "string" and f.shown then
          if f.text:find(wChest.name, 1, true) == 1 then nameShown = true end
          if f.text:find("+", 1, true) then emptyShown = true end
        end
      end
      check(nameShown and emptyShown, "a found white gets a slim line with its name and Power change")
      check(not (TapCatForeverLootReveal and TapCatForeverLootReveal:IsShown()), "found gear: no loot box")
      check(_chat[#_chat]:find("Found on Kobold Vermin", 1, true), "found gear chat line")
      -- the Gear page lists them
      if win then win:Show(); win:SelectTab(1); win:Refresh(true); win.gearSlot = "CHEST"; win:Refresh(); win.gearSlot = nil; win:Refresh() end

      -- 12g. small finds
      TCF.CHEST_SKIN_CHANCE, TCF.RollSkinSource, TCF.CHEST_GEAR_CHANCE = skinChance, skinRoll, gearChance
      TCF.openingAll = nil
      local SF = TCF.SMALL_FIND
      local findClass = TCF.CLASSES[_seed % #TCF.CLASSES + 1].key
      TCF:SetClass(findClass); cd = TCF:CD(); adv = cd.adv
      local fbag, feq = TCF:Bag(findClass), TCF:GearEquipped(findClass)
      -- start bare: gear this class got in earlier checks would fill its slots and leave
      -- little to find (that depends on the seed)
      for k in pairs(fbag) do fbag[k] = nil end
      for k in pairs(feq) do feq[k] = nil end
      local origGrant = TCF.GrantGear
      local grants, bad = 0, {}
      TCF.GrantGear = function(self, it, reason, ...)
        grants = grants + 1
        if not (type(reason) == "string" and reason:find("^Found on ")) then bad[#bad + 1] = "reason " .. tostring(reason) end
        if it.crafted or it.retired or not TCF:GearUsable(it, findClass) or it.req > cd.level or (it.q ~= 1 and it.q ~= 2) then bad[#bad + 1] = gname(it) end
        return origGrant(self, it, reason, ...)
      end
      local found0 = TCF.db.stats.gearFound or 0
      for lvl = 1, 60, 6 do
        cd.level = lvl
        for k = 1, 150 do adv.findClock = nil; TCF:TrashSmallFind({ name = "Kobold Vermin" }, TCF.TIERS[1]) end
      end
      TCF.GrantGear = origGrant
      check(grants >= 15 and #bad == 0, findClass .. " small finds: " .. grants .. ", wrong: " .. table.concat(bad, ", ", 1, math.min(5, #bad)))
      check((TCF.db.stats.gearFound or 0) == found0 + grants, "small finds count as gear found")
      -- a plate wearer finds the heaviest armor there is for its level, not cloth
      do
        local plate, chests = 0, 0
        for k = 1, 200 do
          local it = TCF:RollSmallFind("WARRIOR", 45, { "CHEST" })
          if it and it.slot == "CHEST" then chests = chests + 1; if it.sub == "plate" then plate = plate + 1 end end
        end
        check(chests >= 100 and plate >= 0.8 * chests, "a level 45 Warrior's chest finds are plate: " .. plate .. " of " .. chests)
        local leather, n = 0, 0
        for k = 1, 200 do
          local it = TCF:RollSmallFind("ROGUE", 30, { "LEGS" })
          if it and it.slot == "LEGS" then n = n + 1; if it.sub == "leather" then leather = leather + 1 end end
        end
        check(n >= 100 and leather >= 0.8 * n, "a level 30 Rogue's leg finds are leather: " .. leather .. " of " .. n)
      end
      -- they favour empty slots: half the slots filled, most finds go to the other half
      for k in pairs(fbag) do fbag[k] = nil end
      for k in pairs(feq) do feq[k] = nil end
      cd.level = 30
      local function fillSlot(s)
        for k = 1, 60 do
          local it = TCF:RollSmallFind(findClass, 30, { s })
          for _, ts in ipairs(it and TCF:GearTargetSlots(it, findClass) or {}) do
            if ts == s then fbag[it.id] = (fbag[it.id] or 0) + 1; TCF:EquipGear(it.id, s, findClass); return it end
          end
        end
      end
      for _, s in ipairs({ "HEAD", "CHEST", "LEGS", "FEET", "HANDS", "WRIST", "SHOULDER" }) do fillSlot(s) end
      local empty, nSlots = TCF:SmallFindNeed(findClass)
      local isEmpty = {}
      for _, s in ipairs(empty) do isEmpty[s] = true end
      local toEmpty, rolled = 0, 0
      for k = 1, 300 do
        local it = TCF:RollSmallFind(findClass, 30, empty)
        if it then
          rolled = rolled + 1
          for _, s in ipairs(TCF:GearTargetSlots(it, findClass)) do if isEmpty[s] then toEmpty = toEmpty + 1; break end end
        end
      end
      check(#empty >= 4 and #empty < nSlots and rolled >= 200 and toEmpty >= 0.75 * rolled,
        string.format("finds favour the %d empty slots of %d: %d of %d", #empty, nSlots, toEmpty, rolled))
      -- and they get rare once every slot is covered
      local function findRate(n)
        local got = 0
        TCF.GrantGear = function() got = got + 1 end   -- counted, not kept: the bag stays as it is
        for k = 1, n do adv.findClock = nil; TCF:TrashSmallFind({ name = "Defias Thug" }, TCF.TIERS[2]) end
        TCF.GrantGear = origGrant
        return got / n
      end
      local rateHalf = findRate(3000)
      for _, s in ipairs(empty) do fillSlot(s) end
      local empty2 = TCF:SmallFindNeed(findClass)
      local rateFull = findRate(3000)
      check(#empty2 <= 1 and rateHalf > 4 * rateFull and rateFull < 0.02,
        string.format("finds slow down as slots fill: %.4f with %d empty, %.4f with %d empty", rateHalf, #empty, rateFull, #empty2))
      -- a find waits out the gap after the last one (the gap clock is saved per class)
      for k in pairs(feq) do feq[k] = nil end
      for k in pairs(fbag) do fbag[k] = nil end
      adv.findClock, adv.smallFinds = 1, 0
      local g0 = TCF.db.stats.gearFound
      for k = 1, 300 do TCF:TrashSmallFind({ name = "Kobold Vermin" }, TCF.TIERS[1]) end
      check(TCF.db.stats.gearFound == g0, "no find within " .. SF.GAP_MIN .. " seconds of the last")
      adv.findClock = SF.GAP_MIN + 1
      for k = 1, 300 do TCF:TrashSmallFind({ name = "Kobold Vermin" }, TCF.TIERS[1]) end
      check(TCF.db.stats.gearFound == g0 + 1 and adv.findClock == 0 and adv.smallFinds == 1,
        "one find after the gap, then the gap again")
      -- selling every find doesn't keep them coming fast: a naked cat that has already had
      -- plenty of finds waits the long gap
      for k in pairs(fbag) do fbag[k] = nil end
      adv.findClock, adv.smallFinds = 600, 100
      g0 = TCF.db.stats.gearFound
      for k = 1, 300 do TCF:TrashSmallFind({ name = "Kobold Vermin" }, TCF.TIERS[1]) end
      check(TCF.db.stats.gearFound == g0, "a naked cat with 100 finds behind it waits the long gap")
      adv.findClock, adv.smallFinds = 20, 0
      for k = 1, 300 do TCF:TrashSmallFind({ name = "Kobold Vermin" }, TCF.TIERS[1]) end
      check(TCF.db.stats.gearFound == g0 + 1, "a naked new cat gets a find after a short gap")
      adv.findClock, adv.smallFinds = nil, nil
      -- a new cat in Adventure: about an hour fills most of the slots it shows
      local VIS = { "HEAD", "CHEST", "BACK", "WAIST", "NECK", "FINGER1", "MAINHAND", "OFFHAND" }
      local function hourOfAdventure(name, class, startLevel, minutes)
        login(name)
        TCF:SetClass(class)
        local c = TCF:CD()
        if startLevel > 1 then c.level = startLevel end
        local eq = TCF:GearEquipped(class)
        local finds = 0
        TCF.GrantGear = function(self, it, reason, ...)
          local slot = TCF:BestGearSlot(it, class)
          local wasEmpty = slot and not eq[slot]
          local r = origGrant(self, it, reason, ...)
          if type(reason) == "string" and reason:find("^Found on ") then finds = finds + 1 end
          -- the player equips whatever helps (finds, boss drops)
          if slot and TCF:CanEquipGear(it, class) and (wasEmpty or (TCF:GearUpgrade(it, class) or 0) > 0) then TCF:EquipGear(it.id, slot, class) end
          return r
        end
        if win then win:Hide() end
        TCF:AdvStart()
        local kbf = TapCatForeverKeyListener
        local t, nextKey = 0, 0
        while t < minutes * 60 do
          _clock = _clock + 0.25; t = t + 0.25
          if TCF.inFrenzy and GetTime() > (TCF.frenzyUntil or 0) then TCF.inFrenzy = false end
          TCF:AdvTick(0.25)
          if t >= nextKey then kbf.scripts.OnKeyDown(kbf, "Q"); nextKey = nextKey + 1 end
        end
        TCF.GrantGear = origGrant
        TCF:AdvRetreat()
        -- the shown slots the cat could fill at its level (no rings or necks below about 12)
        local mh = eq.MAINHAND and TCF.GEAR[eq.MAINHAND]
        local worn, reach = 0, 0
        for _, s in ipairs(VIS) do
          if not (s == "OFFHAND" and mh and mh.slot == "2H") then
            local ok = eq[s] ~= nil
            for b = 0, math.floor(math.min(60, c.level) / 5) do
              for _, it in ipairs(TCF.WORLD_POOL[b] or {}) do
                if not ok and it.q <= 2 and it.req <= c.level and TCF:GearUsable(it, class) then
                  for _, ts in ipairs(TCF:GearTargetSlots(it, class)) do if ts == s then ok = true end end
                end
              end
            end
            if ok then reach = reach + 1 end
            if eq[s] then worn = worn + 1 end
          end
        end
        -- the saved gap clock ran during the fights after the last find
        check(finds == 0 or (type(c.adv.findClock) == "number" and c.adv.findClock > 0 and c.adv.smallFinds == finds),
          "the small-find gap clock and count are saved per class: " .. tostring(c.adv.findClock) .. ", " .. tostring(c.adv.smallFinds))
        return worn, reach, finds, c.level, c.adv.kills
      end
      local c1 = TCF.CLASSES[(_seed + 3) % #TCF.CLASSES + 1].key
      local c2 = TCF.CLASSES[(_seed + 7) % #TCF.CLASSES + 1].key
      local w1, r1, f1, l1, k1 = hourOfAdventure("Findcat", c1, 1, 60)
      check(r1 >= 4 and w1 * 2 >= r1 and f1 >= 4 and f1 <= 25,
        string.format("a new level 1 %s fills most shown slots in an hour: %d of %d, %d finds", c1, w1, r1, f1))
      local w2, r2, f2, l2, k2 = hourOfAdventure("Findcat2", c2, 10, 75)
      check(r2 >= 5 and w2 * 2 > r2 and f2 >= 3 and f2 <= 25,
        string.format("a bare level 10 %s fills most shown slots in 75 minutes: %d of %d, %d finds", c2, w2, r2, f2))

      -- 12h. the Compendium builds with every new item and shows white gear apart
      login("Lootcheck")
      if TCF.compendium then TCF.compendium:Hide() end
      TCF.compendium = nil
      local compFrom = #_frames
      local comp = TCF:CreateCompendium()
      local compTo = #_frames
      comp.cat = "gear"; comp.filter = "all"; comp:Show()
      local plainSecs, cellsShown = 0, 0
      local nZones = #TCF.TIERS
      for _, z in ipairs({ 0, 1, 2, firstRaid, nZones }) do
        comp.gearZone, comp.gearSub, comp.page = z, 1, 1
        comp:Refresh()
        for sub = 1, 40 do
          comp.gearSub, comp.page = sub, 1
          comp:Refresh()
        end
      end
      comp.gearZone, comp.page = 0, 1
      for sub = 1, 40 do
        comp.gearSub = sub; comp:Refresh()
      end
      for i = compFrom + 1, compTo do
        local f = _frames[i]
        if f.kind == "FontString" and type(f.text) == "string" and f.text:find("Plain gear, levels", 1, true) and f.shown then plainSecs = plainSecs + 1 end
      end
      check(plainSecs >= 3, "the Compendium lists plain (white) gear apart: " .. plainSecs)
      -- hover the gear cells of the first plain section and the first world section
      local hovered = 0
      for _, sub in ipairs({ 1, 2 }) do
        comp.gearZone, comp.gearSub, comp.page = 0, sub, 1
        comp:Refresh()
        for i = compFrom + 1, compTo do
          local f = _frames[i]
          if f.item and f.item.q and f.scripts and f.scripts.OnEnter and f.shown and hovered < 60 then
            local _, t = tipLines(function() f.scripts.OnEnter(f) end)
            check(t:find("How to get", 1, true), "Compendium gear tooltip: " .. t)
            hovered = hovered + 1
          end
        end
      end
      check(hovered >= 10, "Compendium gear cells hovered: " .. hovered)
      local how = table.concat(TCF:HowToGet(wChest), " / ")
      check(how ~= "" and how:lower():find("white", 1, true), "how to get white gear: " .. how)
      how = table.concat(TCF:HowToGet(sChest), " / ")
      check(how:find("random bonuses", 1, true), "how to get a suffix item: " .. how)
      how = table.concat(TCF:HowToGet(TCF.GEAR[sChest.base]), " / ")
      check(how:find("No longer drops", 1, true), "how to get a retired base: " .. how)
      comp:Hide()
      login(mainChar)
      print(string.format("more gear: %d suffix items on %d bases, %d whites in pools; legendaries only from Heroic Caches and Hoards; " ..
        "small finds %.3f/%.4f per kill (half/all slots filled); new %s L1 60 min: %d finds, %d/%d shown slots, level %d; " ..
        "bare %s L10 75 min: %d finds, %d/%d shown slots", nSuf, nBase, whites, rateHalf, rateFull, c1, f1, w1, r1, l1, c2, f2, w2, r2))
    end)()
    -- 13. the Dungeon Chest (1.5.3): never sold, always dungeon boss gear near the cat's level
    -- (mostly Rare, some Uncommon, a little Epic, never Legendary), from finishing dungeons in
    -- Adventure (first clear, then on the dungeon chest clock), real WoW dungeons and dungeon expeditions
    ;(function()
      local dch = TCF.CHEST_BY_KEY.dungeon
      -- 13a. the chest itself
      check(dch and dch.name == "Dungeon Chest" and not dch.cost and dch.gearOnly and dch.dungeonLoot, "Dungeon Chest: never sold, always gear")
      check((dch.legendary or 0) == 0 and (dch.weights[5] or 0) == 0 and (dch.weights[1] or 0) == 0, "a Dungeon Chest never rolls Legendary or cosmetic rarities")
      check(dch.weights[3] > dch.weights[2] and dch.weights[2] > dch.weights[4] and dch.weights[4] > 0, "mostly Rare, some Uncommon, a little Epic")
      for _, ch in ipairs(TCF.CHESTS) do
        if ch ~= dch then check(ch.icon ~= dch.icon, "the Dungeon Chest has its own icon: " .. ch.key) end
      end
      check(dch.icon:find("^INV_Box_") ~= nil, "the Dungeon Chest icon is a real WoW box: " .. dch.icon)
      local coins0 = TCF.db.coins
      check(TCF:OpenChest("dungeon") == nil and TCF.db.coins == coins0, "a Dungeon Chest can't be bought")
      check(TCF.ChestQuality(dch) == 3, "a Dungeon Chest is announced in Rare blue")
      local odds = {}
      for _, o in ipairs(TCF:ChestOdds(dch)) do odds[o[1]] = o[2] end
      local function about(a, b) return a and math.abs(a - b) < 1e-6 end
      check(about(odds["Rare gear"], 67) and about(odds["Uncommon gear"], 25) and about(odds["Epic gear"], 8)
        and not odds["Legendary gear"] and not odds["Cosmetic"], "Dungeon Chest odds")
      local tip = tipText(function() TCF:ChestOddsTooltip(GameTooltip, dch) end)
      check(tip:find("Rare gear|r 67%", 1, true) and tip:find("Uncommon gear|r 25%", 1, true) and tip:find("Epic gear|r 8%", 1, true)
        and tip:find("dungeons your cat has reached", 1, true) and not tip:find("Legendary", 1, true) and not tip:find("Cosmetic", 1, true),
        "Dungeon Chest tooltip: " .. tip)
      check(not tip:find("!", 1, true), "plain text, no exclamation marks: " .. tip)
      -- the Treasure Bag and Shop texts name it
      local inSources = false
      for _, line in ipairs(TCF.CHEST_SOURCES) do if line:find("^Dungeon Chest:") then inSources = line end end
      check(inSources and inSources:find("Never sold", 1, true) and TCF.CHEST_BAG_TEXT.dungeon, "Treasure Bag texts list the Dungeon Chest")
      check(TCF.DUNGEON_CHEST_TEXT:find("Dungeon Chest", 1, true) and not TCF.DUNGEON_CHEST_TEXT:find("Strongbox", 1, true), "the Shop's free chest text: " .. TCF.DUNGEON_CHEST_TEXT)
      -- achievements count Dungeon Chests
      local nAch = 0
      for _, a in ipairs(TCF.ACHIEVEMENTS) do
        if a.stat == "dungeonChests" then nAch = nAch + 1; check(a.desc:find("Dungeon Chest", 1, true), "achievement text: " .. a.desc) end
      end
      check(nAch >= 2, "achievements for opening Dungeon Chests: " .. nAch)

      -- 13b. which tiers are dungeons
      local firstDungeon, nDungeons = nil, 0
      for ti, t in ipairs(TCF.TIERS) do
        local d = TCF.IsDungeonTier(ti)
        if d then nDungeons = nDungeons + 1; firstDungeon = firstDungeon or ti end
        if t.raid or t.key == "elwynn" or t.key == "westfall" then check(not d, t.name .. " is not a dungeon") end
        if t.key == "dm" or t.key == "strat" or t.key == "rfc" then check(d, t.name .. " is a dungeon") end
      end
      check(nDungeons >= 15 and TCF.TIERS[firstDungeon].key == "rfc", "dungeon tiers: " .. nDungeons)

      -- 13c. opening Dungeon Chests: gear the class can use, from dungeons it reached, near its level
      local skinRoll = TCF.RollSkinSource
      TCF.RollSkinSource = function() end
      local class0 = TCF.db.class
      TCF:SetClass("WARRIOR")
      local cd = TCF:CD()
      local adv = cd.adv
      local saved = { cd.level, adv.tier, adv.stage, adv.best, adv.dungeonClock, adv.chestClock, adv.active }
      local stat0 = TCF.db.stats.dungeonChests or 0
      -- (dungeon shares are counted for the cats that reached dungeons at their level: a level 8
      -- cat is below every dungeon's loot, so it gets gear of the rolled quality for its level)
      local byQ, total, counted, fromDungeon, blues, bluesFromDungeon = {}, 0, 0, 0, 0, 0
      TCF.openingAll = true
      -- a new cat (no dungeon reached: the first dungeon), a level 24 cat that reached the
      -- Deadmines, and a level 60 cat that has reached every dungeon
      local cases = { { 8, 1, 0 }, { 24, 5, 506 }, { 60, 21, 2112 } }
      for ci, case in ipairs(cases) do
        cd.level, adv.tier, adv.best = case[1], case[2], case[3]
        local reached = {}
        for _, ti in ipairs(TCF:DungeonTiers("WARRIOR")) do reached[ti] = true end
        if ci == 1 then check(reached[firstDungeon] and next(reached, next(reached)) == nil, "a new cat's Dungeon Chest uses the first dungeon") end
        for ti in pairs(reached) do check(TCF.IsDungeonTier(ti) and ti <= math.max(1, case[2], firstDungeon), "reached dungeon " .. ti) end
        TCF.db.keys.dungeon = 120
        for k = 1, 120 do
          local g = TCF:OpenChest("dungeon", true)
          local lc = TCF.lastChest
          check(g and lc and lc.gear == g, "a Dungeon Chest always holds gear")
          check(g.q >= 2 and g.q <= 4, "Uncommon to Epic: " .. g.name .. " q" .. g.q)
          check(TCF:GearUsable(g, "WARRIOR"), "Dungeon Chest gear fits the class: " .. g.name)
          -- (dungeon loot is at most 3 levels above the cat, below; the fallback for a quality the
          -- dungeons don't have looks a little higher, like the other chests: early levels have no Epics)
          check(g.req <= math.min(60, case[1]) + 15, "Dungeon Chest gear near the level: " .. g.name .. " req " .. g.req .. " at level " .. case[1])
          byQ[g.q] = (byQ[g.q] or 0) + 1; total = total + 1
          local isDungeon = g.tier and reached[g.tier]
          if isDungeon then
            check(g.req <= math.min(60, case[1]) + 3, "dungeon gear at most 3 levels above the cat: " .. g.name .. " req " .. g.req)
          end
          if ci >= 2 then
            counted = counted + 1
            if isDungeon then fromDungeon = fromDungeon + 1 end
            if g.q == 3 then blues = blues + 1; if isDungeon and g.boss and g.boss > 0 then bluesFromDungeon = bluesFromDungeon + 1 end end
          end
        end
        check(TCF.db.keys.dungeon == 0, "every Dungeon Chest opened")
      end
      TCF.openingAll = nil
      check((TCF.db.stats.dungeonChests or 0) == stat0 + 360, "Dungeon Chests counted")
      TCF:CheckAchievements()
      check(TCF.db.achievements.dchest1 and TCF.db.achievements.dchest25, "opening Dungeon Chests earns their achievements")
      -- 1.5.3.1: gear stays within 3 levels of the cat, so low cats get a green where no blue is that close
      check((byQ[3] or 0) >= (byQ[2] or 0) * 0.7 and (byQ[2] or 0) > (byQ[4] or 0) and (byQ[4] or 0) > 0 and not byQ[5],
        string.format("mostly Rare: %d green, %d blue, %d epic", byQ[2] or 0, byQ[3] or 0, byQ[4] or 0))
      check(bluesFromDungeon >= blues * 0.95, "Rare pieces are dungeon boss loot: " .. bluesFromDungeon .. " of " .. blues)
      check(fromDungeon >= counted * 0.7, "most pieces come from the dungeons reached: " .. fromDungeon .. " of " .. counted)
      -- the pool the chest reel shows matches what the chest can hold
      cd.level, adv.tier, adv.best = 24, 5, 506
      local pool = TCF:DungeonChestPool("WARRIOR")
      check(#pool[3] > 0, "the reel has Rare dungeon gear to show")
      for _, g in ipairs(pool[3]) do
        check(TCF.IsDungeonTier(g.tier) and g.tier <= 5 and g.req <= 27 and TCF:GearUsable(g, "WARRIOR"), "reel pool piece: " .. g.name)
      end
      -- a cat far ahead of its Adventure progress (cat levels come from tapping and expeditions
      -- too) gets gear near its level, never old loot from dungeons far below it: a level 60 cat
      -- still in Westfall, a level 40 cat with no Adventure progress, a level 50 cat at the Deadmines
      for _, case in ipairs({ { 60, 2, 201 }, { 40, 0, 0 }, { 50, 5, 506 } }) do
        cd.level, adv.tier, adv.best = case[1], case[2], case[3]
        local low
        for k = 1, 60 do
          local g = TCF:RollDungeonGear("WARRIOR", 3)
          if not g or g.req < case[1] - 15 then low = g and (g.name .. " req " .. g.req) or "nothing" end
        end
        check(not low, "Dungeon Chest gear stays near a level " .. case[1] .. " cat ahead of its Adventure progress: " .. tostring(low))
        local pool = TCF:DungeonChestPool("WARRIOR")
        for q = 2, 4 do
          for _, g in ipairs(pool[q]) do
            check(g.req >= case[1] - 10 and g.req <= case[1] + 3, "reel pool piece near level " .. case[1] .. ": " .. g.name .. " req " .. g.req)
          end
        end
      end
      cd.level, adv.tier, adv.best = 24, 5, 506
      -- the reel for a Dungeon Chest plays and lands on the real reward
      TCF.db.ui.chestAnim = true
      TCF.db.keys.dungeon = 1
      TCF.forceReveal = true
      -- (a Rare: only blue or better finds get the reel, and a Dungeon Chest is Uncommon 1 in 4)
      local rollRarity = TCF.RollRarity
      TCF.RollRarity = function() return 3 end
      TCF:OpenChest("dungeon", true)
      TCF.RollRarity = rollRarity
      TCF.forceReveal = nil
      check(TapCatForeverReel and TapCatForeverReel:IsShown(), "the Dungeon Chest reel plays")
      check(TapCatForeverReel.title:GetText() == "Opening Dungeon Chest...", "reel title: " .. tostring(TapCatForeverReel.title:GetText()))
      for i = 1, 40 do _update(0.1) end
      if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end

      -- 13d. Adventure: the first clear of a dungeon always gives one, repeat clears on the clock
      local paid = {}
      local origAward = TCF.AwardChest
      TCF.AwardChest = function(self, key, src, ...) paid[#paid + 1] = key .. "@" .. tostring(src); return origAward(self, key, src, ...) end
      local dm = 5
      local t = TCF.TIERS[dm]
      local last = TCF:AdvStages(dm)
      local function killFinal()
        adv.tier, adv.stage = dm, last
        paid = {}
        TCF:AdvMobKilled({ name = t.bosses[#t.bosses][1], boss = #t.bosses, final = true, level = 23 })
        return table.concat(paid, ", ")
      end
      adv.cleared[TCF.AdvStageCode(dm, last)] = nil
      adv.dungeonClock, adv.chestClock = 5000, 0
      check(killFinal():find("^dungeon@The Deadmines cleared$"), "the first clear of a dungeon gives a Dungeon Chest: " .. table.concat(paid, ", "))
      check(adv.dungeonClock == 0, "a Dungeon Chest resets the dungeon chest clock")
      adv.dungeonClock = TCF.ADV.DUNGEON_CHEST_MIN - 1
      check(not killFinal():find("dungeon@", 1, true), "no Dungeon Chest before the clock passes its minimum: " .. table.concat(paid, ", "))
      check(TCF.ADV.DUNGEON_CHEST_MIN >= 3600 and TCF.ADV.DUNGEON_CHEST_RAMP > 0 and TCF.ADV.DUNGEON_CHEST_MIN < TCF.ADV.RAID_CHEST_MIN,
        "the dungeon chest clock: at least an hour, shorter than the raid clock")
      adv.dungeonClock = TCF.ADV.DUNGEON_CHEST_MIN + TCF.ADV.DUNGEON_CHEST_RAMP
      check(killFinal() == "dungeon@The Deadmines finished" and adv.dungeonClock == 0, "a repeat clear on a full clock gives one: " .. table.concat(paid, ", "))
      -- only the final boss: other dungeon bosses roll the usual Pouch
      adv.dungeonClock, adv.chestClock = 1e6, 1e6
      adv.tier, adv.stage = dm, 2
      paid = {}
      TCF:AdvMobKilled({ name = t.bosses[1][1], boss = 1, level = 21 })
      check(table.concat(paid, ","):find("^pouch@"), "a dungeon's other bosses drop a Pouch: " .. table.concat(paid, ", "))
      -- zones and raids never give one
      adv.dungeonClock = 1e6
      adv.tier, adv.stage = 2, TCF:AdvStages(2)
      paid = {}
      TCF:AdvMobKilled({ name = TCF.TIERS[2].bosses[#TCF.TIERS[2].bosses][1], boss = #TCF.TIERS[2].bosses, final = true, level = 16 })
      check(not table.concat(paid, ","):find("dungeon@", 1, true), "an open-world zone never gives a Dungeon Chest: " .. table.concat(paid, ", "))
      -- the clock only runs while fighting in a dungeon
      TCF:AdvReset()
      adv.active = true
      for _, case in ipairs({ { dm, true }, { 1, false } }) do
        adv.tier, adv.stage = case[1], 1
        TCF.advRun.pack, TCF.advRun.respawn = nil, 0.05
        TCF:AdvTick(0.1)
        local c0 = adv.dungeonClock or 0
        for i = 1, 5 do TCF:AdvTick(0.1) end
        local grew = (adv.dungeonClock or 0) > c0
        check(grew == case[2], "the dungeon chest clock runs only in dungeons: " .. TCF.TIERS[case[1]].name)
      end
      adv.active = saved[7]

      -- 13e. real WoW dungeons and expeditions
      check(TCF.DungeonChestFor("party") == "dungeon" and TCF.DungeonChestFor("raid") == "raid", "real dungeons give a Dungeon Chest, raids a Raider's Hoard")
      local nTrips = 0
      for _, e in ipairs(TCF.EXPEDITIONS) do
        if e.dchest then
          nTrips = nTrips + 1
          check(TCF.IsDungeonTier(e.tier) and e.dchest > 0 and e.dchest <= 0.3 and e.dchest / (e.dur / 3600) <= 0.03,
            e.key .. ": only dungeon expeditions bring Dungeon Chests, at a fair rate: " .. e.dchest)
        end
      end
      check(nTrips >= 3, "dungeon expeditions with a Dungeon Chest chance: " .. nTrips)
      local st = TCF.db.expeditions or { active = {} }
      TCF.db.expeditions = st
      local strat = TCF.EXPEDITION_BY_KEY.strat
      local d0 = strat.dchest
      strat.dchest = 1
      paid = {}
      table.insert(st.active, { key = "strat", members = { "WARRIOR", "MAGE", "PRIEST" }, start = 0, finish = 0, power = 1e9, chance = 1 })
      TCF:ClaimExpedition(#st.active)
      strat.dchest = d0
      check(table.concat(paid, ","):find("dungeon@Purge Stratholme", 1, true), "a dungeon expedition can bring home a Dungeon Chest: " .. table.concat(paid, ", "))
      do
        local first = #_frames + 1
        local page = CreateFrame("Frame")
        local okE, errE = pcall(TCF.UI.Builders.expeditions, page, { party = {}, Refresh = function() end })
        check(okE, "expeditions page builds: " .. tostring(errE))
        local stratTip
        for i = first, #_frames do
          local f = _frames[i]
          if f.exp == strat and f.scripts.OnEnter then stratTip = tipText(function() f.scripts.OnEnter(f) end) end
        end
        check(stratTip and stratTip:find("Also a 15% chance of a Dungeon Chest.", 1, true), "Stratholme tooltip shows its Dungeon Chest chance: " .. tostring(stratTip))
      end
      -- a real dungeon run (level 20 and up) sometimes rolls the Heroic Cache's skins (Golden
      -- Treasure Cat, Diamond Cat) at the odds dungeons used to give a Heroic Cache; raids don't
      do
        local rolls = {}
        TCF.RollSkinSource = function(_, kind, match) rolls[#rolls + 1] = { kind = kind, match = match } end
        local lo, hi, day0, uLevel, k0 = TCF.DUNGEON_HEROIC_SKIN_LOW, TCF.DUNGEON_HEROIC_SKIN_HIGH, TCF.db.dungeonDay, UnitLevel, TCF.db.keys.dungeon
        check(lo == 0.10 and hi == 0.25, "the Heroic Cache skin odds after a real dungeon")
        TCF.DUNGEON_HEROIC_SKIN_LOW, TCF.DUNGEON_HEROIC_SKIN_HIGH = 1, 1
        local function run(kind, level)
          rolls, TCF.db.dungeonDay = {}, nil
          UnitLevel = function() return level end
          TCF:DungeonComplete({ id = -1, name = "Test Run", type = kind, bosses = 3, start = 0, rewarded = false }, "lfg")
          local heroic = false
          for _, r in ipairs(rolls) do
            if r.kind == "chest" and r.match({ chest = "heroic" }) and not r.match({ chest = "strong" }) then heroic = true end
          end
          return heroic
        end
        check(run("party", 55), "a real dungeon can roll the Heroic Cache's skins")
        check(not run("party", 15), "not below level 20")
        check(not run("raid", 60), "a real raid doesn't roll them")
        TCF.DUNGEON_HEROIC_SKIN_LOW, TCF.DUNGEON_HEROIC_SKIN_HIGH, TCF.db.dungeonDay, UnitLevel = lo, hi, day0, uLevel
        TCF.db.keys.dungeon = k0
        TCF.RollSkinSource = function() end
        local golden = table.concat(TCF:HowToGet(TCF.ITEMS.skin_golden), " / ")
        check(golden:find("after a real dungeon from level 20", 1, true), "the Compendium names real dungeons for the Golden Treasure Cat: " .. golden)
      end
      TCF.AwardChest = origAward
      -- the chat line names it in Rare blue
      local printed = {}
      local origPrint = TCF.Print
      TCF.Print = function(_, m) printed[#printed + 1] = m end
      local k0 = TCF.db.keys.dungeon or 0
      TCF:AwardChest("dungeon", "Test")
      TCF.Print = origPrint
      TCF.db.keys.dungeon = k0
      check(printed[1] and printed[1]:find("a |c" .. TCF.RARITY[3].hex .. "Dungeon Chest", 1, true) and not printed[1]:find("!", 1, true),
        "a Dungeon Chest is announced in blue: " .. tostring(printed[1]))
      -- the Compendium tells where dungeon boss loot comes from
      local bossItem = TCF.BOSS_LOOT[dm] and TCF.BOSS_LOOT[dm][#t.bosses] and TCF.BOSS_LOOT[dm][#t.bosses][1]
      local how = table.concat(TCF:HowToGet(bossItem), " / ")
      check(how:find("Dungeon Chests can hold it once your cat has reached The Deadmines", 1, true), "Compendium dungeon loot line: " .. how)
      local raidItem
      for ti, tt in ipairs(TCF.TIERS) do
        if tt.raid and not raidItem then for _, list in pairs(TCF.BOSS_LOOT[ti] or {}) do raidItem = raidItem or list[1] end end
      end
      how = table.concat(TCF:HowToGet(raidItem), " / ")
      check(not how:find("Dungeon Chest", 1, true), "raid loot is not in Dungeon Chests: " .. how)

      cd.level, adv.tier, adv.stage, adv.best, adv.dungeonClock, adv.chestClock = saved[1], saved[2], saved[3], saved[4], saved[5], saved[6]
      TCF.RollSkinSource = skinRoll
      TCF:SetClass(class0)
      print(string.format("dungeon chest: %d opened (%d green, %d blue, %d epic), %d of %d from dungeons reached, %d dungeon tiers, %d dungeon trips",
        total, byQ[2] or 0, byQ[3] or 0, byQ[4] or 0, fromDungeon, counted, nDungeons, nTrips))
    end)()
    ------------------------------------------------------------ progression (1.5.3): level cap 60 and the XP
    -- curve, level-up rewards once per class and level, the tap coin guard, chest coins and professions
    -- unlocked by Trade Gold earned. Runs on its own characters (Progcat...) and puts the account back.
    ;(function()
      local startChar = _charName
      -- taps here count exactly one each: no party bonus or Well Fed buff from earlier tests
      local partyMult, foodBuff = TCF.PartyTapMult, TCF.FoodBuff
      TCF.PartyTapMult, TCF.FoodBuff = function() return 1 end, nil
      local function fresh(name) TapCatForeverDB.chars[name .. "-Forever"] = nil; login(name) end
      local function chatSince(n0, pat)
        local hits = {}
        for i = n0 + 1, #_chat do if _chat[i]:find(pat, 1, true) then hits[#hits + 1] = _chat[i] end end
        return hits
      end
      local savedPaid = {}
      for k, v in pairs(TCF.db.levelPaid or {}) do savedPaid[k] = v end
      local savedQuests = TCF.db.quests
      local savedCoins, savedEarned = TCF.db.coins, TCF.db.coinsEarned

      -- 1. the XP curve: fast early, steadily slower, capped at 60
      check(TCF.MAX_LEVEL == 60, "levels stop at 60")
      local cum, prevStep = { [1] = 0 }, 0
      for L = 1, 59 do
        local need = TCF.XPForLevel(L)
        check(need > 0 and (L == 1 or need > TCF.XPForLevel(L - 1)), "each level needs more XP: " .. L)
        if L > 1 then
          local step = need - TCF.XPForLevel(L - 1)
          check(step >= prevStep, "the climb gets steadily slower at " .. L)
          prevStep = step
        end
        cum[L + 1] = cum[L] + need
      end
      check(TCF.XPForLevel(1) <= 120 and TCF.XPForLevel(59) > 100 * TCF.XPForLevel(1), "first levels fast, last ones slow")
      -- at about one key press a second while playing 2 hours a day
      local h = function(L) return cum[L] / 3600 end
      check(h(10) >= 0.75 and h(10) <= 1.25, "level 10 in about the first hour: " .. h(10))
      check(h(20) >= 4 and h(20) <= 10, "level 20 within the first few days: " .. h(20) .. " h")
      check(h(40) / 2 >= 14 and h(40) / 2 <= 42, "level 40 after a few weeks: day " .. h(40) / 2)
      check(h(60) / 2 >= 60 and h(60) / 2 <= 130, "level 60 after a few months: day " .. h(60) / 2)
      for _, t in ipairs(TCF.TITLES) do check(t[1] <= TCF.MAX_LEVEL, "every title can be reached: " .. t[2]) end
      for _, a in ipairs(TCF.ACHIEVEMENTS) do
        if a.stat == "level" then check(a.goal <= TCF.MAX_LEVEL, "every level achievement can be earned: " .. a.name) end
      end
      check(TCF:GetTitle(60) == "Eternal Tapper", "the last title is at 60")

      -- an hour of play at one key press a second, on a new character
      fresh("Progcat")
      local class = TCF.db.class
      local cd = TCF:CD()
      _clock = _clock + 5
      for i = 1, 3600 do _clock = _clock + 1; TCF:Tap() end
      check(cd.level >= 9 and cd.level <= 11, "about level 10 after an hour: " .. cd.level)

      -- 2. the cap: XP stops at 60, nothing breaks
      cd.level, cd.xp = 59, TCF.XPForLevel(59) - 1
      _clock = _clock + 5; TCF:Tap()
      check(cd.level == 60 and cd.xp == TCF.XPForLevel(60) and TCF:IsMaxLevel(), "level 60 with a full XP bar")
      for i = 1, 50 do _clock = _clock + 1; TCF:Tap() end
      TCF:AddClassXP(class, 1e7); TCF:LevelUp()
      check(cd.level == 60 and cd.xp == TCF.XPForLevel(60), "no XP or level past 60")
      check(TCF:GetStat("level") == 60, "achievements see level 60")
      check(TCF:CombatStats().power > 0, "combat stats at 60")
      TCF:AdvReset(); TCF:AdvStart()
      for i = 1, 40 do TCF:AdvTick(0.5) end
      TCF:CD().adv.active = false
      -- expeditions give a cat at 60 no XP and still work
      TCF:AddClassXP(class, 900)
      check(cd.level == 60 and cd.xp == TCF.XPForLevel(60), "expedition XP stops at 60")
      -- a cat above 60 from before the cap becomes 60 and keeps its gear, abilities and title
      cd.level, cd.xp = 75, 123
      cd.abilities.progtest = true
      local gear0 = {}
      for k, v in pairs(cd.gear) do gear0[k] = v end
      login("Progcat")
      cd = TCF:CD()
      check(cd.level == 60 and cd.xp == TCF.XPForLevel(60), "a level 75 cat became 60")
      check(cd.abilities.progtest, "abilities kept")
      for k, v in pairs(gear0) do check(cd.gear[k] == v, "gear kept: " .. tostring(k)) end
      check(TCF:GetTitle() == "Eternal Tapper", "title at 60")
      cd.abilities.progtest = nil
      -- "Growing Up" needs a cat that can still level
      local function questCounters(n)
        local seen = {}
        for i = 1, n do
          TCF.db.quests = nil
          TCF:EnsureQuests()
          for _, q in ipairs(TCF.db.quests.daily) do seen[q.counter] = true end
        end
        return seen
      end
      check(questCounters(60).levels, "Growing Up is offered while a cat can level")
      for _, c in pairs(TCF.db.classData) do c.level = 60 end
      check(not questCounters(60).levels, "no Growing Up when every cat is level 60")
      TCF.db.quests = savedQuests

      -- 3. level-up TapCoins and chests: once per class and level for the whole account
      fresh("Progalt")
      TCF:SetClass("HUNTER")
      TCF.db.levelPaid.HUNTER = 1
      check(rawget(TapCatForeverDB, "levelPaid") == TCF.db.levelPaid, "the record is account-wide")
      local function levelTo(L)
        local c = TCF:CD("HUNTER")
        -- (1.5.4: level chests go to the Hunter's own bag, even while another cat is played)
        local coins, strong, heroic = TCF.db.coins, TCF:ChestsOf("strong", "HUNTER"), TCF:ChestsOf("heroic", "HUNTER")
        while c.level < L do c.xp = 0; TCF:AddClassXP("HUNTER", TCF.XPForLevel(c.level)) end
        return TCF.db.coins - coins, TCF:ChestsOf("strong", "HUNTER") - strong, TCF:ChestsOf("heroic", "HUNTER") - heroic
      end
      local want = 0
      for L = 2, 10 do want = want + TCF.LevelReward(L) end
      local got, strong = levelTo(10)
      check(got == want and strong == 2, "the first Hunter to 10 gets the coins and two Strongboxes: " .. got .. ", " .. strong)
      -- a new alt's Hunter: no coins or chests until it passes level 10
      fresh("Progalt2")
      local chat0 = #_chat
      got, strong = levelTo(10)
      check(got == 0 and strong == 0, "a new alt's Hunter is not paid again: " .. got .. ", " .. strong)
      check(#chatSince(chat0, "already got this level's rewards") >= 9, "the chat line says why")
      got, strong = levelTo(11)
      check(got == TCF.LevelReward(11) and strong == 0, "level 11 is new for the account")
      -- "Reset this character" gives a level 1 cat that can't collect them again
      TCF:ResetProgress("char")
      login("Progalt2")
      check(TCF:CD("HUNTER").level == 1, "reset: a level 1 Hunter")
      got, strong = levelTo(15)
      local want15 = 0
      for L = 12, 15 do want15 = want15 + TCF.LevelReward(L) end
      check(got == want15 and strong == 1, "after a reset only levels 12-15 pay: " .. got .. ", " .. strong)
      -- another class is paid on its own
      TCF.db.levelPaid.DRUID = 1
      local dc = TCF.db.coins
      TCF:AddClassXP("DRUID", TCF.XPForLevel(1))
      check(TCF.db.coins - dc == TCF.LevelReward(2), "a Druid's level 2 still pays")
      -- an old save (no record yet) starts from the highest level any character's cat reached
      TapCatForeverDB.chars["Progold-Forever"] = { class = "ROGUE", classData = { ROGUE = { level = 33, xp = 0 }, MAGE = { level = 70, xp = 0 } } }
      rawset(TapCatForeverDB, "levelPaid", nil)
      login("Progalt2")
      check(TCF.db.levelPaid.ROGUE >= 33 and TCF.db.levelPaid.MAGE == 60 and TCF.db.levelPaid.HUNTER >= 15, "the record starts from every character's cats")
      TapCatForeverDB.chars["Progold-Forever"] = nil

      -- 4. taps beyond 10 a second earn no TapCoins (all 20 still count as taps and XP)
      _group = nil
      TCF:CD().level = 5
      local function value() return TCF.db.coins + TCF.db.coinFrac end
      _clock = _clock + 5
      local v0, taps0, xp0 = value(), TCF.db.taps, TCF:CD().xp
      for i = 1, 30 do TCF:Tap() end
      check(TCF.db.taps - taps0 == 20, "20 taps count in one second")
      check(math.abs(value() - v0 - 10 * 0.02) < 1e-9, "only 10 of them earn TapCoins: " .. (value() - v0))
      _clock = _clock + 5
      v0 = value()
      for s = 1, 5 do for i = 1, 8 do TCF:Tap(); _clock = _clock + 0.125 end end
      check(math.abs(value() - v0 - 40 * 0.02) < 1e-9, "8 taps a second all earn: " .. (value() - v0))
      check(TCF.TAP_COIN_CAP == 10, "the TapCoin cap")

      -- 5. chest coins: mostly none, often tiny, rarely a big handful
      local SPEC = { pouch = { { 2, 5 }, { 40, 80 } }, strong = { { 3, 8 }, { 80, 150 } }, dungeon = { { 3, 8 }, { 80, 150 } },
        heroic = { { 5, 15 }, { 150, 300 } }, raid = { { 5, 15 }, { 150, 300 } } }
      local avgCoins = {}
      for _, ch in ipairs(TCF.CHESTS) do
        local sp = SPEC[ch.key]
        check(sp and ch.coins and ch.coins.tiny[1] == sp[1][1] and ch.coins.tiny[2] == sp[1][2]
          and ch.coins.big[1] == sp[2][1] and ch.coins.big[2] == sp[2][2], "chest coins for " .. ch.key)
        local none, tiny, big, sum, N = 0, 0, 0, 0, 20000
        for i = 1, N do
          local n = TCF:RollChestCoins(ch)
          if n == 0 then none = none + 1
          elseif n >= sp[1][1] and n <= sp[1][2] then tiny = tiny + 1
          elseif n >= sp[2][1] and n <= sp[2][2] then big = big + 1
          else check(false, "coins out of range: " .. n) end
          sum = sum + n
        end
        check(math.abs(none / N - 0.60) < 0.02 and math.abs(tiny / N - 0.35) < 0.02 and math.abs(big / N - 0.05) < 0.01,
          string.format("%s coin odds: %.3f / %.3f / %.3f", ch.key, none / N, tiny / N, big / N))
        avgCoins[ch.key] = sum / N
      end
      -- a typical day of a 2 hours a day player (a 30-day TapCoin pace simulation of the real addon:
      -- about 11 chests a day, mostly Pouches) next to the about 750 TapCoins a day from everything
      -- that repeats. In that simulation chest coins came to 47-57 a day in days 8-30 (5-7%).
      local DAY = { pouch = 7.9, strong = 2.0, dungeon = 0.9, heroic = 0.45, raid = 0.1 }
      local perDay = 0
      for k, n in pairs(DAY) do perDay = perDay + n * avgCoins[k] end
      check(perDay < 0.1 * 750, string.format("chest coins add under 10%% of a day's TapCoins: %.0f a day", perDay))
      -- the opening: the loot box can see the coins while it opens, then TCF.lastChest.coins
      local roll, grant = TCF.RollChestCoins, TCF.GrantGear
      local during
      TCF.GrantGear = function(self, ...) during = TCF.chestCoins; return grant(self, ...) end
      TCF.RollChestCoins = function() return 33 end
      TCF.db.keys.dungeon = (TCF.db.keys.dungeon or 0) + 2   -- (always gear)
      local c0 = TCF.db.coins
      TCF:OpenChest("dungeon", true)
      check(TCF.lastChest and TCF.lastChest.coins == 33 and TCF.db.coins >= c0 + 33, "TCF.lastChest.coins")
      check(during == 33 and TCF.chestCoins == nil, "TCF.chestCoins only while opening")
      TCF.RollChestCoins = function() return 0 end
      TCF:OpenChest("dungeon", true)
      check(TCF.lastChest and TCF.lastChest.coins == nil, "no coins: nil")
      TCF.RollChestCoins, TCF.GrantGear = roll, grant

      -- 6. professions unlock with the Trade Gold this cat earned (Renown is only a fallback)
      local GOLD = { herbalism = 1e9, firstaid = 5e13, fishing = 1e15, cooking = 5e16 }   -- 1.5.3.4
      local RENOWN = { herbalism = 5, firstaid = 20, fishing = 60, cooking = 150 }
      for k, g in pairs(GOLD) do
        check(TCF.PROF_BY_KEY[k].gold == g and TCF.PROF_BY_KEY[k].renown == RENOWN[k], "unlock cost of " .. k)
      end
      fresh("Progprof")
      TCF:SetClass("MAGE")
      local s = TCF:ProfState()
      local have, need, done = TCF:ProfUnlockProgress("herbalism")
      check(have == 0 and need == 1e9 and not done and not TCF:ProfUnlocked("herbalism"), "Herbalism starts locked")
      local c1 = #_chat
      TCF:EarnGold(1e9 - 1)
      check(not TCF:ProfUnlocked("herbalism") and #chatSince(c1, "Herbalism") == 0, "not yet")
      TCF:EarnGold(1)
      check(TCF:ProfUnlocked("herbalism") and s.announced.herbalism, "Herbalism unlocked at 1B earned")
      local lines = chatSince(c1, "can now learn")
      check(#lines == 1 and lines[1]:find("Herbalism", 1, true) and lines[1]:find("Mage", 1, true), "one chat line: " .. tostring(lines[1]))
      TCF:EarnGold(1000); login("Progprof"); TCF:SetClass("WARRIOR"); TCF:SetClass("MAGE")
      check(#chatSince(c1, "can now learn") == 1, "it never repeats")
      -- selling the business never takes an unlock away (and never lowers the gold earned)
      s.lifetime = 6e13; TCF:EarnGold(0)
      check(TCF:ProfUnlocked("firstaid") and #chatSince(c1, "First Aid") == 1, "First Aid at 50T")
      s.lifetime = 1e17
      check(TCF:PrestigeTrade() and s.lifetime == 1e17 and s.gold == 0 and TCF:ProfUnlocked("cooking"), "selling keeps Trade Gold earned and unlocks")
      check(#chatSince(c1, "Cooking") == 1 and #chatSince(c1, "Fishing") == 1, "every unlock announced once")
      -- 1.5.3.4: Renown alone no longer unlocks anything new (only Trade Gold earned)
      TCF:SetClass("PRIEST")
      local p = TCF:ProfState()
      p.renown, p.renownEver = 20, 20
      check(not TCF:ProfUnlocked("herbalism") and not TCF:ProfUnlocked("firstaid"), "Renown alone unlocks nothing")
      -- a cat you aren't playing hears nothing until you play it
      local c2 = #_chat
      TCF:WithTradeClass("WARLOCK", TCF.EarnGold, 6e13)
      local wl = TCF:CD("WARLOCK").trade
      check(wl.lifetime >= 6e13 and not wl.announced.herbalism and #chatSince(c2, "can now learn") == 0, "quiet for another cat")
      TCF:SetClass("WARLOCK")
      lines = chatSince(c2, "can now learn")
      check(#lines == 2 and wl.announced.herbalism and wl.announced.firstaid, "announced when you play it: " .. #lines)
      -- unlocked but never announced (offline): told at login, once
      TCF:SetClass("MAGE")
      s = TCF:ProfState()
      s.announced = {}
      local c3 = #_chat
      login("Progprof")
      check(#chatSince(c3, "can now learn") == 4, "told at login")
      login("Progprof")
      check(#chatSince(c3, "can now learn") == 4, "only once")
      -- a 1.5.2 save already heard about what its Renown unlocked: no chat line for those
      TapCatForeverDB.chars["Progren-Forever"] = { class = "MAGE", classData = { MAGE = { level = 30, xp = 0,
        trade = { gold = 0, lifetime = 3e9, renown = 25, renownEver = 25, famMoved = true, last = time() } } } }
      local c4 = #_chat
      login("Progren")
      check(TCF:ProfUnlocked("firstaid") and #chatSince(c4, "can now learn") == 0, "old Renown unlocks are not announced again")
      TapCatForeverDB.chars["Progren-Forever"] = nil
      -- the 1.5.1 split: a cat whose earned Trade Gold unlocked First Aid keeps First Aid's cloth
      TapCatForeverDB.chars["Progaid-Forever"] = { class = "WARRIOR", classData = { MAGE = { level = 10, xp = 0 }, WARRIOR = { level = 20, xp = 0 } },
        trade = { gold = 10, lifetime = 6e13, renown = 0, renownEver = 0, famMoved = true, last = time(),
          ops = { cloth = { { n = 2, p = 0, run = false, mgr = false } }, mining = { { n = 4, p = 0, run = false, mgr = false } } },
          mats = { linen = 5000, copper = 5 } } }
      login("Progaid")
      check(TCF:CD("WARRIOR").trade.mats.linen == 5000 and TCF:ProfUnlocked("firstaid"), "First Aid by Trade Gold keeps the cloth in the split")
      TapCatForeverDB.chars["Progaid-Forever"] = nil
      -- the page: the locked view shows the gold needed and the progress, tooltips and the guide say so too
      fresh("Progprof2")
      TCF:SetClass("MAGE")
      TCF:EarnGold(5e6)
      local page = CreateFrame("Frame")
      local first = #_frames + 1
      local pw = { profSel = "fishing", profView = "main", Refresh = function() end }
      local refreshPage = TCF.UI.Builders.professions(page, pw)
      local function has(sub)
        for i = first, #_frames do local f = _frames[i]; if f.kind == "FontString" and type(f.text) == "string" and f.text:find(sub, 1, true) then return f.text end end
      end
      refreshPage()
      local lock = has("unlocks when your Mage cat has earned")
      check(lock and lock:find(TCF.GoldStr(1e15), 1, true) and lock:find("So far: " .. TCF.GoldStr(5e6) .. " (0%)", 1, true), "locked view: " .. tostring(lock))
      pw.profSel = "herbalism"; refreshPage()
      check(has("So far: " .. TCF.GoldStr(5e6) .. " (0%)"), "progress in percent")
      pw.profView = "renown"; refreshPage()
      check(has("Herbalism at 1.00B") and not has("unlocks new professions"), "the Renown view lists the gold")
      TCF.ShowProfessionGuide(TCF, "cloth")
      check(has("As this cat earns Trade Gold it unlocks Herbalism, First Aid, Fishing and Cooking") and not has("Renown unlocks"), "the guide's Grow paragraph")
      local tip = tipText(function()
        for i = first, #_frames do local f = _frames[i]
          if f.prof and f.prof.key == "cooking" and f.scripts.OnEnter then f.scripts.OnEnter(f) end
        end
      end)
      check(tip:find("Unlocks when this cat has earned", 1, true) and tip:find("So far:", 1, true), "tab tooltip: " .. tip)

      -- put the account back
      TCF.PartyTapMult, TCF.FoodBuff = partyMult, foodBuff
      TCF.db.levelPaid = savedPaid
      for k, v in pairs(savedPaid) do TCF.db.levelPaid[k] = v end
      for _, n in ipairs({ "Progcat", "Progalt", "Progalt2", "Progprof", "Progprof2" }) do TapCatForeverDB.chars[n .. "-Forever"] = nil end
      TCF.db.coins, TCF.db.coinsEarned = savedCoins, savedEarned
      login(startChar)
      TCF.db.quests = savedQuests
      print(string.format("progression: level 10 at %.1f h, 20 at %.1f h, 40 on day %d, 60 on day %d (2 h a day, taps only); " ..
        "chest coins avg %.1f/%.1f/%.1f (pouch/strongbox/heroic), about %.0f a day", h(10), h(20), math.floor(h(40) / 2 + 0.5),
        math.floor(h(60) / 2 + 0.5), avgCoins.pouch, avgCoins.strong, avgCoins.heroic, perDay))
    end)()
    -- ===== UI section (1.5.3, UI builder): Text distance slider, chest TapCoins line, opt-in developer view =====
    do
      local ui = TCF.db.ui
      local win = TCF.window
      local KEYS = { "textGap", "textAbove", "catOnly", "showLevel", "chestAnim", "shareDev", "testMode" }
      local saved = { point = { unpack(ui.point) }, hudLayout = ui.hudLayout and { unpack(ui.hudLayout) } }
      for _, k in ipairs(KEYS) do saved[k] = ui[k] end
      local function fromFrames(first, sub)
        for i = first, #_frames do
          local f = _frames[i]
          if type(f.text) == "string" and f.text:find(sub, 1, true) then return f end
        end
      end
      local function layoutItem(label)
        for _, a in ipairs(win.settingsLayout) do if a.label == label then return a end end
      end

      -- U1. Text distance: a slider in "Cat and display", saved in db.ui.textGap (default 4, the old gap)
      local gapA = layoutItem("Text distance")
      check(gapA and gapA.kind == "slider" and gapA.x == 16 and gapA.y + gapA.h < 231, "Text distance slider in Cat and display")
      local nSliders = 0
      for _, a in ipairs(win.settingsLayout) do if a.kind == "slider" then nSliders = nSliders + 1 end end
      check(nSliders == 4, "four sliders: " .. nSliders)
      ui.textGap = nil
      check(TCF.HudTextGap() == 4 and TCF.TEXT_GAP_DEFAULT == 4, "the gap is 4 until changed")
      ui.textGap = 999; check(TCF.HudTextGap() == TCF.TEXT_GAP_MAX, "kept in range (high)")
      ui.textGap = -999; check(TCF.HudTextGap() == TCF.TEXT_GAP_MIN, "kept in range (low)")
      ui.textGap = "x"; check(TCF.HudTextGap() == 4, "junk saved value: the default")
      -- the text block's anchor follows the gap, above and below; the cat's feet stay put
      local hud, info = TCF.hud, TCF.hud.info
      local infoPt, height
      info.SetPoint = function(_, ...) infoPt = { ... } end
      hud.SetHeight = function(_, h) height = h end
      ui.catOnly = false; ui.showLevel = true
      local function feet()
        local p = ui.point
        local h = height
        local frameBottom = p[1]:find("BOTTOM") and 0 or p[1]:find("TOP") and -h or -h / 2
        return p[4] + frameBottom + (ui.textAbove and 0 or h - 120)
      end
      for _, anchor in ipairs({ "BOTTOM", "TOPLEFT", "CENTER" }) do
        for _, above in ipairs({ true, false }) do
          ui.point = { anchor, anchor, 10, 200 }
          ui.textAbove = above; ui.textGap = 4; hud:ApplySettings()
          check(height == 160, "default height 160: " .. tostring(height))
          check(infoPt[4] == 0 and infoPt[5] == (above and 4 or -4), "default gap 4: " .. tostring(infoPt[5]))
          local f0 = feet()
          for _, g in ipairs({ 20, -10, 40, 0 }) do
            ui.textGap = g; hud:ApplySettings()
            check(infoPt[1] == (above and "BOTTOM" or "TOP") and infoPt[5] == (above and g or -g), "gap " .. g .. " applied " .. (above and "above" or "below"))
            check(height == 156 + g, "frame covers cat and text at gap " .. g .. ": " .. tostring(height))
            check(math.abs(feet() - f0) < 1e-9, anchor .. ": the cat's feet stay put at gap " .. g .. (above and " (text above)" or " (text below)"))
          end
        end
      end
      -- hiding the text: the frame shrinks to the cat whatever the gap
      ui.textGap = 30; ui.catOnly = true; hud:ApplySettings()
      check(height == 120, "cat only: the cat alone")
      ui.catOnly = false; hud:ApplySettings()
      info.SetPoint, hud.SetHeight = nil, nil
      -- the slider sets and shows the value
      local gs = gapA.frame
      gs:SetValue(12.3)
      check(ui.textGap == 12, "slider sets db.ui.textGap: " .. tostring(ui.textGap))
      ui.textGap = 7; win:RefreshSettings()
      check(gs:GetValue() == 7, "Settings shows the saved gap")
      local tip = tipText(function() gs.scripts.OnEnter(gs) end)
      check(tip:find("between the cat and its level", 1, true) and not tip:find("!", 1, true), "Text distance tooltip: " .. tip)
      -- the slider tooltips carry the old Ctrl/Shift help line
      tip = tipText(function() local s = layoutItem("Cat size").frame; s.scripts.OnEnter(s) end)
      check(tip:find("Ctrl + mouse wheel", 1, true), "Cat size tooltip names Ctrl + wheel")
      check(not win.settingsInfo.help:GetText():find("Ctrl", 1, true), "help line without the wheel line (it is in the slider tooltips)")
      -- test mode: the shortcuts take the place of the party note and the help line
      ui.testMode = true; win:RefreshSettings()
      check(not win.settingsInfo.note:IsShown() and win.settingsInfo.testBox:IsShown(), "test mode: shortcuts instead of the notes")
      ui.testMode = saved.testMode; win:RefreshSettings()
      check(win.settingsInfo.note:IsShown(), "party note back")

      -- U2. chest TapCoins: one plain line in the loot box after the reel, and on the slim line
      local roll, rollCoins = TCF.RollRarity, TCF.RollChestCoins
      local lr = TCF.lootReveal or TCF:CreateLootReveal()
      if TapCatForeverReel then TapCatForeverReel.pending = {} end   -- spins still waiting from earlier checks
      if TapCatForeverReel and TapCatForeverReel:IsShown() then TapCatForeverReel:Finish() end
      lr:Hide()
      ui.chestAnim = true
      TCF.RollRarity = function() return 3 end
      TCF.RollChestCoins = function() return 7 end
      TCF.db.keys.dungeon = (TCF.db.keys.dungeon or 0) + 1
      TCF.forceReveal = true; TCF:OpenChest("dungeon", true); TCF.forceReveal = nil
      check(TapCatForeverReel:IsShown(), "reel for a Rare")
      for i = 1, 40 do _update(0.1) end
      check(lr:IsShown() and lr.coins:GetText() == "+7 TapCoins", "loot box coin line: " .. tostring(lr.coins:GetText()))
      check(not lr.status:GetText():find("TapCoins", 1, true), "the coins are their own line, nothing else")
      -- no coins: no line
      lr:Hide()
      TCF.RollChestCoins = function() return 0 end
      TCF.db.keys.dungeon = TCF.db.keys.dungeon + 1
      TCF.forceReveal = true; TCF:OpenChest("dungeon", true); TCF.forceReveal = nil
      for i = 1, 40 do _update(0.1) end
      check(lr:IsShown() and lr.coins:GetText() == "", "no coins, no line: " .. tostring(lr.coins:GetText()))
      lr:Hide()
      -- animation off: straight to the box, still with the line
      ui.chestAnim = false
      TCF.RollChestCoins = function() return 1234 end
      TCF.db.keys.dungeon = TCF.db.keys.dungeon + 1
      TCF.forceReveal = true; TCF:OpenChest("dungeon", true); TCF.forceReveal = nil
      check(lr:IsShown() and lr.coins:GetText() == "+" .. TCF.Commas(1234) .. " TapCoins", "no reel: coin line " .. tostring(lr.coins:GetText()))
      lr:Hide()
      -- 1.5.3.3: a green from a chest you open gets the loot box too, with its coin line
      TCF.RollRarity = function() return 2 end
      TCF.RollChestCoins = function() return 5 end
      TCF.db.keys.dungeon = TCF.db.keys.dungeon + 1
      TCF.forceReveal = true; TCF:OpenChest("dungeon", true); TCF.forceReveal = nil
      check(lr:IsShown() and lr.coins:GetText() == "+5 TapCoins", "a green: the loot box with the coins: " .. tostring(lr.coins:GetText()))
      lr:Hide()
      -- a second reward from the same chest (a skin) doesn't repeat the coins; the next chest has its own
      ui.chestAnim = false
      local gear
      for _, g in ipairs(TCF.GEAR_LIST) do if g.q == 3 and not g.crafted then gear = g; break end end
      local got = {}
      local direct = TCF.ShowLootRevealDirect
      TCF.ShowLootRevealDirect = function(self, ...) got[#got + 1] = select(7, ...) or false; return direct(self, ...) end
      local function show() lr:Hide(); TCF:ShowLootReveal(gear, true, 0, "test", "heroic", true); return lr.coins:GetText() end
      TCF.db.stats.chests = TCF.db.stats.chests + 1
      TCF.chestCoins = 9
      check(show() == "+9 TapCoins", "the chest's reward shows its coins")
      check(show() == "", "a second reward from the same chest doesn't repeat them")
      TCF.db.stats.chests = TCF.db.stats.chests + 1
      check(show() == "+9 TapCoins", "the next chest has its own")
      TCF.chestCoins = nil
      check(show() == "", "no coins after the opening")
      check(got[1] == 9 and got[2] == false and got[3] == 9 and got[4] == false, "coins passed on with the reward")
      -- a reward taking over a loot box that is already up brings its own line (or none)
      lr:Hide()
      TCF:ShowLootReveal(gear, true, 0, "test", "heroic", true, 3)
      lr:ShowFront({ gear, true, 0, "test", "heroic", true, nil })
      check(lr:IsShown() and lr.coins:GetText() == "", "ShowFront replaces the line")
      lr:ShowFront({ gear, true, 0, "test", "heroic", true, 4 })
      check(lr.coins:GetText() == "+4 TapCoins", "ShowFront shows its coins")
      lr:Hide()
      TCF.ShowLootRevealDirect = direct
      TCF.RollRarity, TCF.RollChestCoins = roll, rollCoins
      ui.chestAnim = saved.chestAnim

      -- U3. opt-in developer view
      local DT = TCF.DevTest
      DT.reset()
      -- the developer is known by name and realm: this test's developer characters are Ziggu and
      -- Ziggutrip on the test realm (Forever); the shipped list is the developer's own
      GetNormalizedRealmName = function() return "Forever" end
      local shippedDevKeys = DT.setDevKeys({ DT.keyHash("ziggu-forever"), DT.keyHash("ziggutrip-forever") })
      local joined, left, removed, guild, channelId = {}, 0, {}, true, 0
      JoinTemporaryChannel = function(name) joined[#joined + 1] = name; channelId = 7 end
      LeaveChannelByName = function(name) if name == TCF.DEV_CHANNEL then left = left + 1; channelId = 0 end end
      GetChannelName = function(name) if name == TCF.DEV_CHANNEL and channelId > 0 then return channelId, name end return 0 end
      IsInGuild = function() return guild end
      ChatFrame1 = CreateFrame("Frame", "ChatFrame1")
      ChatFrame_RemoveChannel = function(cf, name) removed[#removed + 1] = name end
      local sent = {}
      local api = C_ChatInfo.SendAddonMessage
      C_ChatInfo.SendAddonMessage = function(p, msg, ch, target)
        if p == TCF.DEV_PREFIX and type(msg) == "string" and (msg:find("^Q1;") or msg:find("^A1;")) then
          sent[#sent + 1] = { msg = msg, ch = ch, target = target }
        end
        return api(p, msg, ch, target)
      end
      local function addon(text, ch, sender) _fire("CHAT_MSG_ADDON", TCF.DEV_PREFIX, text, ch, sender) end
      local function tick(sec) for i = 1, math.ceil(sec) do _update(1) end end
      local function answers() local n = 0 for _, s in ipairs(sent) do if s.ch == "WHISPER" then n = n + 1 end end return n end
      -- the checkbox: off by default, the tooltip says exactly what is shared, and with whom
      local cb = win.settingsShare
      ui.shareDev = nil; win:RefreshSettings()
      check(cb and not cb:GetChecked(), "sharing is off by default")
      local shareA = layoutItem("Share my cat's progress (developer stats and leaderboard)")
      check(shareA and shareA.kind == "check" and shareA.frame == cb, "the sharing checkbox is on the Settings page")
      tip = tipText(function() cb.scripts.OnEnter(cb) end)
      for _, words in ipairs({ "addon version", "class", "cat level", "zones cleared", "TapCoins",
                               "only shared with the addon's developer", "while you are both online", "Off by default",
                               "Chat Channels window", "can see your character's name",
                               "Realm leaderboard", "players on your realm", "total taps", "achievements earned",
                               "Adventure zones cleared", "never over the internet", "take you off their leaderboard", "Heroic Cache",
                               "every character on your account", "belong together", "Anyone who joins that channel",
                               "could also read what is shared", "hear it later" }) do
        check(tip:find(words, 1, true), "sharing tooltip says: " .. words)
      end
      check(not tip:find("!", 1, true), "no exclamation marks in the sharing tooltip")
      -- opted out: never joins, never answers, even the developer
      login(_charName)
      ui = TCF.db.ui
      tick(30)
      check(#joined == 0, "opted out: no channel joined")
      addon("Q1;111111", "GUILD", "Ziggu-Forever"); tick(5)
      check(answers() == 0, "opted out: no answer")
      -- opting in joins the hidden channel and takes it out of every chat window
      cb:SetChecked(true); cb.scripts.OnClick(cb)
      check(ui.shareDev == true, "the checkbox turns sharing on")
      tick(2)
      check(#joined == 1 and joined[1] == TCF.DEV_CHANNEL and removed[1] == TCF.DEV_CHANNEL, "joined the hidden channel and hid it")
      tick(3)
      check(#removed >= 2, "hidden again after the join came through")
      -- its notices never reach chat
      local filter = TCF.DevChatFilter
      check(filter(nil, "CHAT_MSG_CHANNEL_NOTICE", "YOU_JOINED", "", "", "7. " .. TCF.DEV_CHANNEL, "", "", 0, 7, TCF.DEV_CHANNEL) == true, "join notice filtered")
      check(filter(nil, "CHAT_MSG_CHANNEL_NOTICE", "YOU_JOINED", "", "", "1. General", "", "", 0, 1, "General") == false, "other channels untouched")
      check(filter(nil, "CHAT_MSG_CHANNEL", "hi", "Bob", "", _SECRET, "", "", 0, 1, _SECRET) == false, "secret channel names are left alone")
      -- only the developer gets an answer, only by whisper, at most once a minute
      addon("Q1;222222", "GUILD", "Bob-Forever"); tick(5)
      check(answers() == 0, "someone else asking: no answer")
      addon("Q1;222222", "WHISPER", "Ziggu-Forever"); tick(5)
      check(answers() == 0, "a whispered question is ignored")
      addon("Q1;333333", "GUILD", "Ziggu-Forever")
      addon("Q1;333333", "CHANNEL", "Ziggu-Forever")
      tick(5)
      check(answers() == 1, "one answer for a question heard twice: " .. answers())
      local a = sent[#sent]
      check(a.ch == "WHISPER" and a.target == "Ziggu-Forever", "answer whispered to the developer: " .. tostring(a.target))
      local nonce, rec = TCF.DevParseAnswer(a.msg)
      local mine = TCF:DevSummary()
      check(nonce == "333333" and rec and rec.class == TCF.db.class and rec.level == TCF:CD().level and rec.coins == math.floor(TCF.db.coins)
        and rec.zones == mine.zones and rec.version == mine.version, "the answer holds the five things: " .. a.msg)
      check(select(2, a.msg:gsub(";", "")) == 6, "and nothing else")
      addon("Q1;444444", "GUILD", "Ziggutrip-Forever"); tick(5)
      check(answers() == 1, "a new question within a minute: no second answer")
      tick(60)
      addon("Q1;444444", "PARTY", "Someone-Otherrealm"); tick(5)
      check(answers() == 1, "anyone else asking: no answer")
      check(TCF.DevIsDeveloperName("Ziggutrip-Otherrealm") and TCF.DevIsDeveloperName("Ziggu") and not TCF.DevIsDeveloperName("Zigguu-Forever"),
        "the developer's character names count on any realm")
      addon("Q1;444444", "PARTY", "Ziggutrip-Forever"); tick(5)
      check(answers() == 2 and sent[#sent].target == "Ziggutrip-Forever", "after a minute: answered")
      -- anything odd or secret is ignored without errors
      tick(61)
      for _, bad in ipairs({ { _SECRET, "GUILD", "Ziggu-Forever" }, { "Q1;555555", _SECRET, "Ziggu-Forever" }, { "Q1;555555", "GUILD", _SECRET },
                              { "Q1;", "GUILD", "Ziggu-Forever" }, { "Q1;55;55", "GUILD", "Ziggu-Forever" }, { "Q1;" .. string.rep("9", 40), "GUILD", "Ziggu-Forever" },
                              { "Q2;555555", "GUILD", "Ziggu-Forever" }, { "Q1;555555", "SAY", "Ziggu-Forever" }, { "Q1;555555", "GUILD", "" } }) do
        addon(bad[1], bad[2], bad[3])
      end
      _fire("CHAT_MSG_ADDON", _SECRET, "Q1;555555", "GUILD", "Ziggu-Forever")
      tick(5)
      check(answers() == 2, "odd or secret questions: no answer")
      -- turning it off leaves the channel and stops answering
      cb:SetChecked(false); cb.scripts.OnClick(cb)
      check(not ui.shareDev and left == 1 and channelId == 0, "off: left the hidden channel")
      addon("Q1;666666", "GUILD", "Ziggu-Forever"); tick(5)
      check(answers() == 2, "off: no answer")
      -- a join still on its way when sharing was turned off: left as soon as it comes through
      ui.shareDev = true; TCF:DevShareChanged(); tick(2)
      ui.shareDev = false; TCF:DevShareChanged()
      left = 0; channelId = 7
      DT.event("CHAT_MSG_CHANNEL_NOTICE", "YOU_JOINED", "", "", "7. " .. TCF.DEV_CHANNEL, "", "", 0, 7, TCF.DEV_CHANNEL)
      check(left == 1 and channelId == 0, "late join left again")
      channelId = 0
      -- the developer's side: /tcf players is only for the developer (or test mode)
      DT.reset(); sent = {}
      local c0 = #_chat
      SlashCmdList.TAPCATFOREVER("players")
      check(not (TCF.devView and TCF.devView:IsShown()) and #sent == 0, "not the developer: /tcf players does nothing")
      check(#_chat > c0 and _chat[#_chat]:find("/tapcat", 1, true), "and gets the usual help line")
      ui.testMode = true
      _group = { party1 = { "Alice", nil } }
      SlashCmdList.TAPCATFOREVER("players")
      local view = TCF.devView
      check(view and view:IsShown(), "test mode: /tcf players opens the window")
      local q = {}
      for _, s in ipairs(sent) do q[s.ch] = s.msg end
      check(q.GUILD and q.GUILD:match("^Q1;%d+$") and q.PARTY == q.GUILD, "asked over guild and group: " .. tostring(q.GUILD))
      check(not q.CHANNEL and joined[#joined] == TCF.DEV_CHANNEL, "joined the hidden channel to ask there")
      tick(2)
      check(sent[#sent].ch == "CHANNEL" and sent[#sent].target == 7 and sent[#sent].msg == q.GUILD, "asked over the hidden channel once joined")
      local askNonce = q.GUILD:match("^Q1;(%d+)$")
      -- asking again within TCF.DEV_ASK_GAP seconds sends nothing
      local n0 = #sent
      SlashCmdList.TAPCATFOREVER("players")
      check(#sent == n0 and _chat[#_chat]:find("ask again in", 1, true), "asking again too soon: " .. tostring(_chat[#_chat]))
      -- answers by whisper with this question's number are listed; anything else is not
      local function answer(sender, text, ch) addon(text, ch or "WHISPER", sender) end
      answer("Alice-Forever", "A1;" .. askNonce .. ";1.5.3;WARRIOR;42;7;12345")
      answer("Bob-Otherrealm", "A1;" .. askNonce .. ";1.5.2;PRIEST;12;1;99")
      answer("Carl-Forever", "A1;000000;1.5.3;WARRIOR;42;7;12345")             -- an old question
      answer("Dana-Forever", "A1;" .. askNonce .. ";1.5.3;WARRIOR;42;7;12345", "GUILD")   -- not a whisper
      answer("Eve-Forever", "A1;" .. askNonce .. ";1.5.3;DRAGON;42;7;12345")   -- no such class
      answer("Finn-Forever", "A1;" .. askNonce .. ";1.5.3;MAGE;0;7;12345")     -- level 0
      answer("Gus-Forever", "A1;" .. askNonce .. ";1.5.3;MAGE;5;7;99999999999999999999")
      answer("Hal-Forever", "A1;" .. askNonce .. ";1.5.3;MAGE;5;7;12;extra")
      answer(_SECRET, "A1;" .. askNonce .. ";1.5.3;MAGE;5;7;12")
      answer("Ivy-Forever", _SECRET)
      local rows = TCF:DevViewRows()
      check(#rows == 2 and rows[1].name == "Alice-Forever" and rows[1].level == 42 and rows[1].zones == 7 and rows[1].coins == 12345
        and rows[2].name == "Bob-Otherrealm" and rows[2].version == "1.5.2", "two good answers listed, highest level first: " .. #rows)
      tick(1)
      check(view.title:GetText() == "Players sharing their progress (2)", "window title: " .. tostring(view.title:GetText()))
      check(view.rows[1][1]:GetText() == "Alice-Forever" and view.rows[1][2]:GetText() == "Warrior" and view.rows[1][5]:GetText() == TCF.Commas(12345),
        "first row: " .. tostring(view.rows[1][1]:GetText()))
      check(view.status:GetText():find("guild, group, hidden channel", 1, true), "status line: " .. tostring(view.status:GetText()))
      -- the same player answering again replaces their row; at most 200 kept
      answer("Alice-Forever", "A1;" .. askNonce .. ";1.5.3;WARRIOR;43;7;12400")
      for i = 1, 250 do answer("Cat" .. i .. "-Forever", "A1;" .. askNonce .. ";1.5.3;ROGUE;3;0;10") end
      rows = TCF:DevViewRows()
      check(#rows == 200 and rows[1].level == 43, "at most 200 kept, one row per player: " .. #rows)
      -- you are listed too when you share (so the window can be tried alone)
      ui.shareDev = true
      rows = TCF:DevViewRows()
      local you
      for _, r in ipairs(rows) do if r.self then you = r end end
      check(you and you.name:find("(you)", 1, true) and you.class == TCF.db.class, "you are listed when you share")
      view.scripts.OnMouseWheel(view, -1); view:Refresh()
      check(view.scroll == 1, "the list scrolls")
      -- a real developer character can ask without test mode
      ui.testMode = nil
      tick(TCF.DEV_ASK_GAP + 1)
      _charName = "Ziggu"
      check(TCF:IsDeveloper(), "Ziggu is the developer")
      n0 = #sent
      SlashCmdList.TAPCATFOREVER("players")
      check(#sent > n0 and sent[n0 + 1].msg:match("^Q1;%d+$"), "the developer asks")
      _charName = "Ziggutrip"; check(TCF:IsDeveloper(), "Ziggutrip too")
      _charName = "Zigguu"; check(not TCF:IsDeveloper(), "other names are not")
      GetNormalizedRealmName = function() return "Otherrealm" end
      _charName = "Ziggu"; check(TCF:IsDeveloper(), "the developer's names count on any realm")
      GetNormalizedRealmName = function() return "Forever" end
      _charName = mainChar
      check(TCF:DevViewRows()[1] and #TCF:DevViewRows() == 1, "a new question starts a fresh list (only you)")
      -- put everything back
      view:Hide()
      _group = nil
      DT.reset()
      C_ChatInfo.SendAddonMessage = api
      JoinTemporaryChannel, LeaveChannelByName, GetChannelName, IsInGuild, ChatFrame_RemoveChannel = nil, nil, nil, nil, nil
      DT.setDevKeys(shippedDevKeys); GetNormalizedRealmName = nil
      for _, k in ipairs(KEYS) do ui[k] = saved[k] end
      ui.point, ui.hudLayout = saved.point, saved.hudLayout
      TCF.hud:ApplySettings()
      if win:IsShown() then win:RefreshSettings() end
      print("UI section (text distance, chest coin line, developer view): all checks passed")
    end
    -- ===== end of UI section =====
    -- ===== Review fixes section (1.5.3, review-fix builder): no stat-less loot, leftover test items
    -- taken off old saves, starter swaps that keep the player's off-hand and Power, XP carried over to
    -- the new curve, the TapCoin cap per paid tap, the developer known by name and realm, the channel
    -- join limit, and "Max level" at the cap =====
    do
      local before = _charName
      -- F1. loot pools: nothing Uncommon or better without stats, nothing Rare or better at item level 1-5
      local nPool, nBoss = 0, 0
      local function scan(list, where)
        for _, it in ipairs(list or {}) do
          nPool = nPool + 1
          check(not it.retired and not it.placeholder, "a retired item in " .. where .. ": " .. it.name)
          check(not (it.q >= 2 and (it.statStr or "") == ""), "an item with no stats drops (" .. where .. "): " .. it.name)
          check(not (it.q >= 3 and it.ilvl <= 5), "a Rare or better item at item level " .. it.ilvl .. " drops: " .. it.name)
        end
      end
      for band, list in pairs(TCF.WORLD_POOL) do scan(list, "world band " .. band) end
      for tier, list in pairs(TCF.TIER_POOL) do scan(list, "tier " .. tier) end
      for tier, bosses in pairs(TCF.BOSS_LOOT) do
        for boss, list in pairs(bosses) do
          nBoss = nBoss + 1
          check(#list > 0, "boss " .. tier .. "/" .. boss .. " still has loot")
          scan(list, "boss " .. tier .. "/" .. boss)
        end
      end
      check(nPool > 5000 and nBoss > 50, "pools scanned: " .. nPool .. " items, " .. nBoss .. " bosses")
      local talisman
      for _, it in ipairs(TCF.GEAR_LIST) do if it.name == "Talisman of Arathor" then talisman = it end end
      check(talisman and talisman.retired and not talisman.placeholder, "Talisman of Arathor (no stats) no longer drops, owners keep it")
      for _, id in ipairs({ 38692, 33292, 50287, 46349 }) do
        local it = TCF.GEAR[id]
        check(it and it.placeholder and it.retired, "a leftover test item is a placeholder: " .. id)
      end
      local bcGreen
      for _, it in ipairs(TCF.GEAR_LIST) do
        if it.retired and not it.placeholder and not it.suffix and it.q == 2 and (it.statStr or "") ~= ""
          and not TCF.IsClassicItem(it.id, it.ilvl) then bcGreen = it; break end
      end
      check(bcGreen, "a later-expansion green with stats")
      check(not TCF:CanEquipGear(TCF.GEAR[38692], "DRUID"), "a placeholder can't be equipped")

      -- F2. a 1.5.2 save: placeholders worn and in bags go (paid), later-expansion gear stays, a cat
      -- left without a weapon gets its starter, and XP keeps its share of the level on the new curve
      local ui0 = TapCatForeverDB.ui and TapCatForeverDB.ui.chat
      TapCatForeverDB.ui = TapCatForeverDB.ui or {}
      TapCatForeverDB.ui.chat = true
      local paid0 = TapCatForeverDB.levelPaid
      local oldNeed10, oldNeed50 = math.floor(120 * 10 ^ 1.25), math.floor(120 * 50 ^ 1.25)
      TapCatForeverDB.chars["Fixold-Forever"] = { class = "DRUID", classData = {
        DRUID = { level = 10, xp = 2100, gear = { MAINHAND = 38692 }, bag = { [38692] = 1 }, starterFixed = true, starterFixed2 = true },
        WARRIOR = { level = 50, xp = 15000, gear = { HEAD = 33292 }, bag = { [33292] = 1, [50287] = 2, [bcGreen.id] = 1 },
          starterFixed = true, starterFixed2 = true },
        MAGE = { level = 70, xp = 5 },
      } }
      local want = TCF:GearSellValue(TCF.GEAR[38692]) + TCF:GearSellValue(TCF.GEAR[33292]) + 2 * TCF:GearSellValue(TCF.GEAR[50287])
      local c0 = #_chat
      login("Fixold")
      local druid, warrior, mage = TCF:CD("DRUID"), TCF:CD("WARRIOR"), TCF:CD("MAGE")
      local function holds(class, id)
        if TCF:Bag(class)[id] then return true end
        for _, v in pairs(TCF:GearEquipped(class)) do if v == id then return true end end
        return false
      end
      for _, cl in ipairs(TCF.CLASSES) do
        check(TCF:CD(cl.key).placeholderFixed, cl.key .. " placeholder pass flag")
        for id in pairs(TCF:Bag(cl.key)) do check(not TCF.GEAR[id] or not TCF.GEAR[id].placeholder, cl.key .. " bag still holds a placeholder: " .. id) end
        for slot, id in pairs(TCF:GearEquipped(cl.key)) do check(not TCF.GEAR[id] or not TCF.GEAR[id].placeholder, cl.key .. " still wears a placeholder in " .. slot) end
      end
      check(not holds("DRUID", 38692) and not holds("WARRIOR", 33292) and not holds("WARRIOR", 50287), "leftover test items are gone")
      check(TCF:GearEquipped("DRUID").MAINHAND == TCF:StarterWeapon("DRUID").id, "the druid got its starter back in the main hand")
      check(TCF:Bag("WARRIOR")[bcGreen.id] == 1, "later-expansion gear stays: " .. bcGreen.name)
      local line, nLines = nil, 0
      for i = c0 + 1, #_chat do if _chat[i]:find("leftover test", 1, true) then line = _chat[i]; nLines = nLines + 1 end end
      check(line and line:find("4 leftover test items with no stats were taken off your cats. You got " .. want .. " TapCoins for them.", 1, true),
        "one plain chat line names the count and the TapCoins: " .. tostring(line))
      check(nLines == 1 and not line:find("!", 1, true), "only one line, no exclamation marks: " .. nLines)
      check(druid.level == 10 and druid.xp == math.floor(TCF.XPForLevel(10) * math.min(0.99, 2100 / oldNeed10)) and druid.xp == 927,
        "level 10 at 2,100 of 2,133 becomes 927 of 942: " .. druid.xp)
      check(warrior.level == 50 and warrior.xp == math.floor(TCF.XPForLevel(50) * 15000 / oldNeed50) and warrior.xp < TCF.XPForLevel(50),
        "level 50 keeps its share of the level: " .. warrior.xp .. " / " .. TCF.XPForLevel(50))
      check(mage.level == 60 and mage.xp == TCF.XPForLevel(60), "a cat above 60 is 60 with a full bar")
      check(druid.xpCurve2 and warrior.xpCurve2 and TCF:CD("ROGUE").xpCurve2, "XP carried over once for every cat")
      -- logging in again changes nothing
      local snap = { coins = TCF.db.coins, dxp = druid.xp, wxp = warrior.xp, dmain = TCF:GearEquipped("DRUID").MAINHAND, n = #_chat }
      login("Fixold")
      druid, warrior = TCF:CD("DRUID"), TCF:CD("WARRIOR")
      check(druid.xp == snap.dxp and warrior.xp == snap.wxp and TCF:GearEquipped("DRUID").MAINHAND == snap.dmain, "a second login changes no XP or gear")
      local again = false
      for i = snap.n + 1, #_chat do if _chat[i]:find("leftover test", 1, true) then again = true end end
      check(not again, "no second chat line")

      -- F3. the 1.5.3 starter swap keeps a priest's held item (and its mace); with nothing in the
      -- off hand, the new staff goes on
      local peq, pbag, pcd = TCF:GearEquipped("PRIEST"), TCF:Bag("PRIEST"), TCF:CD("PRIEST")
      check(TCF.GEAR[5611] and TCF.GEAR[5611].slot == "HOLD" and TCF.GEAR[3223].slot ~= "2H" and TCF.GEAR[9603].slot == "2H", "test items: a held item, the old mace, the new staff")
      check(TCF:StarterWeapon("PRIEST").id == 9603, "the priest's starter is Gritroot Staff")
      for k in pairs(peq) do peq[k] = nil end
      for k in pairs(pbag) do pbag[k] = nil end
      peq.MAINHAND, peq.OFFHAND, pbag[3223], pbag[5611] = 3223, 5611, 1, 1
      pcd.starterFixed2 = nil; TCF:FixStarterWeapons()
      check(peq.MAINHAND == 3223 and peq.OFFHAND == 5611 and (pbag[9603] or 0) >= 1, "a priest with a held item keeps both, the staff waits in the bag")
      for k in pairs(peq) do peq[k] = nil end
      for k in pairs(pbag) do pbag[k] = nil end
      peq.MAINHAND, pbag[3223] = 3223, 1
      pcd.starterFixed2 = nil; TCF:FixStarterWeapons()
      check(peq.MAINHAND == 9603 and peq.OFFHAND == nil and pbag[3223] == 1, "a priest with an empty off hand gets the staff")
      -- a level 1 cat can wear its own starter, whatever the weapon's level
      for _, cl in ipairs(TCF.CLASSES) do
        local cd, w = TCF:CD(cl.key), TCF:StarterWeapon(cl.key)
        local lv = cd.level
        cd.level = 1
        local bag = TCF:Bag(cl.key)
        local had = bag[w.id]
        bag[w.id] = (had or 0) + 1
        check(TCF:CanEquipGear(w, cl.key), cl.key .. " can wear its starter " .. w.name .. " (level " .. w.req .. ") at level 1")
        local tip = tipText(function() TCF:GearTooltip(GameTooltip, w, cl.key) end)
        check(w.req <= 1 or (tip:find("any level", 1, true) and not tip:find("Requires class level", 1, true)), cl.key .. " starter tooltip: " .. tip)
        bag[w.id] = had
        cd.level = lv
      end
      local other
      for _, it in ipairs(TCF.GEAR_LIST) do if it.req >= 20 and it.slot == "2H" and TCF:GearUsable(it, "DRUID") then other = it; break end end
      TCF:Bag("DRUID")[other.id] = 1
      check(not TCF:CanEquipGear(other, "DRUID"), "other gear still needs its level")
      TCF:Bag("DRUID")[other.id] = nil

      -- F4. TapCoins from tapping: the first 10 taps of every second earn, at any speed
      _group = nil
      TCF:SetClass("DRUID")
      local function value() return TCF.db.coins + TCF.db.coinFrac end
      local function run(rate, secs)
        _clock = _clock + 5
        local v0, t0 = value(), TCF.db.taps
        local start = _clock
        for i = 0, rate * secs - 1 do _clock = start + i / rate; TCF:Tap() end
        _clock = start + secs
        return math.floor((value() - v0) / 0.02 + 0.5), TCF.db.taps - t0
      end
      local p12, t12 = run(12, 10)
      check(p12 >= 99 and p12 <= 100 and t12 == 120, "12 taps a second: about 10 a second earn, all count: " .. p12 .. ", " .. t12)
      local p10 = run(10, 10)
      check(p10 == 100, "10 taps a second: all earn: " .. p10)
      local p15 = run(15, 10)
      check(p15 >= 99 and p15 <= 100, "15 taps a second: still 10 a second earn: " .. p15)
      local p8 = run(8, 10)
      check(p8 == 80, "8 taps a second: all earn: " .. p8)

      -- F5. developer view: the next question is answered, and the channel join gives up
      local DT = TCF.DevTest
      DT.reset()
      check(TCF.DEV_ASK_GAP >= TCF.DEV_ANSWER_GAP + 4, "the developer can't ask before players can answer again")
      GetNormalizedRealmName = function() return "Forever" end
      local shipped = DT.setDevKeys({ DT.keyHash("ziggu-forever") })
      local sent, joins, chan = {}, 0, 0
      local api = C_ChatInfo.SendAddonMessage
      C_ChatInfo.SendAddonMessage = function(p, msg, ch, target)
        if p == TCF.DEV_PREFIX and type(msg) == "string" and msg:find("^A1;") then sent[#sent + 1] = { msg = msg, target = target } end
        return api(p, msg, ch, target)
      end
      JoinTemporaryChannel = function() joins = joins + 1 end   -- the join never comes through
      GetChannelName = function() return chan end
      local function tick(sec) for i = 1, math.ceil(sec) do _update(1) end end
      local function ask(n, sender) _fire("CHAT_MSG_ADDON", TCF.DEV_PREFIX, "Q1;" .. n, "GUILD", sender) end
      TCF.db.ui.shareDev = true; TCF:DevShareChanged()
      ask(101, "Ziggu"); tick(5)   -- no realm: the player's own
      check(#sent == 1 and sent[1].target == "Ziggu", "a sender without a realm is on your realm: " .. #sent)
      tick(TCF.DEV_ASK_GAP - 5)
      ask(102, "Ziggu-Forever"); tick(5)
      check(#sent == 2, "asked again after DEV_ASK_GAP: answered again")
      ask(103, "Ziggu-Elsewhere"); tick(TCF.DEV_ASK_GAP)
      check(#sent == 2, "the right name on the wrong realm: no answer")
      for i = 1, 6 do DT.event("PLAYER_REGEN_ENABLED"); tick(2) end
      check(joins <= 3 and DT.state().joinGaveUp, "a join that never comes through is tried at most 3 times: " .. joins)
      DT.event("PLAYER_REGEN_ENABLED"); tick(2)
      check(joins <= 3 and not DT.state().joinAt, "and not again after fights")
      TCF.db.ui.shareDev = false; TCF:DevShareChanged()
      TCF.db.ui.shareDev = true; TCF:DevShareChanged(); tick(2)
      local j0 = joins
      check(j0 >= 1 and not DT.state().joinGaveUp, "turning sharing on again gives a fresh try")
      DT.event("CHAT_MSG_CHANNEL_NOTICE", "WRONG_PASSWORD", "", "", "", "", "", 0, 0, TCF.DEV_CHANNEL)
      for i = 1, 3 do DT.event("PLAYER_REGEN_ENABLED"); tick(2) end
      check(joins == j0 and DT.state().joinGaveUp, "a wrong password for the channel: no more joins")
      TCF.db.ui.shareDev = false; TCF:DevShareChanged()
      C_ChatInfo.SendAddonMessage = api
      JoinTemporaryChannel, GetChannelName = nil, nil
      DT.setDevKeys(shipped); GetNormalizedRealmName = nil
      DT.reset()

      -- F6. at the cap the Profile says "Max level" and the cat's level says (max)
      local win = TCF.window
      local cd = TCF:CD()
      local lv, xp = cd.level, cd.xp
      cd.level, cd.xp = TCF.MAX_LEVEL, TCF.XPForLevel(TCF.MAX_LEVEL)
      local f0 = #_frames
      win:RefreshLight(); TCF.hud:Refresh()
      local maxText = false
      for _, f in ipairs(_frames) do if f.text == "Max level" then maxText = true end end
      check(maxText, "the Profile's XP text says Max level")
      check(TCF.hud.level:GetText():find("Lv 60 (max)", 1, true), "the cat's level says (max): " .. tostring(TCF.hud.level:GetText()))
      cd.level, cd.xp = 10, 5
      win:RefreshLight(); TCF.hud:Refresh()
      check(not TCF.hud.level:GetText():find("(max)", 1, true), "no (max) below the cap")
      cd.level, cd.xp = lv, xp

      -- put everything back
      TapCatForeverDB.ui.chat = ui0
      TapCatForeverDB.levelPaid = paid0
      login(before)
      TapCatForeverDB.chars["Fixold-Forever"] = nil
      print("review fixes section (loot, saves, starters, XP, TapCoins, developer view, max level): all checks passed")
    end
    -- ===== end of review fixes section =====
    print("class professions, crafted gear, party cats and loot notices: all checks passed")
    end
    -- every referenced art file must exist
    local missing = {}
    for path in pairs(_textures) do
      local f = path:match("AddOns\\TapCatForever\\Art\\(.+)$")
      if f then _artcheck[#_artcheck + 1] = f end
    end
    print("chat lines:", #_chat)
    -- plain English for players: no exclamation marks in chat lines or achievement names and texts
    for _, line in ipairs(_chat) do assert(not line:find("!", 1, true), "exclamation mark in a chat line: " .. line) end
    for _, a in ipairs(TCF.ACHIEVEMENTS) do
      assert(not a.name:find("!", 1, true), "exclamation mark in an achievement name: " .. a.name)
      assert(not (a.desc or ""):find("!", 1, true), "exclamation mark in an achievement text: " .. tostring(a.desc))
    end
    for _, n in ipairs(TCF.NEWS) do
      assert(not (n.highlight or ""):find("!", 1, true), "exclamation mark in the What's new note for " .. n.version)
      assert(not n.highlight or #n.highlight <= 170, "What's new note too long for the strip: " .. n.version)
    end
    for i = 1, 6 do print("  " .. _chat[i]) end
    for i = #_chat - 3, #_chat do print("  " .. _chat[i]) end
    '''

# ---- capes art (1.5.3, side drapes): gear cloaks and the cosmetic cape hang down both sides of the cat
# and tuck in behind its body; nothing may run across the bottom under the paws
def check_capes_art():
    import re as _re, json
    V = {}
    for m in _re.finditer(r'V\["([^"]+)"\]=\{"([^"]+)",(\d+),(\d+),(\d+),(\d+),[\d.]+,[\d.]+,"(\w+)"\}', open(os.path.join(ROOT, "VectorData.lua")).read()):
        k, t, x, y, w, h, kind = m.groups(); V[k] = (t, int(x), int(y), int(w), int(h), kind)
    specs = [l.strip() for l in open(os.path.join(ROOT, "tools", "item_specs", "back.txt")) if l.strip() and not l.startswith("#")]
    keys = json.load(open(os.path.join(ROOT, "tools", "item_specs", "groups.json")))["back"]
    capes = [k for k, sp in zip(keys, sorted(specs, key=lambda s: int(s.split(":")[0]))) if sp.split(":", 1)[1].split()[0] == "cloak"]
    capes += ["cos:back_cape:a", "cos:back_cape:b", "cos:back_cape:f"]
    assert len(capes) >= 20, "capes art: too few cloak drawings found (%d)" % len(capes)
    for k in capes:
        assert k in V, "capes art: no drawing for " + k
        t, x, y, w, h, kind = V[k]
        assert kind == "back", "capes art: %s is not a back drawing" % k
        assert os.path.exists(os.path.join(ROOT, "Art", "v", t + ".tga")), "capes art: missing texture " + t
        # the old capes ended at 494 with a band under the paws; the drapes stop at the paws (460)
        assert y + h <= 470, "capes art: %s reaches %d, below the paws" % (k, y + h)
        assert w >= 340, "capes art: %s is too narrow to show on both sides (%d)" % (k, w)
    print("capes art (side drapes, %d drawings): all checks passed" % len(capes))

# ---- leaderboard section (1.5.3, realm leaderboard): several fake clients, each its own Lua state with
# the addon loaded, share one realm clock and one hidden channel. The test routes every channel message
# to the others, so the board has to spread by gossip; then the extra fields (L2) and a client that
# only knows L1, merge rules, caps, expiry, opt-out, the sign-up chest, odd or secret input, the rate
# limits, and the Leaderboard tab (opt-in panel, Join and Leave, sections).
LB_KINDS = ("L1;", "L2;", "R1;", "X1;")
# the L1 pattern of the first 1.5.3 builds: what a client that doesn't know L2 reads
OLD_L1 = re.compile(r"^L1;([^;|]+);([A-Z]+);(\d+);(\d+);(\d+);(\d+);([A-Za-z0-9.\-]+);(\d+)$")
# GameFontNormal (Friz Quadrata, 12 px): a rough, generous width of a label in pixels
def est_width(text):
    w = 0.0
    for ch in text:
        if ch in "il.,'|": w += 3.5
        elif ch in "fjrt ": w += 4.5
        elif ch in "mw": w += 10
        elif ch in "MW": w += 11.5
        elif ch.isupper(): w += 8.5
        elif ch.isdigit(): w += 7
        else: w += 6.8
    return w
LB_CLIENT = r"""
_srv = 1800000000
function GetServerTime() return _srv end
function GetNormalizedRealmName() return "Forever" end
_chanId, _joins = 0, 0
function JoinTemporaryChannel(name) _joins = _joins + 1; _chanId = 7 end
function LeaveChannelByName() _chanId = 0 end
function GetChannelName(n) return _chanId end
_out = {}
C_ChatInfo.SendAddonMessage = function(p, msg, ch, target)
  if _sendResult == 0 then table.insert(_out, { p, msg, ch, target }) end
  return _sendResult
end
function _deliver(p, msg, sender, chan, chanName)
  _fire("CHAT_MSG_ADDON", p, msg, chan or "CHANNEL", sender, "", 0, 7, chanName or "TapCatFvrShare", 0)
end
function _tick(n, srv) for i = 1, n do _srv = srv + i; _update(1) end end
function _boardKeys()
  local b = TapCatForever.LeaderboardBoard(false)
  local t = {}
  if b then for k in pairs(b.e) do t[#t + 1] = k end end
  table.sort(t)
  return table.concat(t, ",")
end
function _boardCount()
  local b = TapCatForever.LeaderboardBoard(false)
  local n = 0
  if b then for _ in pairs(b.e) do n = n + 1 end end
  return n
end
function _entry(k)
  local b = TapCatForever.LeaderboardBoard(false)
  return b and b.e[k]
end
function _optIn(on) TapCatForever.db.ui.shareDev = on; TapCatForever:DevShareChanged() end
function _takeOut() local o = _out; _out = {}; return o end
"""

def check_leaderboard(seed=1):
    srv = [1800000000]
    clients = {}
    log = []        # (srv, sender, msg, ch, target)
    def ck(c, m):
        if not c: raise AssertionError("leaderboard: " + m)

    class Client:
        def __init__(self, name, cls, opted=False, before=None):
            self.name, self.full = name, name + "-Forever"
            self.lua = load_addon(login=False)
            self.lua.execute(LB_CLIENT)
            self.lua.execute("math.randomseed(%d)" % ((seed + sum(map(ord, name)) * 7919) % 2147483647))
            self.lua.execute('_charName = "%s"; _srv = %d' % (name, srv[0]))
            if before: self.lua.execute(before)
            self.lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
            self.lua.execute('TapCatForever.db.class = "%s"' % cls)
            self.online = True
            self.sent = []   # (srv, msg)
            clients[name] = self
        def ev(self, expr): return self.lua.eval(expr)
        def ex(self, code): return self.lua.execute(code)
        def heroic(self): return self.ev("TapCatForever.db.keys.heroic or 0")
        def key(self, name): return (name + "-forever").lower()

    def step(n=1):
        for _ in range(n):
            for c in clients.values():
                if c.online: c.lua.globals()._tick(1, srv[0])
            srv[0] += 1
            for c in list(clients.values()):
                if not c.online: continue
                out = c.lua.globals()._takeOut()
                for i in range(1, len(out) + 1):
                    p, msg, ch, target = out[i][1], out[i][2], out[i][3], out[i][4]
                    c.sent.append((srv[0], msg))
                    log.append((srv[0], c.name, msg, ch, target))
                    ck(p == "TapCatFvr", "prefix " + str(p))
                    if msg[:3] not in LB_KINDS: continue
                    ck(ch == "CHANNEL" and target in (7, "7"), "leaderboard messages only go to the hidden channel when not grouped: %s %s" % (ch, target))
                    ck(len(msg) <= 255, "message too long")
                    for d in clients.values():   # everyone in the channel hears it, the sender too (echo)
                        if d.online and d.ev("_chanId") > 0:
                            d.lua.globals()._deliver(p, msg, c.full)

    def lbmsgs(c, since=0): return [m for (t, m) in c.sent if t > since and m[:3] in LB_KINDS]
    def xstr(c, k):   # entry k's extra fields on c's board, as one string (None without them)
        return c.ev('(function() local e = _entry("%s"); if not e or not e.x then return nil end; local x = e.x; '
                    'return table.concat(x.lv, ".") .. "|" .. TapCatForever.LeaderboardBigText(x.g) .. "|" .. table.concat(x.sk, ".") end)()' % k)
    def own_x(c):
        return c.ev('(function() local x = TapCatForever:LeaderboardOwnExtra(); '
                    'return table.concat(x.lv, ".") .. "|" .. TapCatForever.LeaderboardBigText(x.g) .. "|" .. table.concat(x.sk, ".") end)()')
    def page(c): return c.lua.eval("TapCatForever.leaderboardView")
    def click(c, path): c.ex("local b = %s; b.scripts.OnClick(b)" % path)

    # 0. a player who never opts in: joins nothing, sends nothing, reads nothing, sees no board
    E = Client("Echo", "DRUID")
    step(120)
    ck(E.ev("_joins") == 0 and lbmsgs(E) == [], "opted out: no channel, no messages")
    E.lua.globals()._deliver("TapCatFvr", "L1;Zed-Forever;MAGE;5;100;1;0;1.5.3;%d" % srv[0], "Zed-Forever")
    ck(E.ev("_boardCount()") == 0 and E.ev("#TapCatForever:LeaderboardRows()") == 0, "opted out: nothing read, no rows")
    h0 = E.heroic()

    # 1. Alpha and Cedric opt in together. Alpha gets the sign-up chest once, with one chat line
    A = Client("Alpha", "WARRIOR")
    C = Client("Cedric", "MAGE")
    # Alpha's other cats and trade: a level 17 Mage cat, Trade Gold and a few skills (the extra fields)
    A.ex("""local TCF = TapCatForever
      TCF.db.classData.MAGE.level = 17
      local s = TCF:ProfState("WARRIOR"); s.lifetime = 1234567890123; s.skill.blacksmithing = 150; s.skill.herbalism = 42""")
    ha, chat0 = A.heroic(), A.ev("#_chat")
    A.ex("_optIn(true)"); C.ex("_optIn(true)")
    ck(A.heroic() == ha + 1, "sign-up: a Heroic Cache")
    lines = [A.ev("_chat[%d]" % i) for i in range(chat0 + 1, A.ev("#_chat") + 1)]
    ck(len(lines) == 1 and "Heroic Cache" in lines[0] and "leaderboard" in lines[0] and "!" not in lines[0], "one plain chat line: %r" % lines)
    ck(A.ev("TapCatForever.db.ui.lbSignupChest") == True, "the sign-up chest is remembered for the account")
    step(90)
    ck(A.ev("_joins") >= 1 and A.ev("_chanId") == 7, "opting in joins the hidden channel")
    ck(A.ev("_boardKeys()") == "cedric-forever" and C.ev("_boardKeys()") == "alpha-forever", "two players online together see each other: %s / %s" % (A.ev("_boardKeys()"), C.ev("_boardKeys()")))
    ck(len([m for m in lbmsgs(A) if m.startswith("L1;Alpha-Forever;WARRIOR;")]) == 1, "Alpha shared its own summary once")
    own = [m for m in lbmsgs(A) if m[:3] in ("L1;", "L2;")]
    ck(len(own) == 2 and own[0].startswith("L1;") and own[1].startswith("L2;Alpha-Forever;"), "its L2 right after its L1: %r" % own)
    ck(OLD_L1.match(own[0]), "the L1 is unchanged, so builds that only know L1 still read it: " + own[0])
    ck(own[1].split(";")[3] == "1.1.1.1.1.1.17.1.1" and own[1].split(";")[4] == "1234567e6" and own[1].split(";")[5] == "150.1.1.42.1.1.1",
       "L2 holds every class cat's level, Trade Gold and the best skills: " + own[1])
    ck(xstr(C, "alpha-forever") == own_x(A), "Cedric has Alpha's extra fields: %s" % xstr(C, "alpha-forever"))
    e = C.ev('_entry("alpha-forever")')
    ck(e.c == "WARRIOR" and e.l == A.ev("TapCatForever:CD().level") and e.t == A.ev("TapCatForever.db.taps") and e.v == A.ev("TapCatForever:DevSummary().version"), "the summary holds the right numbers")
    for c in (A, C):
        ck(c.ev("_chat[#_chat]").find("TapCatFvr") < 0 and all("L1;" not in c.ev("_chat[%d]" % i) for i in range(1, c.ev("#_chat") + 1)), "nothing about the channel prints in chat")

    # 2. Alpha logs off; Cedric stays a while
    A.online = False
    step(30 * 60)
    ck(len([m for m in lbmsgs(C) if m.startswith("L1;Cedric")]) >= 2, "a summary again every 12 to 15 minutes")

    # 3. Bravo, never online with Alpha, logs in and opts in: Cedric passes Alpha on
    B = Client("Bravo", "PRIEST")
    # Bravo joins from the Leaderboard tab: the opt-in panel, then the big Join button
    hb = B.heroic()
    B.ex("TapCatForever:ShowLeaderboard()")
    ck(B.ev("TapCatForever.window:IsShown() and TapCatForever.window.tab == TapCatForever.window.TAB_LEADERBOARD"), "/tcf top opens the Leaderboard tab")
    ck(B.ev("TapCatForever.leaderboardView.join:IsShown()") and not B.ev("TapCatForever.leaderboardView.board:IsShown()"),
       "not joined: the tab shows the opt-in panel, not the board")
    jt = "\n".join(B.ev("TapCatForever.leaderboardView.joinText[%d]:GetText()" % i) for i in range(1, B.ev("#TapCatForever.leaderboardView.joinText") + 1))
    for words in ("your realm", "name and realm", "class cats", "total taps", "achievements earned", "Adventure zones cleared",
                  "Trade Gold", "profession skills", "addon version", "Nothing else", "joined too", "through the addon",
                  "no internet", "nothing shows in your chat", "could read", "every character on your account", "developer", "leave at any time"):
        ck(words in jt, "the opt-in panel says: " + words)
    ck("!" not in jt, "no exclamation marks on the opt-in panel")
    ck("first time you join" in B.ev("TapCatForever.leaderboardView.joinReward:GetText()") and "Heroic Cache" in B.ev("TapCatForever.leaderboardView.joinReward:GetText()"),
       "the panel offers the Heroic Cache")
    ck(B.ev("TapCatForever.leaderboardView.joinBtn:GetText()") == "Join the leaderboard", "the big Join button")
    ck(not B.ev("TapCatForever.db.ui.shareDev") and B.ev("_joins") == 0, "nothing turned on just by looking")
    click(B, "TapCatForever.leaderboardView.joinBtn")
    ck(B.ev("TapCatForever.db.ui.shareDev") == True and B.heroic() == hb + 1, "Join turns sharing on and gives the Heroic Cache")
    B.ex("TapCatForever.window:SelectTab(TapCatForever.window.TAB_SETTINGS)")
    ck(B.ev("TapCatForever.window.settingsShare:GetChecked()") == True, "the Settings checkbox follows")
    B.ex("TapCatForever.window:SelectTab(TapCatForever.window.TAB_LEADERBOARD)")
    ck(B.ev("TapCatForever.leaderboardView.board:IsShown()") and not B.ev("TapCatForever.leaderboardView.join:IsShown()"), "after joining the tab shows the board")
    ck(B.ev("TapCatForever.leaderboardView.rows[1].entry.self") == True and B.ev("TapCatForever.leaderboardView.rows[1].hl:IsShown()"), "your own row, highlighted")
    step(180)
    ck(B.ev("_joins") >= 1, "Join joins the hidden channel")
    ck(B.ev("_boardKeys()") == "alpha-forever,cedric-forever", "gossip: Bravo learned about Alpha from Cedric: " + B.ev("_boardKeys()"))
    ck(xstr(B, "alpha-forever") == own_x(A), "gossip carries the extra fields too: %s" % xstr(B, "alpha-forever"))

    # 4. Cedric logs off, Delta logs in with only Bravo online: gets Alpha and Cedric from Bravo
    C.online = False
    step(20 * 60)
    D = Client("Delta", "ROGUE")
    D.ex("_optIn(true)")
    step(180)
    ck(D.ev("_boardKeys()") == "alpha-forever,bravo-forever,cedric-forever", "gossip reaches Delta: " + D.ev("_boardKeys()"))

    # 5. Alpha comes back (a reload) at a higher level: the newer summary replaces the old one everywhere
    A.online = True
    A.ex("TapCatForever.LeaderboardTest.reset(); TapCatForever:CD().level = 30; TapCatForever.db.taps = 123456; _fire('PLAYER_LOGIN')")
    step(120)
    for c in (B, D):
        e = c.ev('_entry("alpha-forever")')
        ck(e and e.l == 30 and e.t == 123456, c.name + " has Alpha's newer summary")
    ck(A.heroic() == ha + 1, "no second sign-up chest after a reload")
    newTs = D.ev('_entry("alpha-forever").ts')
    old = "L1;Alpha-Forever;WARRIOR;3;50;1;0;1.5.3;%d" % (newTs - 3600)
    D.lua.globals()._deliver("TapCatFvr", old, "Bravo-Forever")
    ck(D.ev('_entry("alpha-forever").l') == 30, "an older copy passed on later never replaces a newer one")
    forged = "L1;Delta-Forever;ROGUE;60;999999999;80;28;1.5.3;%d" % (srv[0] + 1)
    D.lua.globals()._deliver("TapCatFvr", forged, "Bravo-Forever")
    ck(D.ev('_entry("delta-forever")') is None, "your own entry never comes from someone else")
    # a big change sends sooner (a level), but not more often than every 5 minutes
    n0 = len(lbmsgs(A))
    A.ex("TapCatForever:CD().level = 31")
    step(6 * 60)
    ck(any(m.startswith("L1;Alpha-Forever;WARRIOR;31;") for m in lbmsgs(A)[n0:]), "a new level is shared within minutes")
    ck(D.ev('_entry("alpha-forever").l') == 31, "and reaches the others")

    # 5b. the extra fields (L2): a skill-up is shared within minutes; newest wins; an L2 never adds a
    # player; a client that only knows L1 still sees and is seen on Total taps and its own class
    n0 = len(lbmsgs(A))
    A.ex('TapCatForever:ProfState("WARRIOR").skill.blacksmithing = 200')
    step(6 * 60)
    ck(any(m.startswith("L2;Alpha-Forever;") and m.split(";")[5].startswith("200.") for m in lbmsgs(A)[n0:]), "10 more skill points are shared within minutes")
    ck(xstr(D, "alpha-forever") == own_x(A) and xstr(B, "alpha-forever") == own_x(A), "and reach the others: %s" % xstr(D, "alpha-forever"))
    D.ex(r"""
      local TCF = TapCatForever
      local b, t = TCF.LeaderboardBoard(false), _srv
      _r = {}
      local e = b.e["alpha-forever"]
      local xts = e.xts
      _r.older = select(2, TCF.LeaderboardMergeExtra(b, "alpha-forever", { lv = { 1, 1, 1, 1, 1, 1, 1, 1, 1 }, g = 1, sk = { 1, 1, 1, 1, 1, 1, 1 } }, xts - 10, t))
      _r.kept = e.x.sk[1] == 200
      _r.unknown = select(2, TCF.LeaderboardMergeExtra(b, "nobody-forever", e.x, t, t))
      _r.self = select(2, TCF.LeaderboardMergeExtra(b, "delta-forever", e.x, t, t, "delta-forever"))
      _r.future = select(2, TCF.LeaderboardMergeExtra(b, "alpha-forever", e.x, t + 3600, t))
      -- a newer L1 keeps the extra fields until the next L2
      TCF.LeaderboardMerge(b, { n = e.n, c = e.c, l = e.l, t = e.t + 5, a = e.a, z = e.z, v = e.v, ts = e.ts + 1 }, t)
      _r.keptAfterL1 = b.e["alpha-forever"].x ~= nil and b.e["alpha-forever"].xts == xts
      -- the sections
      local function find(list, n) for _, r in ipairs(list) do if r.n == n then return r end end end
      local mage = TCF:LeaderboardSection("class", "MAGE")
      _r.mageAlpha = find(mage, "Alpha-Forever") and find(mage, "Alpha-Forever").val
      _r.mageSelf = find(mage, "Delta-Forever") and find(mage, "Delta-Forever").self
      _r.mageBravo = find(mage, "Bravo-Forever") ~= nil   -- Bravo's Mage cat is level 1
      local war = TCF:LeaderboardSection("class", "WARRIOR")
      _r.warAlpha = find(war, "Alpha-Forever") and find(war, "Alpha-Forever").val
      local bs = TCF:LeaderboardSection("prof", "blacksmithing")
      _r.bsAlpha = find(bs, "Alpha-Forever") and find(bs, "Alpha-Forever").val
      _r.bsTop = bs[1].n
      local gold = TCF:LeaderboardSection("prof", "gold")
      _r.gold = find(gold, "Alpha-Forever") and find(gold, "Alpha-Forever").val
      local herb = TCF:LeaderboardSection("prof", "herbalism")
      _r.herb = find(herb, "Alpha-Forever") and find(herb, "Alpha-Forever").val
      _r.herbBravo = find(herb, "Bravo-Forever") ~= nil
      _r.sorted = true
      for _, sec in ipairs({ { "class", "MAGE" }, { "class", "WARRIOR" }, { "prof", "gold" }, { "prof", "cooking" }, { "taps", "level" } }) do
        local list = TCF:LeaderboardSection(sec[1], sec[2])
        for i = 2, #list do if list[i].val > list[i - 1].val then _r.sorted = false end end
        if not find(list, "Delta-Forever") then _r.sorted = false end   -- your own row is in every section
      end
    """)
    r = D.lua.globals()._r
    ck(r.older == "older" and r.kept and r.unknown == "unknown" and r.self == "self" and r.future == "future", "L2 merge rules: %s %s %s %s" % (r.older, r.unknown, r.self, r.future))
    ck(r.keptAfterL1, "a newer L1 keeps the extra fields until the next L2")
    ck(r.mageAlpha == 17 and r.mageSelf and not r.mageBravo, "Per class: Alpha's level 17 Mage cat, you, and no level 1 cats of others")
    ck(r.warAlpha == 31, "Per class: the class a player plays uses their summary's level")
    ck(r.bsAlpha == 200 and r.bsTop == "Alpha-Forever" and abs(r.gold - 1234567890123) < 1e6 and r.herb == 42 and not r.herbBravo,
       "Professions: skills and Trade Gold (%s %s %s)" % (r.bsAlpha, r.gold, r.herb))
    ck(r.sorted, "every section is ranked, with your own row")
    # forward and backward: more numbers or fields from a later version are skipped; odd ones refused
    ok = "L2;Zed-Forever;%d;1.2.3.4.5.6.7.8.9;12345;1.2.3.4.5.6.7" % srv[0]
    for msg, good in ((ok, True), (ok.replace("8.9;", "8.9.60.61;") + ".300;and more;5", True), (ok + ";", True),
                      (ok.replace(";12345;", ";9999999e93;"), True), (ok.replace(";12345;", ";12345678;"), False),
                      (ok.replace(";12345;", ";1e100;"), False), (ok.replace(";12345;", ";1e;"), False), (ok.replace("1.2.3.4.5.6.7.8.9", "1.2.3.4.5.6.7.8"), False),
                      (ok.replace("1.2.3.4.5.6.7.8.9", "1.2.3.4.5.6.7.8.201"), False), (ok.replace("1.2.3.4.5.6.7.8.9", "1..3.4.5.6.7.8.9"), False),
                      (ok[:-1] + "1000", False), (ok + "x", False), (ok.replace("Zed-Forever", "Zed"), False), (ok.replace("Zed", "Z|d"), False),
                      ("L2;Zed-Forever;%d;1.2.3.4.5.6.7.8.9;12345" % srv[0], False), ("L2;" + "A" * 300, False)):
        got = D.ev('TapCatForever.LeaderboardParseExtra("%s") ~= nil' % msg.replace('"', '\\"'))
        ck(got == good, "L2 parse %s: %s" % ("accepts" if good else "refuses", msg))
    D.lua.globals()._deliver("TapCatFvr", ok, "Zed-Forever")
    ck(D.ev('_entry("zed-forever")') is None, "an L2 never adds a player")
    D.lua.globals()._deliver("TapCatFvr", "L2;Delta-Forever;%d;60.60.60.60.60.60.60.60.60;99999e9;300.300.300.300.300.300.300" % srv[0], "Bravo-Forever")
    ck(D.ev('(function() for _, r in ipairs(TapCatForever:LeaderboardSection("prof", "cooking")) do if r.self then return r.val end end end)()') == 1,
       "your own extra fields never come from someone else")
    big = D.ev('TapCatForever.LeaderboardExtraText({ n = string.rep("A", 40) .. "-" .. string.rep("B", 39), xts = 99999999999, '
               'x = { lv = { 200, 200, 200, 200, 200, 200, 200, 200, 200 }, g = 9.9e99, sk = { 999, 999, 999, 999, 999, 999, 999 } } })')
    ck(big and len(big) <= 255 and D.ev('TapCatForever.LeaderboardParseExtra("%s") ~= nil' % big), "the longest L2 fits in one message: %d" % len(big or ""))
    # Oscar runs a build that only knows L1: drops every L2 it would send or hear
    O = Client("Oscar", "HUNTER")
    O.ex(r"""
      local send = C_ChatInfo.SendAddonMessage
      C_ChatInfo.SendAddonMessage = function(p, msg, ch, target) if msg:sub(1, 3) == "L2;" then return 0 end return send(p, msg, ch, target) end
      local deliver = _deliver
      _deliver = function(p, msg, ...) if msg:sub(1, 3) == "L2;" then return end return deliver(p, msg, ...) end
      _optIn(true)
    """)
    step(240)
    ck("alpha-forever" in O.ev("_boardKeys()") and O.ev('_entry("alpha-forever").x') is None, "the L1-only client lists Alpha, without extra fields: " + O.ev("_boardKeys()"))
    ck(D.ev('_entry("oscar-forever")') is not None and D.ev('_entry("oscar-forever").x') is None, "and is listed by the others")
    def in_section(c, sec, sub, n):
        return c.ev('(function() for _, r in ipairs(TapCatForever:LeaderboardSection("%s", "%s")) do if r.n == "%s" then return true end end return false end)()' % (sec, sub, n))
    ck(in_section(D, "taps", "taps", "Oscar-Forever") and in_section(D, "class", "HUNTER", "Oscar-Forever"), "Oscar shows under Total taps and the class he plays")
    ck(not in_section(D, "class", "MAGE", "Oscar-Forever") and not in_section(D, "prof", "gold", "Oscar-Forever"), "but not elsewhere")
    O.online = False

    # 6. Alpha leaves from the Leaderboard tab (Leave asks first): one "take me off", honoured by the
    # others, and nothing more is sent
    s0 = len(A.sent)
    A.ex("TapCatForever:ShowLeaderboard()")
    click(A, "TapCatForever.leaderboardView.leaveBtn")
    ck(A.ev("TapCatForever.leaderboardView.confirm:IsShown()") and A.ev("TapCatForever.db.ui.shareDev") == True, "Leave asks first")
    ck("!" not in A.ev("TapCatForever.leaderboardView.confirmText:GetText()"), "the question is plain")
    click(A, "TapCatForever.leaderboardView.confirmNo")
    ck(not A.ev("TapCatForever.leaderboardView.confirm:IsShown()") and A.ev("TapCatForever.db.ui.shareDev") == True, "Stay keeps you on")
    # the question doesn't wait for you after leaving the tab (the test frames don't run OnHide on Hide)
    click(A, "TapCatForever.leaderboardView.leaveBtn")
    A.ex("local v = TapCatForever.leaderboardView; v:Hide(); if v.scripts.OnHide then v.scripts.OnHide(v) end; TapCatForever:ShowLeaderboard()")
    ck(not A.ev("TapCatForever.leaderboardView.confirm:IsShown()") and A.ev("TapCatForever.leaderboardView.leaveBtn:IsShown()")
       and A.ev("TapCatForever.db.ui.shareDev") == True, "leaving the tab drops the Leave question")
    click(A, "TapCatForever.leaderboardView.leaveBtn")
    click(A, "TapCatForever.leaderboardView.confirmYes")
    ck(A.ev("TapCatForever.db.ui.shareDev") == False, "Leave turns sharing off")
    step(1)
    rm = [m for (t, m) in A.sent[s0:]]
    ck(len(rm) == 1 and rm[0].startswith("R1;"), "opting out sends one take-me-off: %r" % rm)
    for c in (B, D):
        ck(c.ev('_entry("alpha-forever")') is None, c.name + " took Alpha off")
    ck(A.ev("_chanId") == 0, "opted out: left the hidden channel")
    step(40 * 60)
    ck(len(A.sent) == s0 + 1, "opted out: nothing else sent")
    ck(A.ev("#TapCatForever:LeaderboardRows()") == 0, "opted out: you don't see the board")
    A.ex("TapCatForever:ShowLeaderboard()")
    ck(A.ev("TapCatForever.leaderboardView.join:IsShown()") and not A.ev("TapCatForever.leaderboardView.board:IsShown()"),
       "opted out: the tab shows the opt-in panel again")
    ck("already got" in A.ev("TapCatForever.leaderboardView.joinReward:GetText()"), "and says the account already had its Heroic Cache")
    A.ex("TapCatForever.window:Hide()")
    # an old copy of Alpha passed on later doesn't bring them back; nor does their old take-me-off replayed
    rmTs = int(rm[0][3:])
    D.lua.globals()._deliver("TapCatFvr", "L1;Alpha-Forever;WARRIOR;31;123456;1;0;1.5.3;%d" % (rmTs - 60), "Bravo-Forever")
    ck(D.ev('_entry("alpha-forever")') is None, "a stale copy after the take-me-off is ignored")
    # only a player's own take-me-off counts: Bravo can't remove Delta from Delta's board or Cedric anywhere
    D.lua.globals()._deliver("TapCatFvr", "R1;%d" % srv[0], "Bravo-Forever")
    ck(D.ev('_entry("bravo-forever")') is None, "Bravo's own take-me-off removes Bravo")
    ck(D.ev('_entry("cedric-forever")') is not None, "and nobody else")
    D.lua.globals()._deliver("TapCatFvr", "L1;Bravo-Forever;PRIEST;1;1;1;0;1.5.3;%d" % (srv[0] - 5), "Bravo-Forever")
    ck(D.ev('_entry("bravo-forever")') is None, "a summary older than that take-me-off doesn't bring Bravo back")
    D.lua.globals()._deliver("TapCatFvr", "L1;Bravo-Forever;PRIEST;1;1;1;0;1.5.3;%d" % (srv[0] + 1), "Bravo-Forever")
    ck(D.ev('_entry("bravo-forever")') is not None, "a newer one from Bravo does")
    D.lua.globals()._deliver("TapCatFvr", "R1;%d" % (srv[0] - 30), "Bravo-Forever")
    ck(D.ev('_entry("bravo-forever")') is not None, "an old take-me-off replayed after a newer summary is ignored")
    # Alpha joins again from the tab: back on the boards, no second chest
    A.ex("TapCatForever:ShowLeaderboard()")
    click(A, "TapCatForever.leaderboardView.joinBtn")
    A.ex("TapCatForever.window:Hide()")
    step(120)
    ck(A.heroic() == ha + 1, "opting in again: no second chest")
    ck(D.ev('_entry("alpha-forever")') is not None, "opting in again puts you back on the board")
    # a new character on the same account: still no chest (the account already had it)
    A.ex('_charName = "Alphalt"; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    step(5)
    ck(A.heroic() == 0 and A.ev("TapCatForever.db.keys.heroic or 0") == 0, "an alt gets no sign-up chest")
    A.ex('_charName = "Alpha"; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')

    # 7. a save that already shared (from before this version): the chest once, on the first tick after login
    F = Client("Foxtrot", "HUNTER", before="TapCatForeverDB = { ui = { shareDev = true } }")
    ck(F.heroic() == 0, "no chest before the first tick")
    step(2)
    ck(F.heroic() == 1, "already sharing: the sign-up chest once")
    F.ex("TapCatForever.LeaderboardTest.reset(); _fire('PLAYER_LOGIN')")
    step(2)
    ck(F.heroic() == 1, "and only once")

    # 8. every client stayed inside the send limits: a gap of 2 seconds and at most 30 in 10 minutes
    budget = A.ev("TapCatForever.LB_SEND_BUDGET")
    ck(budget == 30, "send budget %s" % budget)
    def send_limits():
        for c in clients.values():
            ts = [t for (t, m) in c.sent if m[:3] in ("L1;", "L2;", "X1;")]
            for i in range(1, len(ts)):
                ck(ts[i] - ts[i - 1] >= 2, c.name + " sent two messages less than 2 seconds apart")
            ts = [t for (t, m) in c.sent if m[:3] in LB_KINDS]
            for i in range(len(ts)):
                ck(len([t for t in ts if ts[i] <= t < ts[i] + 600]) <= budget, c.name + " sent more than %d messages in 10 minutes" % budget)
    send_limits()

    # 9. merge rules, caps and expiry (Delta's board)
    D.ex(r"""
      local TCF = TapCatForever
      local b, t = TCF.LeaderboardBoard(true), _srv
      local merge = TCF.LeaderboardMerge
      local function E(n, ts, lvl) return { n = n, c = "MAGE", l = lvl or 5, t = 10, a = 1, z = 0, v = "1.5.3", ts = ts } end
      for k in pairs(b.e) do b.e[k] = nil end
      for k in pairs(b.rm) do b.rm[k] = nil end
      _r = {}
      _r.add = merge(b, E("Zara-Forever", t - 100), t)
      _r.older = select(2, merge(b, E("Zara-Forever", t - 200, 9), t))
      _r.same = select(2, merge(b, E("Zara-Forever", t - 100, 9), t))
      _r.newer = merge(b, E("Zara-Forever", t - 50, 9), t)
      _r.future = select(2, merge(b, E("Yuri-Forever", t + 3600), t))
      _r.ancient = select(2, merge(b, E("Yuri-Forever", t - 31 * 86400), t))
      _r.self = select(2, merge(b, E("Delta-Forever", t), t, "delta-forever"))
      -- the cap: 600 players, the newest 500 kept
      local letters = "abcdefghijklmnopqrstuvwxyz"
      local function nm(i) local a, c = (i % 26) + 1, (math.floor(i / 26) % 26) + 1
        return "Cap" .. letters:sub(c, c) .. letters:sub(a, a) .. "-Forever" end
      for k in pairs(b.e) do b.e[k] = nil end
      for i = 1, 600 do merge(b, E(nm(i), t - 100000 + i), t) end
      local n, oldest = 0, nil
      for _, e in pairs(b.e) do n = n + 1; if not oldest or e.ts < oldest then oldest = e.ts end end
      _r.capN, _r.capOldest = n, oldest - (t - 100000)
      _r.full = select(2, merge(b, E("Late-Forever", t - 200000), t))
      -- expiry: 31 days old drops off at the next login
      local any
      for k, e in pairs(b.e) do any = k; e.ts = t - 31 * 86400; break end
      b.rm["gone-forever"] = t - 40 * 86400
      b.rm["kept-forever"] = t - 86400
      TCF.LeaderboardTest.reset(); _fire("PLAYER_LOGIN")
      b = TCF.LeaderboardBoard(false)
      _r.expired = b.e[any] == nil
      _r.left = 0; for _ in pairs(b.e) do _r.left = _r.left + 1 end
      _r.rmGone, _r.rmKept = b.rm["gone-forever"] == nil, b.rm["kept-forever"] ~= nil
      -- a saved board edited by hand: bad entries go
      b.e["junk-forever"] = { n = "Junk-Forever", c = "DRAGON", l = 5, t = 1, a = 0, z = 0, v = "1", ts = t }
      b.e["other-forever"] = { n = "Bob-Forever", c = "MAGE", l = 5, t = 1, a = 0, z = 0, v = "1", ts = t }
      b.e["str-forever"] = "hello"
      TCF.LeaderboardTest.prune(b, t)
      _r.junk = b.e["junk-forever"] == nil and b.e["other-forever"] == nil and b.e["str-forever"] == nil
    """)
    r = D.lua.globals()._r
    ck(r.add == "added" and r.older == "older" and r.same == "older" and r.newer == "updated", "newest summary wins: %s %s %s %s" % (r.add, r.older, r.same, r.newer))
    ck(r.future == "future" and r.ancient == "old" and r.self == "self", "too far ahead, too old, and yourself are refused")
    ck(r.capN == 500 and r.capOldest == 101 and r.full == "full", "cap: the newest 500 kept (%s, oldest %s, %s)" % (r.capN, r.capOldest, r.full))
    ck(r.expired and r.left == 499 and r.rmGone and r.rmKept, "players not seen for 30 days drop off")
    ck(r.junk, "odd saved entries are dropped")

    # 10. odd and secret messages: ignored without errors
    D.ex("_optIn(true)")
    n0 = D.ev("_boardCount()")
    now = srv[0]
    good = "L1;Good-Forever;MAGE;5;100;1;0;1.5.3;%d" % now
    bad = [
        ("L1;", "Bob-Forever"), ("L1;Bob-Forever;MAGE;5;100;1;0;1.5.3", "Bob-Forever"),
        (good.replace("MAGE", "DRAGON"), "Good-Forever"), (good.replace(";5;", ";0;"), "Good-Forever"),
        (good.replace(";5;", ";9999;"), "Good-Forever"), (good.replace(";100;", ";9999999999999999;"), "Good-Forever"),
        (good.replace("Good-Forever", "Go0d-Forever"), "Good-Forever"), (good.replace("Good-Forever", "Good"), "Good-Forever"),
        (good.replace("Good-Forever", "Go|cffd-Forever"), "Good-Forever"), (good.replace("Good-Forever", "Go od-Forever"), "Good-Forever"),
        (good.replace("Good-Forever", "Good-For-ever"), "Good-Forever"), (good.replace("1.5.3", "1.5;3"), "Good-Forever"),
        (good + ";extra", "Good-Forever"), (good[:-1] + "x", "Good-Forever"), ("L1;" + "A" * 300, "Good-Forever"),
        (good.replace("Good-Forever", "G" * 60 + "-Forever"), "Good-Forever"), ("R1;abc", "Cedric-Forever"),
        ("R1;" + "9" * 13, "Cedric-Forever"), ("R1;%d" % (now + 99999), "Cedric-Forever"), ("X1;hello", "Good-Forever"),
        (good, "Bad Name-Forever"), (good, ""),
    ]
    for msg, sender in bad:
        D.lua.globals()._deliver("TapCatFvr", msg, sender)
    D.lua.globals()._deliver("TapCatFvr", good, "Good-Forever", "WHISPER")   # 1.5.3.2: party, raid and guild count; whispers don't
    D.lua.globals()._deliver("TapCatFvr", good, "Good-Forever", "CHANNEL", "General")
    D.lua.globals()._deliver("OtherAddon", good, "Good-Forever")
    D.ex('_fire("CHAT_MSG_ADDON", _SECRET, "%s", "CHANNEL", "Good-Forever", "", 0, 7, "TapCatFvrShare", 0)' % good)
    D.ex('_fire("CHAT_MSG_ADDON", "TapCatFvr", _SECRET, "CHANNEL", "Good-Forever", "", 0, 7, "TapCatFvrShare", 0)')
    D.ex('_fire("CHAT_MSG_ADDON", "TapCatFvr", "%s", _SECRET, "Good-Forever", "", 0, 7, "TapCatFvrShare", 0)' % good)
    D.ex('_fire("CHAT_MSG_ADDON", "TapCatFvr", "%s", "CHANNEL", _SECRET, "", 0, 7, "TapCatFvrShare", 0)' % good)
    D.ex('_fire("CHAT_MSG_ADDON", "TapCatFvr", "%s", "CHANNEL", "Good-Forever", "", 0, 7, _SECRET, 0)' % good)
    D.ex('_srvSave = _srv; GetServerTime = function() return _SECRET end')
    D.lua.globals()._deliver("TapCatFvr", good, "Good-Forever")   # a secret clock: nothing can be compared, nothing kept
    D.ex('GetServerTime = function() return _srv end')
    ck(D.ev("_boardCount()") == n0 and D.ev('_entry("good-forever")') is None,
       "odd or secret messages change nothing (%d -> %d)" % (n0, D.ev("_boardCount()")))
    D.lua.globals()._deliver("TapCatFvr", good, "Good-Forever")
    ck(D.ev('_entry("good-forever")') is not None, "the good one is read")

    # 11. the read limit: a flood of 400 summaries in one second, at most 240 read
    D.ex("for k in pairs(TapCatForever.LeaderboardBoard(true).e) do TapCatForever.LeaderboardBoard(true).e[k] = nil end")
    D.ex("TapCatForever.LeaderboardTest.reset(); _optIn(true)")
    D.ex(r"""
      local letters = "abcdefghijklmnopqrstuvwxyz"
      for i = 1, 700 do
        local a, c = (i % 26) + 1, (math.floor(i / 26) % 26) + 1
        local n = "Flood" .. letters:sub(c, c) .. letters:sub(a, a) .. "-Forever"
        _deliver("TapCatFvr", "L1;" .. n .. ";MAGE;5;" .. i .. ";1;0;1.5.3;" .. _srv, n)
      end
    """)
    _lim = min(D.ev("TapCatForever.LB_READ_BUDGET"), D.ev("TapCatForever.LB_MAX_ENTRIES"))
    ck(D.ev("_boardCount()") == _lim, "at most %d kept from a minute's flood: %d" % (_lim, D.ev("_boardCount()")))
    # the send limit: many newcomers in a row never push a client past 30 messages in 10 minutes
    s0 = len(D.sent)
    t0 = srv[0]
    for i in range(30):
        nm = "New" + "abcdefghijklmnopqrstuvwxyz"[i // 26] + "abcdefghijklmnopqrstuvwxyz"[i % 26] + "-Forever"
        D.lua.globals()._deliver("TapCatFvr", "L1;%s;MAGE;5;1;1;0;1.5.3;%d" % (nm, srv[0]), nm)
        step(20)
    sentNow = [t for (t, m) in D.sent[s0:] if m[:3] in ("L1;", "L2;")]
    ck(len(sentNow) > 0 and all(len([u for u in sentNow if s <= u < s + 600]) <= budget for s in sentNow), "send limit held: %d sent" % len(sentNow))

    # 11b. a take-me-off reaches players who were offline: it is passed on (X1) like the board, and a
    # newcomer never shows that player. The earlier clients log off for this part.
    for c in clients.values(): c.online = False
    G, H, M = Client("Golf", "SHAMAN"), Client("Hotel", "PALADIN"), Client("Mike", "WARLOCK")
    for c in (G, H, M): c.ex("_optIn(true)")
    step(120)
    ck(H.ev("_boardKeys()") == "golf-forever,mike-forever" and M.ev("_boardKeys()") == "golf-forever,hotel-forever",
       "Golf, Hotel and Mike see each other: %s / %s" % (H.ev("_boardKeys()"), M.ev("_boardKeys()")))
    H.online = False
    G.ex("_optIn(false)")
    step(1)
    ck(M.ev('_entry("golf-forever")') is None and M.ev('TapCatForever.LeaderboardBoard(false).rmn["golf-forever"]') == "Golf-Forever",
       "Mike heard Golf's take-me-off and keeps the name to pass it on")
    G.online = False
    step(5 * 60)
    H.online = True
    H.ex("TapCatForever.LeaderboardTest.reset(); _fire('PLAYER_LOGIN')")
    ck(H.ev('_entry("golf-forever")') is not None, "Hotel was offline and still lists Golf")
    step(35 * 60)
    ck(any(m.startswith("X1;Golf-Forever;") for m in lbmsgs(M)), "Mike passed the take-me-off on")
    ck(H.ev('_entry("golf-forever")') is None and H.ev('TapCatForever.LeaderboardBoard(false).rm["golf-forever"]') is not None,
       "Hotel took Golf off when it heard it")
    ck(M.ev('_entry("golf-forever")') is None, "Golf's old summary passed on by Hotel didn't bring Golf back for Mike")
    M.online = False
    K = Client("Kilo", "DRUID")
    K.ex("_optIn(true)")
    step(30 * 60)
    ck(K.ev("_boardKeys()") == "hotel-forever,mike-forever", "a newcomer gets the board without Golf: " + K.ev("_boardKeys()"))
    ck(K.ev('TapCatForever.LeaderboardBoard(false).rm["golf-forever"]') is not None, "and the take-me-off note with it")
    # Golf shares again: back on the boards of those who hear Golf
    G.online = True
    G.ex("_optIn(true)")
    step(120)
    ck(K.ev('_entry("golf-forever")') is not None and H.ev('_entry("golf-forever")') is not None, "sharing again puts Golf back")
    G.ex("_optIn(false)")
    step(1)
    G.online = False

    # 11c. the take-me-off is kept until it has gone out, for every character on the account that shared
    N = Client("November", "MAGE")
    N.ex("_optIn(true)")
    step(90)
    N.ex('TapCatForever.LeaderboardTest.reset(); TapCatForever.DevTest.reset(); _chanId = 0; _charName = "Novalt"; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    N.full = "Novalt-Forever"
    step(90)
    ck(K.ev('_entry("november-forever")') is not None and K.ev('_entry("novalt-forever")') is not None, "both of November's characters shared")
    ck(N.ev('TapCatForever.db.ui.lbShared["november-forever"] and TapCatForever.db.ui.lbShared["novalt-forever"]') == True,
       "the account remembers which characters shared")
    # back on November, the box is unticked 10 seconds after login, before the channel is joined
    N.ex('TapCatForever.LeaderboardTest.reset(); TapCatForever.DevTest.reset(); _chanId = 0; _charName = "November"; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    N.full = "November-Forever"
    step(10)
    ck(N.ev("_chanId") == 0, "not in the channel yet")
    s0 = len(N.sent)
    N.ex("_optIn(false)")
    step(1)
    ck(len(N.sent) == s0, "no channel: nothing sent yet")
    ck(N.ev('TapCatForever.db.ui.lbRemove["november-forever"] ~= nil and TapCatForever.db.ui.lbRemove["novalt-forever"] ~= nil') == True,
       "a take-me-off is saved for both characters")
    step(30)
    rm = [m for (t, m) in N.sent[s0:]]
    ck(len(rm) == 1 and rm[0].startswith("R1;"), "it goes out once the channel is joined: %r" % rm)
    ck(K.ev('_entry("november-forever")') is None and K.ev('_entry("novalt-forever")') is not None, "Kilo took November off; the alt waits for its own login")
    ck(N.ev("_chanId") == 0 and N.ev('TapCatForever.db.ui.lbRemove["november-forever"]') is None, "then the channel is left and the note cleared")
    # the alt logs in while opted out: its own take-me-off after the usual join delay, then it leaves
    N.ex('TapCatForever.LeaderboardTest.reset(); TapCatForever.DevTest.reset(); _chanId = 0; _charName = "Novalt"; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    N.full = "Novalt-Forever"
    s0 = len(N.sent)
    step(40)
    rm = [m for (t, m) in N.sent[s0:]]
    ck(len(rm) == 1 and rm[0].startswith("R1;"), "the alt sends its own take-me-off at login: %r" % rm)
    ck(K.ev('_entry("novalt-forever")') is None, "and Kilo took the alt off")
    ck(N.ev("_chanId") == 0 and N.ev("TapCatForever.db.ui.lbRemove") is None, "nothing left to send, channel left")
    j0 = N.ev("_joins")
    step(30 * 60)
    N.ex('TapCatForever.LeaderboardTest.reset(); TapCatForever.DevTest.reset(); _charName = "November"; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    N.full = "November-Forever"
    step(60)
    ck(len(N.sent) == s0 + 1 and N.ev("_joins") == j0 and N.ev("_chanId") == 0, "opted out with nothing to send: no channel, nothing sent")

    # 11d. off, on, our own summary sent, off again within 10 seconds: a second take-me-off at once
    s0 = len(K.sent)
    K.ex("_optIn(false)")
    step(1)
    K.ex("_optIn(true); TapCatForever.LeaderboardTest.setOwnAt(GetTime() + 2)")
    step(4)
    def kmsgs(): return [m for (t, m) in K.sent[s0:] if m.startswith("R1;") or m.startswith("L1;Kilo-Forever;")]
    msgs = kmsgs()
    ck(len(msgs) == 2 and msgs[0].startswith("R1;") and msgs[1].startswith("L1;Kilo-Forever;"), "take-me-off, then a summary: %r" % msgs)
    ck(H.ev('_entry("kilo-forever")') is not None, "Hotel lists Kilo again")
    K.ex("_optIn(false)")
    step(1)
    msgs = kmsgs()
    ck(len(msgs) == 3 and msgs[2].startswith("R1;"), "the second take-me-off goes out at once: %r" % msgs)
    ck(H.ev('_entry("kilo-forever")') is None, "and Hotel took Kilo off again")
    K.ex("_optIn(true); _optIn(false)")
    step(15)
    ck(len(kmsgs()) == 3, "with no summary in between, no more take-me-off")

    # 11e. limits per sender (Hotel's board)
    H.ex("TapCatForever.LeaderboardTest.reset()")
    H.ex('for i = 1, 300 do _deliver("TapCatFvr", "L1;Hotel-Forever;PALADIN;5;1;1;0;1.5.3;" .. _srv, "Hotel-Forever") end')
    ck(H.ev("#TapCatForever.LeaderboardTest.state().readAt") == 0, "our own messages coming back cost no reading")
    n0 = H.ev("_boardCount()")
    flood = r"""
      local letters = "abcdefghijklmnopqrstuvwxyz"
      for i = %d, %d do
        local n = "Fake" .. letters:sub(math.floor(i / 26) %% 26 + 1, math.floor(i / 26) %% 26 + 1) .. letters:sub(i %% 26 + 1, i %% 26 + 1) .. "-Forever"
        _deliver("TapCatFvr", "L1;" .. n .. ";MAGE;5;1;1;0;1.5.3;" .. _srv, "Spammer-Forever")
      end
    """
    # 30 messages that change nothing (an L2 about nobody), then 30 new players: only the first 10 are read
    H.ex('for i = 1, 30 do _deliver("TapCatFvr", "L2;Nobody-Forever;" .. _srv .. ";1.1.1.1.1.1.1.1.1;0;1.1.1.1.1.1.1", "Spammer-Forever") end')
    H.ex(flood % (1, 30))
    msgs, adds = H.ev("TapCatForever.LB_SENDER_MSGS"), H.ev("TapCatForever.LB_SENDER_ADDS")
    ck(msgs == 40 and adds == 40, "per-sender limits %s %s" % (msgs, adds))
    ck(H.ev("_boardCount()") == n0 + msgs - 30, "one sender: at most %d messages read in 10 minutes (%d)" % (msgs, H.ev("_boardCount()") - n0))
    H.ex("_clock = _clock + 601"); H.ex(flood % (31, 70))
    H.ex("_clock = _clock + 601"); H.ex(flood % (71, 90))
    ck(H.ev("_boardCount()") == n0 + adds, "one sender adds at most %d players an hour (%d)" % (adds, H.ev("_boardCount()") - n0))
    H.ex("_clock = _clock + 601")
    H.lua.globals()._deliver("TapCatFvr", "L1;Spammer-Forever;MAGE;5;1;1;0;1.5.3;%d" % srv[0], "Spammer-Forever")
    ck(H.ev('_entry("spammer-forever")') is not None, "their own summary still counts")
    H.ex("_clock = _clock + 601")
    H.lua.globals()._deliver("TapCatFvr", "X1;Mike-Forever;%d" % srv[0], "Spammer-Forever")
    ck(H.ev('_entry("mike-forever")') is not None, "past the limit, they can't take others off either")
    # a player who took themselves off comes back only through their own summary
    H.ex('TapCatForever.LeaderboardRemove(TapCatForever.LeaderboardBoard(false), "zulu-forever", _srv - 10, _srv, "Zulu-Forever")')
    H.lua.globals()._deliver("TapCatFvr", "L1;Zulu-Forever;MAGE;9;9;1;0;1.5.3;%d" % srv[0], "Mike-Forever")
    ck(H.ev('_entry("zulu-forever")') is None, "a fresh summary passed on by someone else doesn't bring them back")
    H.lua.globals()._deliver("TapCatFvr", "L1;Zulu-Forever;MAGE;9;9;1;0;1.5.3;%d" % srv[0], "Zulu-Forever")
    ck(H.ev('_entry("zulu-forever")') is not None and H.ev('TapCatForever.LeaderboardBoard(false).rm["zulu-forever"]') is None, "their own does")
    # X1 checks: an X1 older than the entry is ignored; one about yourself is ignored
    H.lua.globals()._deliver("TapCatFvr", "X1;Zulu-Forever;%d" % (srv[0] - 60), "Mike-Forever")
    ck(H.ev('_entry("zulu-forever")') is not None, "a take-me-off older than the summary is ignored")
    H.lua.globals()._deliver("TapCatFvr", "X1;Hotel-Forever;%d" % srv[0], "Mike-Forever")
    ck(H.ev('TapCatForever.LeaderboardBoard(false).rm["hotel-forever"]') is None, "a take-me-off about yourself is ignored")
    for bad in ("X1;Zulu-Forever", "X1;Zulu;%d" % srv[0], "X1;Zulu-Forever;abc", "X1;Zu|ru-Forever;%d" % srv[0], "X1;Zulu-Forever;" + "9" * 13):
        H.lua.globals()._deliver("TapCatFvr", bad, "Mike-Forever")
    ck(H.ev('_entry("zulu-forever")') is not None, "odd take-me-off messages are ignored")

    # 11f. entries that turn 30 days old during a long session are neither passed on nor shown
    H.ex(r"""
      local b = TapCatForever.LeaderboardBoard(false)
      local saved = {}
      for k, v in pairs(b.e) do saved[k] = v; b.e[k] = nil end
      b.e["stale-forever"] = { n = "Stale-Forever", c = "MAGE", l = 5, t = 1, a = 0, z = 0, v = "1.5.3", ts = _srv - TapCatForever.LB_EXPIRE - 1 }
      b.e["okay-forever"] = { n = "Okay-Forever", c = "MAGE", l = 5, t = 1, a = 0, z = 0, v = "1.5.3", ts = _srv - TapCatForever.LB_EXPIRE + 60 }
      _r = { relay = false, row = false, okRelay = false, okRow = false }
      for _, k in ipairs(TapCatForever.LeaderboardTest.pickRelays(GetTime(), 1e12, false)) do
        if k == "stale-forever" then _r.relay = true elseif k == "okay-forever" then _r.okRelay = true end
      end
      for _, r in ipairs(TapCatForever:LeaderboardRows("taps")) do
        if r.n == "Stale-Forever" then _r.row = true elseif r.n == "Okay-Forever" then _r.okRow = true end
      end
      b.e["stale-forever"], b.e["okay-forever"] = nil, nil
      for k, v in pairs(saved) do b.e[k] = v end
    """)
    ck(not H.ev("_r.relay") and not H.ev("_r.row"), "an entry past 30 days is not passed on or shown")
    ck(H.ev("_r.okRelay") and H.ev("_r.okRow"), "one just inside 30 days still is")

    # 11g. relays count as passed on only once they went out
    H.ex(r"""
      local LT = TapCatForever.LeaderboardTest
      LT.reset()
      _r = {}
      local c = _chanId
      _chanId = 0
      _r.noChan = LT.relay(GetTime(), GetTime(), false)
      _chanId = c
      _sendResult = 1
      _r.queued = LT.relay(GetTime(), GetTime(), false)
      for i = 1, 30 do _update(1) end
      _r.marked = next(LT.state().relayedAt) ~= nil
      _r.left = #LT.state().queue
      _sendResult = 0
      _r.again = LT.relay(GetTime(), GetTime(), false)
      for i = 1, 30 do _update(1) end
      _r.markedNow = next(LT.state().relayedAt) ~= nil
    """)
    r = H.lua.globals()._r
    ck(r.noChan == 0 and r.queued > 0 and not r.marked and r.left == 0, "failed relays are not counted as passed on (%s %s %s %s)" % (r.noChan, r.queued, r.marked, r.left))
    ck(r.again > 0 and r.markedNow, "they are picked again and counted once sent")
    H.ex("_takeOut()")
    send_limits()

    # 12. the Leaderboard tab: 12 tabs (Casino is the 11th) in two rows of 6 whose labels fit; the Settings button, /tcf top
    # and /tcf leaderboard open it; the three sections with ranks, sorting, your row in each, scrolling
    B.ex("if not TapCatForever.window then TapCatForever:CreateWindow() end; TapCatForever.window:Show()")
    names = [B.ev("TapCatForever.window.tabNames[%d]" % i) for i in range(1, B.ev("#TapCatForever.window.tabNames") + 1)]
    ck(len(names) == 12 and B.ev("#TapCatForever.window.tabButtons") == 12 and names[B.ev("TapCatForever.window.TAB_LEADERBOARD") - 1] == "Leaderboard"
       and names[-1] == "Settings", "12 tabs, Leaderboard among them: %r" % names)
    tw, ts = B.ev("TapCatForever.window.tabWidth"), B.ev("TapCatForever.window.tabStep")
    # 1.6.0: ten tabs in two rows of 5 (Casino and Settings are icon buttons next to the title)
    ck(tw == 110 and ts > tw and abs(4 * ts + tw - 560) < 0.01, "two rows of 5 tabs, 110 wide, filling the 560 wide panel (step %s)" % ts)
    for n in names:
        # clear of the button's rounded ends, 5 px each side (UI.lua switches to the small font past that)
        ck(est_width(n) <= tw - 10, "tab label fits: %s (about %.1f of %d px)" % (n, est_width(n), tw - 10))
    lay = B.lua.eval("TapCatForever.window.settingsLayout")
    items = [lay[i] for i in range(1, len(lay) + 1)]
    lb = [a for a in items if a.label == "Leaderboard"]
    share = [a for a in items if a.kind == "check" and "leaderboard" in a.label]
    ck(len(lb) == 1 and lb[0].kind == "button" and len(share) == 1 and lb[0].y == share[0].y and share[0].x + share[0].w <= lb[0].x,
       "Settings: the Leaderboard button sits beside the sharing checkbox in Help and info")
    B.ex("TapCatForever.window:SelectTab(TapCatForever.window.TAB_SETTINGS)")
    B.ex("local f = TapCatForever.window.settingsLayout; for _, a in ipairs(f) do if a.label == 'Leaderboard' then a.frame.scripts.OnClick(a.frame) end end")
    ck(B.ev("TapCatForever.window:IsShown() and TapCatForever.window.tab == TapCatForever.window.TAB_LEADERBOARD"), "the Settings button opens the Leaderboard tab")
    for word in ("top", "leaderboard"):
        B.ex("TapCatForever.window:Hide(); TapCatForever.window:SelectTab(1); SlashCmdList.TAPCATFOREVER('%s')" % word)
        ck(B.ev("TapCatForever.window:IsShown() and TapCatForever.window.tab == TapCatForever.window.TAB_LEADERBOARD"), "/tcf %s opens the tab" % word)
    B.ex(r"""
      local TCF = TapCatForever
      local b, t = TCF.LeaderboardBoard(true), _srv
      local classes = { "MAGE", "WARRIOR", "PRIEST", "ROGUE" }
      for i = 1, 20 do
        local n = "Rank" .. string.char(96 + i) .. "-Forever"
        local x = { lv = { i, 2, 3, 4, 5, 6, (i * 7) % 23 + 1, 8, 9 }, g = 1000 * i * i, sk = { i * 10, 1, 1, 1, 1, 1, (i * 13) % 300 } }
        TCF.LeaderboardMerge(b, { n = n, c = classes[i % 4 + 1], l = i, t = 1000 * (21 - i), a = i % 7, z = i % 5, v = "1.5.3", ts = t - i * 4000,
          x = x, xts = t - i * 4000 }, t)
      end
      TCF.db.taps = 999999999   -- you lead on taps
      local win, v = TCF.window, TCF.leaderboardView
      local function click(f) f.scripts.OnClick(f) end
      local function youRow()
        local you
        for i, row in ipairs(v.rows) do if row.entry and row.entry.self then you = i end end
        return you
      end
      local function sorted(field)
        for i = 2, 14 do
          local a, c = v.rows[i - 1].entry, v.rows[i].entry
          if a and c and c[field] > a[field] then return false end
        end
        return true
      end
      win.lbScroll = 0
      v:Refresh()
      _w = { title = v.title:GetText(), r1 = v.rows[1].cells[2]:GetText(), rank1 = v.rows[1].cells[1]:GetText(), seen = v.rows[2].cells[7]:GetText() }
      local you = youRow()
      _w.youHl = you and v.rows[you].hl:IsShown() or false
      _w.otherHl = v.rows[you == 1 and 2 or 1].hl:IsShown()
      _w.sections = #v.sectionBtns
      local lvl
      _w.tapsLabel = v.subLabel:GetText()
      for _, h in ipairs(v.heads) do if h.sortKey == "level" then lvl = h end end
      click(lvl)
      _w.levelLabel = v.subLabel:GetText()
      _w.byLevel = v.rows[1].entry.l
      _w.maxLevel = 0
      for _, r in ipairs(TCF:LeaderboardRows("taps")) do _w.maxLevel = math.max(_w.maxLevel, r.l) end
      _w.sorted = sorted("l")
      v.scripts.OnMouseWheel(v, -1)
      _w.scroll = win.lbScroll
      _w.note = v.note:GetText()
      _w.empty = v.empty:IsShown()
      -- Per class: 9 class buttons, the Mage board by the Mage cat's level, your row highlighted
      click(v.sectionBtns[2])
      _w.classShown, _w.profHidden = 0, true
      for _, b in ipairs(v.classBtns) do if b:IsShown() then _w.classShown = _w.classShown + 1 end end
      for _, b in ipairs(v.profBtns) do if b:IsShown() then _w.profHidden = false end end
      for _, b in ipairs(v.classBtns) do if b.class == "MAGE" then click(b) end end
      _w.classHead = v.heads[3].label:GetText()
      _w.classSorted = sorted("val")
      _w.classTop = v.rows[1].entry.val
      _w.classLabel = v.subLabel:GetText()
      _w.classScroll = win.lbScroll
      local cy = youRow()
      for _ = 1, 40 do if cy then break end; v.scripts.OnMouseWheel(v, -1); cy = youRow() end
      _w.classYouHl = cy and v.rows[cy].hl:IsShown() or false
      -- Professions: 8 boards, Trade Gold first
      click(v.sectionBtns[3])
      _w.profShown = 0
      for _, b in ipairs(v.profBtns) do if b:IsShown() then _w.profShown = _w.profShown + 1 end end
      _w.goldHead = v.heads[3].label:GetText()
      _w.profCol4 = v.heads[4].label:GetText()
      _w.profTaps = v.rows[1].cells[4]:GetText() == TCF.Commas(v.list[1].t)
      _w.goldTop = v.rows[1].cells[3]:GetText() == TCF.FormatBig(v.list[1].val) and v.list[1].val >= 400000
      _w.goldSorted = sorted("val")
      for _, b in ipairs(v.profBtns) do if b.board == "cooking" then click(b) end end
      _w.cookHead = v.heads[3].label:GetText()
      _w.cookSorted = sorted("val")
      _w.cookLabel = v.subLabel:GetText()
      local py = youRow()
      for _ = 1, 40 do if py then break end; v.scripts.OnMouseWheel(v, -1); py = youRow() end
      _w.profYouHl = py and v.rows[py].hl:IsShown() or false
      _w.profNote = v.note:GetText()
      click(v.sectionBtns[1])
      _w.back = v.heads[4].label:GetText()
    """)
    w = B.lua.globals()._w
    ck(w.title.startswith("Realm leaderboard") and w.rank1 == 1, "tab title and ranks: %s" % w.title)
    ck(w.youHl and not w.otherHl, "your own row is highlighted, others are not")
    ck(w.sections == 3, "three sections")
    ck(w.byLevel == w.maxLevel and w.maxLevel >= 20 and w.sorted, "sorting by cat level: %s" % w.byLevel)
    ck(w.tapsLabel.startswith("Everyone by total taps.") and w.levelLabel.startswith("Everyone by cat level.") and "!" not in w.levelLabel,
       "the line under the sections follows the sort: %r / %r" % (w.tapsLabel, w.levelLabel))
    ck(w.scroll == 1 and not w.empty, "the list scrolls with the mouse wheel")
    ck("30 days" in w.note and "your realm" in w.note and "!" not in w.note, "the limits are explained at the bottom: " + w.note)
    ck(w.classShown == 9 and w.profHidden and w.classHead == "Level" and w.classSorted and w.classTop == 23 and "Mage" in w.classLabel,
       "Per class: 9 class buttons, the Mage board by level (%s, top %s)" % (w.classLabel, w.classTop))
    ck(w.classYouHl, "Per class: your own row highlighted")
    ck(w.profShown == 8 and w.goldHead == "Trade Gold" and w.goldTop and w.goldSorted, "Professions: the Trade Gold board")
    ck(w.profCol4 == "Taps" and w.profTaps, "Professions: a Taps column, not the level of the cat being played (%s)" % w.profCol4)
    ck(w.cookHead == "Cooking" and w.cookSorted and "Cooking" in w.cookLabel and w.profYouHl, "Professions: the Cooking board, your row highlighted")
    ck("!" not in w.profNote and "older version" in w.profNote, "the section notes: " + w.profNote)
    ck(w.back == "Taps", "back to Total taps")
    ck(B.ev("TapCatForever.LeaderboardAgo(%d - 7200, %d)" % (srv[0], srv[0])) == "2 h ago" and B.ev("TapCatForever.LeaderboardAgo(%d - 3 * 86400, %d)" % (srv[0], srv[0])) == "3 days ago", "last seen")

    # 13. the What's new strip leads with the leaderboard
    hl = B.ev('(function() for _, n in ipairs(TapCatForever.NEWS) do if n.version == "1.5.3" then return n.highlight end end end)()')
    ck(hl and hl.startswith("New: a realm leaderboard tab.") and "Join" in hl and len(hl) <= 170 and "!" not in hl, "1.5.3 What's new note: %r" % hl)

    # nobody who opted out ever sent a leaderboard message, and nothing printed with an exclamation mark
    ck(lbmsgs(E) == [] and E.heroic() == h0, "Echo (never opted in) sent nothing and got no chest")
    for c in clients.values():
        for i in range(1, c.ev("#_chat") + 1):
            line = c.ev("_chat[%d]" % i)
            ck("!" not in line and "TapCatFvr" not in line, "chat line: " + line)
    print("leaderboard section (%d clients, %d channel messages, gossip, extra fields, L1-only client, merge, caps, expiry, opt-out, sign-up chest, odd input, limits, tab, opt-in panel, sections): all checks passed"
          % (len(clients), len([1 for l in log if l[2][:3] in LB_KINDS])))

def load_addon(login=True):
    """Loads every file in the TOC into a sandboxed Lua 5.1 with the mocked WoW API."""
    lua = L.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    ns = lua.eval("{}")
    toc = open(os.path.join(ROOT, "TapCatForever.toc")).read().splitlines()
    files = [l.strip() for l in toc if l.strip().endswith(".lua")]
    for fn in files:
        src = open(os.path.join(ROOT, fn.replace("\\", "/")), encoding="utf-8").read()  # TOC paths like Sets\X.lua
        chunk = lua.execute("return function(src, name) return assert(loadstring(src, name)) end")(src, "@" + fn)
        lua.execute("return function(f) setfenv(f, setmetatable({ os = false, io = false, require = false, loadfile = false, dofile = false }, { __index = _G, __newindex = _G })) end")(chunk)
        chunk("TapCatForever", ns)
    if login:
        lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    return lua

def main():
    # every run uses new random numbers (loot, chests, skill-ups); TCF_SEED=<n> repeats a run
    seed = int(os.environ.get("TCF_SEED") or (int(time.time() * 1000) ^ os.getpid()) % 2147483647)
    print("seed:", seed)
    lua = load_addon(login=False)
    lua.execute("_seed = %d; math.randomseed(_seed); math.random(); math.random()" % seed)
    lua.execute("_artcheck = {}")
    lua.execute(TEST)
    check_capes_art()  # capes art section (see check_capes_art)
    check_leaderboard(seed)  # leaderboard section (see check_leaderboard)
    # more sections, one file each: tools/tests/test_<name>.py with check(seed, load_addon);
    # each loads its own copy of the addon (load_addon()) and raises/asserts on a failure
    import importlib.util, glob
    for path in sorted(glob.glob(os.path.join(ROOT, "tools", "tests", "test_*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        mod.check(seed, load_addon)
    art = os.path.join(ROOT, "Art")
    missing = sorted(set(f for f in lua.globals()._artcheck.values() if not os.path.exists(os.path.join(art, f.replace("\\", "/") + ".tga"))))
    print("referenced textures:", len(list(lua.globals()._artcheck.values())), "missing:", missing)
    # item art sanity
    bad = lua.execute('''
      local bad = {}
      for _, it in ipairs(TapCatForever.ITEM_LIST) do
        -- tap effects are cartoon sprites in Art/v (t_<shape>)
        local names = it.slot == "tap" and { "v/t_" .. it.art } or TapCatForever.PART_B[it.art] and { it.art .. "_a", it.art .. "_b" } or { it.art }
        for _, n in ipairs(names) do bad[#bad + 1] = n end
      end
      return bad''')
    gone = sorted(set(n for n in bad.values() if not os.path.exists(os.path.join(art, n.replace("\\", "/") + ".tga"))))  # (adv track: Art/adv\\ paths)
    print("item art missing:", gone)
    print("items:", lua.eval("#TapCatForever.ITEM_LIST"))
    return 1 if (missing or gone) else 0

if __name__ == "__main__":
    sys.exit(main())
