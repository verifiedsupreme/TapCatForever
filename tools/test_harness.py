#!/usr/bin/env python3
"""Runs the addon against a mocked WoW API (Lua 5.1 via lupa) and exercises every feature."""
import os, sys, time
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
    TCF:ToggleWindow()
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
    for tab = 1, 10 do win:SelectTab(tab) end
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
    for k = 1, 5 do TCF:OpenChest("strong") end
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
    local strongBefore = TCF.db.keys.strong + TCF.db.keys.heroic
    _inInstance = "party"; _fire("PLAYER_ENTERING_WORLD")
    for i = 1, 3 do _fire("ENCOUNTER_END", 1, "Boss", 1, 5, 1) end
    _fire("ENCOUNTER_END", 2, "Boss", 1, 5, _SECRET)   -- secret success value must not error
    TCF.db.dungeonRun.start = TCF.db.dungeonRun.start - 400
    _inInstance = false; _fire("ZONE_CHANGED_NEW_AREA")
    assert(TCF.db.keys.strong + TCF.db.keys.heroic == strongBefore + 1, "dungeon at level 20+ gives a Strongbox (or sometimes a Heroic Cache)")
    -- group-finder completion while inside a raid
    local heroicBefore = TCF.db.keys.heroic
    _inInstance = "raid"; _fire("PLAYER_ENTERING_WORLD"); _fire("LFG_COMPLETION_REWARD"); _fire("LFG_COMPLETION_REWARD")
    assert(TCF.db.keys.heroic == heroicBefore + 1, "raid completion once")
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
    ps.mats.linen = (ps.mats.linen or 0) + 100; assert(TCF:Craft(TCF.RECIPES[TCF:CraftProf()][1]), "craft the first Tailoring cosmetic")
    for _, p in ipairs(TCF.PROFESSIONS) do
      win.profSel = p.key
      for _, v in ipairs({ "main", "upg", "craft", "renown" }) do win.profView = v; win:SelectTab(5); _update(0.2) end
    end
    ps.lifetime = 1e14
    assert(TCF:PrestigeTrade(), "sell the business")
    assert(ps.gold == 0 and ps.ops.mining[1].n == 0 and ps.ops.cloth[1].n == 0 and ps.ops.skinning[1].n == 0 and TCF:ProfUnlocked("cooking"), "reset keeps unlocks")
    print("renown after selling:", ps.renown)
    -- paperdoll click (right click unequips, left click jumps to the wardrobe)
    for tab = 1, 10 do win:SelectTab(tab) end
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
    assert(TCF:GetLoadout("MAGE").acc == "race_tauren", "racial piece worn by the alt's cats")
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
    assert(not TCF.db.trade or TCF.db.trade.renown == 0, "alt has its own professions")
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
      check(#F.ops == 6 and F.tab == TAB[k] and F.craft == CRAFT[k], k .. " family table")
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
      TCF.db.trade = nil
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
    TCF:SetClass("WARRIOR"); s = TCF:ProfState()
    check(s.ops.mining[1].n == 0 and s.ops.cloth[1].n == 120, "switching class later moves nothing")
    TapCatForeverDB.chars["Oldwar-Forever"] = { class = "WARRIOR", trade = { gold = 1, ops = { mining = { { n = 5, p = 0, run = false, mgr = false } } },
      mats = { copper = 9 }, pickLvl = 4, skill = { mining = 30 }, last = time() } }
    login("Oldwar"); s = TCF:ProfState()
    check(s.ops.mining[1].n == 5 and s.mats.copper == 9 and TCF:ToolLevel("mining") == 4 and TCF:ProfSkill("mining") == 30, "an old Warrior keeps Mining")
    TapCatForeverDB.chars["Oldrogue-Forever"] = { class = "ROGUE", trade = { gold = 1 } }
    login("Oldrogue"); s = TCF:ProfState()
    check(s.ops.skinning[6] and TCF:ToolLevel() == 0 and s.mats and s.upgrades, "a sparse old save is repaired")
    TapCatForeverDB.chars["Oldmage-Forever"], TapCatForeverDB.chars["Oldwar-Forever"], TapCatForeverDB.chars["Oldrogue-Forever"] = nil, nil, nil
    login("Proftest")
    -- 4. helpers of a family that isn't the current class's keep working, offline and online
    TCF.db.trade = nil; ps = TCF:ProfState()
    ps.ops.skinning[1] = { n = 10, p = 0, run = true, mgr = true }
    ps.ops.mining[2] = { n = 3, p = 0, run = true, mgr = true }
    ps.ops.cloth[1] = { n = 5, p = 0, run = true, mgr = false }   -- started by hand, no helper: not offline
    ps.last = time() - 3600
    TCF:ProfessionsTick(true)
    local function cycles(f, i, sec) return math.floor(sec / TCF:OpCycleTime(f, i)) * TCF:OpMatsPerCycle(f, i) end
    check(ps.mats.lightleather >= cycles("skinning", 1, 3599) and ps.mats.lightleather <= cycles("skinning", 1, 3605), "Trapper worked offline while a Mage: " .. tostring(ps.mats.lightleather))
    check(ps.mats.tin >= cycles("mining", 2, 3599) and ps.mats.tin <= cycles("mining", 2, 3605), "Foreman worked offline while a Mage: " .. tostring(ps.mats.tin))
    check((ps.mats.linen or 0) == 0 and ps.gold > 0, "a spot without a helper doesn't run offline")
    local ll = ps.mats.lightleather
    for k = 1, 40 do TCF:ProfAdvance(0.25) end
    check(ps.mats.lightleather > ll, "Trapper keeps working online while a Mage")
    TCF:SetClass("WARRIOR"); ll = ps.mats.lightleather
    for k = 1, 40 do TCF:ProfAdvance(0.25) end
    check(ps.mats.lightleather > ll, "and while a Warrior")
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
    for k = 2, 24 do TCF:Craft(r1) end
    check(TCF:ProfSkill("tailoring") == 25, "orange recipe: a point every craft, got " .. TCF:ProfSkill("tailoring"))
    for k = 1, 30 do TCF:Craft(r1) end
    local sk = TCF:ProfSkill("tailoring")
    check(sk > 25 and sk < 55, "yellow/green recipe: some crafts give no point, got " .. sk)
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
    -- 7. loot notices: gear from anything but your own chest click goes to the bag with a small notice
    toasts = 0
    if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
    TCF:GrantGear(found, "Adventure")
    TCF:GrantGear(TCF:RollWorldLoot(20, "MAGE") or found, "Quest")
    check(toasts == 2 and TapCatForeverLootToasts and TapCatForeverLootToasts:IsShown(), "non-chest gear: notices")
    check(not (TapCatForeverLootReveal and TapCatForeverLootReveal:IsShown()), "non-chest gear: no loot box")
    local named = false
    for _, f in ipairs(_frames) do if f.kind == "FontString" and type(f.text) == "string" and f.text:find(found.name, 1, true) == 1 and f.shown then named = true end end
    check(named, "the notice names the item")
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
          check(toasts == 0, "chest gear: no small notice")
          check(TapCatForeverReel and TapCatForeverReel:IsShown(), "chest gear: the reel plays")
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
    ps.renownEver = math.max(ps.renownEver, 200)
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
      -- wearing the old starter: swapped, and a two-handed staff clears the off hand
      if old and new and old.id ~= new.id and off then
        for k in pairs(eq) do eq[k] = nil end
        eq.MAINHAND = old.id; bag[old.id] = 1
        if old.slot ~= "2H" then eq.OFFHAND = off.id; bag[off.id] = 1 end
        cd.starterFixed = nil; TCF:FixStarterWeapons()
        check(eq.MAINHAND == new.id, "starter fix swaps the old starter")
        if new.slot == "2H" then check(eq.OFFHAND == nil, "two-handed starter clears the off hand") end
        check((bag[old.id] or 0) >= 1, "old starter stays in the bag")
      end
      for k in pairs(eq) do eq[k] = nil end
      for k, v in pairs(saveEq) do eq[k] = v end
    end
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
    -- 11. What's new strip and Patch notes
    do
      local realVersion = TCF.version
      TCF.version = TCF.NEWS[1].version
      check(TCF.NEWS[1].highlight ~= nil and TCF:CurrentNews() == TCF.NEWS[1], "current version has news")
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
    print("class professions, crafted gear, party cats and loot notices: all checks passed")
    end
    -- every referenced art file must exist
    local missing = {}
    for path in pairs(_textures) do
      local f = path:match("AddOns\\TapCatForever\\Art\\(.+)$")
      if f then _artcheck[#_artcheck + 1] = f end
    end
    print("chat lines:", #_chat)
    for i = 1, 6 do print("  " .. _chat[i]) end
    for i = #_chat - 3, #_chat do print("  " .. _chat[i]) end
    '''

def load_addon(login=True):
    """Loads every file in the TOC into a sandboxed Lua 5.1 with the mocked WoW API."""
    lua = L.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    ns = lua.eval("{}")
    toc = open(os.path.join(ROOT, "TapCatForever.toc")).read().splitlines()
    files = [l.strip() for l in toc if l.strip().endswith(".lua")]
    for fn in files:
        src = open(os.path.join(ROOT, fn), encoding="utf-8").read()
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
    gone = sorted(set(n for n in bad.values() if not os.path.exists(os.path.join(art, n + ".tga"))))
    print("item art missing:", gone)
    print("items:", lua.eval("#TapCatForever.ITEM_LIST"))
    return 1 if (missing or gone) else 0

if __name__ == "__main__":
    sys.exit(main())
