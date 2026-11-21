#!/usr/bin/env python3
"""Runs the addon against a mocked WoW API (Lua 5.1 via lupa) and exercises every feature."""
import os, sys
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
  LFG_COMPLETION_REWARD = 1 } -- SENT left out on purpose to exercise the fallback
_inInstance = false
function UnitLevel() return 25 end
function UnitRace() return _race or "Orc", _race or "Orc", 2 end
_charName = "Kittyhawk"
function UnitName() return _charName end
function GetRealmName() return "Forever" end
function IsInInstance() if _inInstance then return true, _inInstance end return false, "none" end
function GetInstanceInfo() return "The Deadmines", _inInstance, 1, "Normal", 5, 0, false, 36 end
function UnitClass() return "Mage", "MAGE" end
function InCombatLockdown() return false end
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
    for k = 1, 10 do _clock = _clock + 2; assert(TCF:MineClick(1), "mine copper by hand") end
    assert(not TCF:MineClick(1), "pickaxe has a cooldown")
    assert(ps.gold >= 10 and (ps.mats.copper or 0) >= 10, "hand mining gives gold and ore")
    assert(not TCF:MineClick(2), "tin needs a vein first")
    assert(TCF:BuyOp("mining", 1, 1), "buy first copper vein")
    for k = 1, 3000 do
      kb.scripts.OnKeyDown(kb, "Q"); _update(0.25)
      if k % 4 == 0 then TCF:MineClick(1) end
      for i = 6, 1, -1 do TCF:BuyOp("mining", i, "max") end
      for i = 1, 6 do TCF:HireForeman("mining", i) end
      for _, u in ipairs(TCF.UPGRADES.mining) do TCF:BuyUpgrade(u.id) end
    end
    local o = ps.ops.mining
    print(string.format("mining after ~12 min: gold %s lifetime %s veins %d/%d/%d/%d/%d/%d pick tier %d skill %d",
      TCF.FormatBig(ps.gold), TCF.FormatBig(ps.lifetime), o[1].n, o[2].n, o[3].n, o[4].n, o[5].n, o[6].n, TCF:PickLevel(), TCF:ProfSkill("mining")))
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
    ps.mats.copper = 100; assert(TCF:Craft(TCF.RECIPES.mining[1]), "craft copper sparks")
    for _, p in ipairs(TCF.PROFESSIONS) do
      win.profSel = p.key
      for _, v in ipairs({ "main", "upg", "craft", "renown" }) do win.profView = v; win:SelectTab(5); _update(0.2) end
    end
    ps.lifetime = 1e14
    assert(TCF:PrestigeTrade(), "sell the business")
    assert(ps.gold == 0 and ps.ops.mining[1].n == 0 and TCF:ProfUnlocked("cooking"), "reset keeps unlocks")
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
    lua = load_addon(login=False)
    lua.execute("_artcheck = {}")
    lua.execute(TEST)
    art = os.path.join(ROOT, "Art")
    missing = sorted(set(f for f in lua.globals()._artcheck.values() if not os.path.exists(os.path.join(art, f.replace("\\", "/") + ".tga"))))
    print("referenced textures:", len(list(lua.globals()._artcheck.values())), "missing:", missing)
    # item art sanity
    bad = lua.execute('''
      local bad = {}
      for _, it in ipairs(TapCatForever.ITEM_LIST) do
        local names = TapCatForever.PART_B[it.art] and { it.art .. "_a", it.art .. "_b" } or { it.art }
        for _, n in ipairs(names) do bad[#bad + 1] = n end
      end
      return bad''')
    gone = sorted(set(n for n in bad.values() if not os.path.exists(os.path.join(art, n + ".tga"))))
    print("item art missing:", gone)
    print("items:", lua.eval("#TapCatForever.ITEM_LIST"))
    return 1 if (missing or gone) else 0

if __name__ == "__main__":
    sys.exit(main())
