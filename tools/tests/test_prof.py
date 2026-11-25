# 1.6 professions (prof track): the skill-up curve. More sections join this file as features land.
PRE = r'''
local T = TapCatForever
_fails = {}
function check(ok, msg) if not ok then _fails[#_fails + 1] = tostring(msg) end end
-- quiet: no chat lines or sounds in these checks
T.PlaySound = function() end
'''

CURVE = r'''
local T = TapCatForever
-- the bands: gap < 5 always, < 15 half, < 30 1 in 5, < 50 1 in 20, then never (gathering too)
local C = T.SkillUpChance
check(C(1, 1) == 1 and C(5, 1) == 1 and C(6, 1) == 0.5 and C(15, 1) == 0.5 and C(16, 1) == 0.2
  and C(30, 1) == 0.2 and C(31, 1) == 0.05 and C(50, 1) == 0.05 and C(51, 1) == 0 and C(1, 250) == 1, "skill-up bands")
check(C(300, 290) == 0, "no points at 300")
local col, word = T.SkillUpColor(10, 1)
check(col == "|cffffff00" and word == "often", "yellow is often: " .. tostring(word))
check(select(2, T.SkillUpColor(200, 1)) == "no longer" and select(2, T.SkillUpColor(1, 100)) == "always", "grey and orange words")
check(T.SkillUpLine(40, 1) == "Still teaches you: rarely", "tooltip line: " .. T.SkillUpLine(40, 1))
check(T.SpotDifficulty(1) == 0 and T.SpotDifficulty(6) == 250, "spot difficulty")
-- measured: crafting the same skill-1 recipe stops at 51; a grey one never gives a point
T:SetClass("MAGE")
local ps = T:ProfState()
ps.skill.tailoring = nil
local r1
for _, r in ipairs(T.RECIPES.tailoring) do if r.gear and r.skill == 1 then r1 = r; break end end
local n5 = 0
for k = 1, 5 do T:ProfSkillUp("tailoring", 1) end
check(T:ProfSkill("tailoring") == 6, "the first five always give a point: " .. T:ProfSkill("tailoring"))
for k = 1, 20000 do T:ProfSkillUp("tailoring", 1) end
check(T:ProfSkill("tailoring") == 51, "a skill-1 recipe teaches up to 51, got " .. T:ProfSkill("tailoring"))
-- gathering: clicking the first spot by hand stops at 50 too (spot 1 is difficulty 0)
ps.skill.cloth = nil
for k = 1, 20000 do T:ProfSkillUp("cloth", T.SpotDifficulty(1)) end
check(T:ProfSkill("cloth") == 50, "the first spot teaches up to 50, got " .. T:ProfSkill("cloth"))
for k = 1, 20000 do T:ProfSkillUp("cloth", T.SpotDifficulty(6)) end
check(T:ProfSkill("cloth") == 300, "the sixth spot teaches up to 300, got " .. T:ProfSkill("cloth"))
-- every list can be climbed to 300 with its teach levels (no gap leaves you stuck)
local function climb(list, req, teach, key)
  ps.skill[key] = nil
  for guard = 1, 400 do
    local sk = T:ProfSkill(key)
    if sk >= 300 then break end
    local best
    for _, e in ipairs(list) do if req(e) <= sk then best = e end end
    for k = 1, 3000 do if T:ProfSkillUp(key, teach(best)) then break end end
  end
  return T:ProfSkill(key)
end
check(climb(T.SEEDS, function(e) return e[7] end, function(e) return e.teach end, "herbalism") == 300, "Herbalism reaches 300")
check(climb(T.BANDAGES, function(e) return e[7] end, function(e) return e.teach end, "firstaid") == 300, "First Aid reaches 300")
check(climb(T.FISHING_SPOTS, function(e) return e.skill end, function(e) return e.teach end, "fishing") == 300, "Fishing reaches 300")
check(climb(T.COOK_RECIPES, function(e) return e[5] end, function(e) return e.teach end, "cooking") == 300, "Cooking reaches 300")
for _, key in ipairs({ "blacksmithing", "leatherworking", "tailoring" }) do
  local gear = {}
  for _, r in ipairs(T.RECIPES[key]) do if r.gear then gear[#gear + 1] = r end end
  check(climb(gear, function(e) return e.skill end, function(e) return e.skill end, key) == 300, key .. " reaches 300")
end
for _, sd in ipairs(T.SEEDS) do check(sd.teach >= sd[7], "seed teach level " .. sd[1]) end
-- the Crafting page shows the colours and the tooltip line
ps.skill.tailoring = 20
T:CreateWindow(); T.window:Show(); T.window:SelectTab(5)
T.window.profView = "craft"; T.window:Refresh()
local colored = false
for _, f in ipairs(_frames) do
  local t = f.GetText and f:GetText()
  if type(t) == "string" and t:find("Skill 1|r", 1, true) and t:find("|cff40c040Skill 1", 1, true) then colored = true end
end
check(colored, "a skill-1 recipe at skill 20 shows green")
ps.skill.tailoring = nil; ps.skill.cloth = nil
for _, k in ipairs({ "herbalism", "firstaid", "fishing", "cooking" }) do ps.skill[k] = nil end
'''


STARTER = r'''
local T = TapCatForever
local FAM_CLASS = { blacksmithing = "WARRIOR", leatherworking = "ROGUE", tailoring = "MAGE" }
local NEED = { WRIST = true, LEGS = true, CHEST = true, HANDS = true, FEET = true, WAIST = true }
for craft, cls in pairs(FAM_CLASS) do
  T:SetClass(cls)
  local set = T.CRAFT_STARTER[craft]
  check(set and #set >= 7, craft .. " starter set has 7 slots")
  local slots, recipeOf = {}, {}
  for _, r in ipairs(T.RECIPES[craft]) do if r.gear then recipeOf[r.gear] = r end end
  for _, ids in ipairs(set) do
    for _, id in ipairs(ids) do
      local it, r = T.GEAR[id], recipeOf[id]
      check(it and it.q == 1 and it.crafted == craft, craft .. " starter piece is white and crafted: " .. tostring(id))
      check(r and r.starter and r.skill <= 35, craft .. " starter recipe at low skill: " .. tostring(id))
      local cost = 0
      for m, n in pairs(r and r.mats or {}) do cost = cost + n; check(T.CRAFT_MAT_TIER[m] == 1, "starter uses tier-1 materials") end
      check(cost <= 12, craft .. " starter piece is cheap: " .. cost)
      check(it.slot ~= "FINGER" and it.slot ~= "NECK" and it.slot ~= "TRINKET", "no rings, necks or trinkets")
      check(T:GearUsable(it, cls), cls .. " can wear " .. it.name)
      slots[it.slot] = true
    end
  end
  for k in pairs(NEED) do check(slots[k], craft .. " starter set covers " .. k) end
  if craft ~= "blacksmithing" then check(slots.BACK, craft .. " starter set has a cloak") end
  if craft == "blacksmithing" then check(slots.MH or slots["2H"], "blacksmithing starter set has a weapon") end
  -- progress: crafting a piece, a piece in the bag or worn all count
  local ps = T:ProfState()
  ps.starterMade = nil
  local bag = T:Bag()
  for _, ids in ipairs(set) do for _, id in ipairs(ids) do bag[id] = nil end end
  local done, total = T:StarterProgress(craft)
  check(done == 0 and total == #set, craft .. " starter progress starts at 0: " .. done)
  local r1 = recipeOf[set[1][1]]
  for m, n in pairs(r1.mats) do ps.mats[m] = (ps.mats[m] or 0) + n end
  check(T:Craft(r1), "craft the first starter piece")
  check(T:StarterProgress(craft) == 1, craft .. " 1 made")
  bag[set[1][1]] = nil
  check(T:StarterProgress(craft) == 1, "made once still counts after selling it")
  bag[set[2][1]] = 1
  check(T:StarterProgress(craft) == 2, "a piece in the bag counts")
  bag[set[2][1]] = nil
  ps.starterMade = nil
end
-- the Crafting page: the starter set comes first at low skill, with its progress at the top
T:SetClass("MAGE")
local ps = T:ProfState()
ps.skill.tailoring = nil
T:CreateWindow(); T.window:Show(); T.window:SelectTab(5)
T.window.profView = "main"; T.window:Refresh()
T.window.profView = "craft"; T.window:Refresh()
local head, starterRows = false, 0
for _, f in ipairs(_frames) do
  local t = f.shown ~= false and f.GetText and f:GetText()
  if type(t) == "string" and t:find("Starter set 0/7 made", 1, true) then head = true end
  if type(t) == "string" and t:find("Starter set|r", 1, true) then starterRows = starterRows + 1 end
end
check(head, "Crafting page shows Starter set 0/7 made")
check(starterRows >= 7, "the first rows are the starter set: " .. starterRows)
'''


SPEED = r'''
-- Hand speed was tried during 1.6 testing and taken out: the click only gets a little faster with the tool
local T = TapCatForever
T:SetClass("MAGE")
local ps = T:ProfState()
local fam = T:MainProf()
check(math.abs(T:ToolCooldown(fam, 0) - 1.5) < 1e-9, "a new tool: 1.5s a click")
check(math.abs(T:ToolCooldown(fam, 60) - 0.75) < 1e-9, "the tool stops at 0.75s")
check(T:ToolCooldown(fam, 20) < T:ToolCooldown(fam, 10), "every tool level a little faster")
-- an old save that bought Hand speed levels clicks like everyone else
ps.tools[fam] = 60
ps.speed[fam] = T.SPEED_MAX
T.toolNext = {}
local clicks = 0
for k = 1, 2000 do _clock = _clock + 0.01; if T:GatherClick(fam, 1) then clicks = clicks + 1 end end
check(clicks >= 25 and clicks <= 28, "20 seconds at 0.75s: about 27 clicks, got " .. clicks)
-- the page: no Hand speed button or text, the clicks a second line names the tool
ps.speed[fam] = 3
ps.ops[fam][1].n = 1
T:CreateWindow(); T.window:Show(); T.window:SelectTab(5)
T.window.profView = "main"; T.window:Refresh()
local btn, line = false, false
for _, f in ipairs(_frames) do
  local t = f.GetText and f:GetText()
  if type(t) == "string" and f.shown and t:find("Hand speed", 1, true) then btn = true end
  if type(t) == "string" and t:find("clicks a second", 1, true) and t:find("a little faster", 1, true) then line = true end
end
check(not btn and line, "spots page: no Hand speed, clicks a second with the tool")
ps.speed[fam] = nil
'''


COSMETIC = r'''
local T = TapCatForever
local function find(key, item) for _, r in ipairs(T.RECIPES[key]) do if r.item == item then return r end end end
check(find("tailoring", "craft_tl_scarf").mats.linen == 300, "an uncommon cosmetic costs 5x (60 -> 300 linen)")
check(find("tailoring", "craft_tl_felwings").mats.felcloth == 16000 and find("tailoring", "craft_tl_felwings").mats.runecloth == 48000, "a legendary one 40x")
local skin = find("tailoring", "skin_runestitch")
check(skin and skin.mats.runecloth == 9000 and T.ITEMS.skin_runestitch.get.mats == skin.mats, "a fur colour costs 10x and the Compendium shows the same")
check(find("herbalism", "craft_lotus_bloom").mats.lotus == 60 and find("fishing", "craft_pinchy_gift").mats.pinchy == 5, "rare inputs unchanged")
check(find("cooking", "craft_chef_spice").mats.d_chili == 25 and find("cooking", "craft_chef_spice").mats.hotspice == 100, "dishes and spices unchanged")
check(find("firstaid", "craft_onyxia_cloak").mats.b_heavyrunecloth == 100, "bandages unchanged")
-- gear recipes are the CraftData.lua amounts
for key, list in pairs(T.CRAFT_RECIPES) do
  local byGear = {}
  for _, r in ipairs(list) do byGear[r.gear] = r end
  for _, r in ipairs(T.RECIPES[key]) do
    if r.gear then
      for m, n in pairs(r.mats) do check(byGear[r.gear].mats[m] == n, "gear recipe unchanged: " .. r.gear) end
    end
  end
end
'''


SPOTS = r'''
local T = TapCatForever
T:SetClass("MAGE")
local ps = T:ProfState()
local fam = T:MainProf()
check(T:SpotCount() == 9, "9 spots per family")
for _, k in ipairs(T.FAMILY_KEYS) do
  check(#T.FAMILIES[k].ops == 9, k .. " has 9 spots")
  for i, o in ipairs(T.FAMILIES[k].ops) do check(T.MAT_BY_KEY[o[2]] and o[4], k .. " spot " .. i .. " material") end
  check(#ps.ops[k] == 9, "trade has 9 spot states for " .. k)
end
ps.renownEver, ps.renown, ps.lifetime, ps.spotsOpen = 0, 0, 0, nil
ps.skill[fam] = 1
-- (1.7.4) a ladder: a spot opens once you own one of the spot before it
for i = 1, 9 do ps.ops[fam][i].n = 0 end
local ok, why = T:SpotUnlocked(fam, 3)
check(T:SpotUnlocked(fam, 1) and not T:SpotUnlocked(fam, 2) and not ok and why:find("first", 1, true), "spot 3 needs spot 2 first: " .. tostring(why))
ps.ops[fam][1].n = 1
check(T:SpotUnlocked(fam, 2) and not T:SpotUnlocked(fam, 3), "owning spot 1 opens spot 2 only")
ps.ops[fam][3].n = 2
check(T:SpotUnlocked(fam, 3), "a spot you own stays open")
for i = 1, 6 do ps.ops[fam][i].n = 1 end
ok, why = T:SpotUnlocked(fam, 7)
check(T:SpotUnlocked(fam, 6) and not ok and why:find("Renown 100", 1, true), "spot 7 opens at Renown 100: " .. tostring(why))
ps.gold = 1e30
check(not T:BuyOp(fam, 7, 1) and T:OpMaxBuy(fam, 7) == 0, "a closed spot can't be bought")
ps.renownEver = 100
check(T:SpotUnlocked(fam, 7) and T:BuyOp(fam, 7, 1) and ps.ops[fam][7].n == 1, "Renown 100 opens spot 7")
ps.renownEver = 0
check(T:SpotUnlocked(fam, 7), "an open spot stays open")
ps.renownEver = 600
ok, why = T:SpotUnlocked(fam, 8)
check(not ok and why:find("skill 250", 1, true), "spot 8 also needs the gathering skill: " .. tostring(why))
ps.skill[fam] = 250
check(T:SpotUnlocked(fam, 8), "spot 8 open")
ps.ops[fam][8].n = 1   -- (1.7.4) the ladder: spot 9 needs one of spot 8
ok, why = T:SpotUnlocked(fam, 9)
check(not ok and why:find("Trade Gold earned", 1, true) and why:find("skill 300", 1, true), "spot 9 needs 1Qa earned and skill 300: " .. tostring(why))
ps.lifetime, ps.skill[fam] = 1e15, 300
check(T:SpotUnlocked(fam, 9) and T:BuyOp(fam, 9, 1), "spot 9 open")
check(T:GatherIncome(fam) > 0 and T:OpRevenue(fam, 9) > 0, "later spots earn")
for i = 7, 9 do check(T.PROF_OPS[i].rev > T.PROF_OPS[i - 1].rev, "spot " .. i .. " earns more per spot than spot " .. (i - 1)) end
check(T:HireForeman(fam, 9) and ps.ops[fam][9].mgr, "a helper for spot 9")
local m0 = ps.mats.wartorn or 0
T:ProfAdvance(T:OpCycleTime(fam, 9) + 1)
check((ps.mats.wartorn or 0) > m0, "spot 9 gives Wartorn Cloth Scrap")
-- later spots have upgrades too
local n9 = 0
for _, u in ipairs(T.UPGRADES[fam]) do if u.op == 9 then n9 = n9 + 1 end end
check(n9 == 3, "spot 9 has its profit upgrades")
local sv = { ps.renownEver, ps.lifetime, ps.skill[fam] }
ps.spotsOpen, ps.renownEver, ps.lifetime, ps.skill[fam] = { [7] = true }, 0, 0, 1
check(not T:BuyUpgrade(fam .. "8_0"), "no profit upgrade for a spot that hasn't opened")
ps.spotsOpen[8], ps.spotsOpen[9] = true, true
ps.renownEver, ps.lifetime, ps.skill[fam] = sv[1], sv[2], sv[3]
-- the page scrolls to the later spots
ps.ops[fam][1].n = 3
T:CreateWindow(); T.window:Show(); T.window:SelectTab(5)
T.window.profView = "main"; T.window:Refresh()
local function texts()
  local all = {}
  for _, f in ipairs(_frames) do local t = f.GetText and f:GetText(); if type(t) == "string" then all[#all + 1] = t end end
  return table.concat(all, "\n")
end
local tx = texts()
check(tx:find("7-9 of 9", 1, true) and tx:find("Cult of the Damned (Naxxramas)", 1, true), "the page opens on the newest spots (whole pages: 7-9)")
T.window.spotScroll = 0; T.window:Refresh()
check(texts():find("1-6 of 9", 1, true), "scrolled back to the first spots")
-- selling resets them like the others, the spots stay open
ps.lifetime = math.max(ps.lifetime, 1e15); ps.runEarned = ps.lifetime
T:PrestigeTrade()
check(ps.ops[fam][9].n == 0 and not ps.ops[fam][9].mgr and not T:SpotUnlocked(fam, 9) and T:SpotUnlocked(fam, 1), "(1.7.4) selling resets spot 9: the ladder starts again from the first spot")
for i = 1, 8 do ps.ops[fam][i].n = 1 end
check(T:SpotUnlocked(fam, 9), "and spot 9's own gate stays opened (Renown, skill)")
-- 1.6.0: no round Professions button in the header any more; the Professions tab opens it
check(T.window.profQuick == nil and T.UI.ProfQuickButton == nil, "no Professions button by the title")
T.window:SelectTab(1)
T.window.tabButtons[5].scripts.OnClick(T.window.tabButtons[5])
check(T.window.tab == 5, "the Professions tab opens it")
local function tipOf(owner)
  local lines = {}
  GameTooltip.AddLine = function(_, t) lines[#lines + 1] = tostring(t) end
  owner:GetScript("OnEnter")(owner)
  GameTooltip.AddLine = nil
  return table.concat(lines, "\n")
end
local tip
-- the later spots say their material has no recipe yet; the early ones don't
check(T.MatUsedInRecipe("linen") and not T.MatUsedInRecipe("wartorn"), "linen is used in recipes, Wartorn Cloth Scrap not yet")
T.window.profView = "main"; T.window.spotScroll = 3; T.window:Refresh()
local row9
for _, f in ipairs(_frames) do if f.spot == 9 and f.box then row9 = f end end
check(row9, "a row shows spot 9 after scrolling")
if row9 then
  tip = tipOf(row9.box)
  check(tip:find("not used in any recipe yet", 1, true), "spot 9 tooltip: " .. tip)
end
ps.ops[fam][1].n = math.max(1, ps.ops[fam][1].n)
T.window.spotScroll = 0; T.window:Refresh()
-- the click line reads as clicks a second, not as a level number
local hint
for _, f in ipairs(_frames) do local t = f.GetText and f:GetText(); if type(t) == "string" and t:find("By hand:", 1, true) and f.shown then hint = t end end
check(hint and hint:find("clicks a second", 1, true) and not hint:find("Hand speed", 1, true), "click hint: " .. tostring(hint))
'''

GLITCH = r'''
local T = TapCatForever
T:SetClass("MAGE")
local ps = T:ProfState()
local fam = T:MainProf()
local function chat(pat) for k = #_chat, 1, -1 do if tostring(_chat[k]):find(pat, 1, true) then return _chat[k] end end end
-- tied to the patch
local saveV = T.version
T.version = "1.6.0"; check(T:GlitchPatchActive(), "on in 1.6.x")
T.version = "1.6.2"; check(T:GlitchPatchActive(), "on in 1.6.2")
T.version = "1.7.0"; check(not T:GlitchPatchActive(), "off in 1.7")
T.version = "1.16.0"; check(not T:GlitchPatchActive(), "off in 1.16")
T.version = saveV
-- off: never happens
T.glitchForce = false
T.GLITCH_ODDS = 1
T.toolNext = {}
for k = 1, 20 do _clock = _clock + 2; T:GatherClick(fam, 1) end
check(not T:Glitch() and not chat("Something is wrong"), "no glitch outside the patch")
-- on: a click can start it (odds forced to 1 here)
T.glitchForce = true
T:SetGlitchDay(nil)
ps.ops[fam][1].n = 50
_clock = _clock + 2
check(T:GatherClick(fam, 1) and T:Glitch(), "a click by hand started a glitch")
local line = chat("Something is wrong at your Defias Hideout (Westfall) spot.")
check(line and not line:find("!", 1, true), "one quiet chat line: " .. tostring(line))
-- review fix: once a day per WoW character, kept in that character's own data
check(rawget(TapCatForeverDB, "profGlitchDay") == nil and T.charData and T.charData.profGlitchDay == date("%Y-%m-%d"),
  "the glitch day is saved per character, not for the account")
local g0, m0 = ps.gold, ps.mats.linen or 0
_clock = _clock + 2
check(T:GatherClick(fam, 1), "click the glitched spot")
check(ps.gold - g0 >= T:ToolGold(fam, 1) * 10 and (ps.mats.linen or 0) - m0 >= 3, "a glitched click pays far more")
-- only that spot
ps.ops[fam][2].n = 5
local gl = T:Glitch()
check(gl.i == 1 and gl.clicks == 1, "the glitch is on spot 1")
-- the page shows it (flickering name, time left)
T:CreateWindow(); T.window:Show(); T.window:SelectTab(5); T.window.profView = "main"; T.window.spotScroll = 0; T.window:Refresh()
local shown = false
for _, f in ipairs(_frames) do local t = f.GetText and f:GetText(); if type(t) == "string" and t:find("Work it by hand", 1, true) then shown = true end end
check(shown, "the glitched row says to work it by hand")
-- it ends after a minute with a summary line
_clock = _clock + T.GLITCH_SECONDS + 1
T:ProfessionsTick(false, 0.25)
check(not T:Glitch() and chat("Your Defias Hideout (Westfall) spot is back to normal. While it lasted it paid"), "a line when it ends")
-- once a day
local n = 0
for k = 1, 30 do _clock = _clock + 2; T:GatherClick(fam, 1); if T:Glitch() then n = n + 1 end end
check(n == 0, "only once a day")
-- another character on the account has its own glitch that day; back on this one, still used up
local mine = T.charData
T.charData = {}
_clock = _clock + 2
T:GatherClick(fam, 1)
check(T:Glitch(), "an alt can still find its own glitch the same day")
T.profGlitch = nil
T.charData = mine
for k = 1, 10 do _clock = _clock + 2; T:GatherClick(fam, 1) end
check(not T:Glitch(), "this character's glitch stays used up")
-- with chat lines off, the end line shows only while you still play that cat
local function countBack() local c = 0; for _, l in ipairs(_chat) do if tostring(l):find("back to normal", 1, true) then c = c + 1 end end; return c end
T.db.ui.chat = false
T:SetGlitchDay(nil); _clock = _clock + 2; T:GatherClick(fam, 1)
check(T:Glitch(), "glitch for the chat-off check")
local before = countBack()
_clock = _clock + T.GLITCH_SECONDS + 1; T:ProfessionsTick(false, 0.25)
check(countBack() == before + 1, "the end line answers your clicks even with chat lines off")
T:SetGlitchDay(nil); _clock = _clock + 2; T:GatherClick(fam, 1)
check(T:Glitch(), "glitch for the class switch check")
T:SetClass("ROGUE")
before = countBack()
_clock = _clock + T.GLITCH_SECONDS + 1; T:ProfessionsTick(false, 0.25)
check(not T.profGlitch and countBack() == before, "no end line for a cat you switched away from, with chat lines off")
T:SetClass("MAGE")
T.db.ui.chat = true
-- sixteen past the hour: the first click starts it, without luck
T:SetGlitchDay(nil)
T.GLITCH_ODDS = 1e9
local realDate = date
date = function(fmt, ...) if fmt == "%M" then return "16" end return realDate(fmt, ...) end
_clock = _clock + 2
T:GatherClick(fam, 1)
check(T:Glitch(), "sixteen past the hour starts it")
date = function(fmt, ...) if fmt == "%M" then return "17" end return realDate(fmt, ...) end
T.profGlitch = nil; T:SetGlitchDay(nil)
for k = 1, 30 do _clock = _clock + 2; T:GatherClick(fam, 1) end
check(not T:Glitch(), "not at seventeen past without luck")
date = realDate
-- helpers and other cats never glitch
T:SetGlitchDay(nil); T.GLITCH_ODDS = 1
T:WithTradeClass("WARRIOR", function(self) self.toolNext = {}; self:GatherClick("mining", 1) end)
check(not T:Glitch(), "a cat you aren't playing never glitches")
T.glitchForce, T.GLITCH_ODDS = nil, 3000
'''


def run(lua, code, name):
    lua.execute(PRE)
    lua.execute(code)
    fails = list(lua.eval("_fails").values())
    if fails:
        raise AssertionError(name + ": " + "; ".join(fails[:12]))


SECTIONS = [
    (CURVE, "professions skill-up curve", "orange 100%, yellow 50%, green 20%/5%, grey 0, every list reaches 300, colours"),
    (STARTER, "professions starter sets", "a white piece for every armour slot per craft, cheap, wearable, progress, shown first"),
    (SPEED, "professions click speed", "Hand speed taken out: 1.5s to 0.75s with the tool only, old saves too, page"),
    (COSMETIC, "professions cosmetic costs", "Cosmetic only recipes cost 3x-40x by rarity, rare inputs and gear recipes unchanged"),
    (SPOTS, "professions later spots", "spots 7-9 open with Renown, skill and Trade Gold earned, buy, helpers, scroll, reset on sale, header button"),
    (GLITCH, "professions patch secret", "a glitched spot: only in 1.6, by hand, once a day, sixteen past the hour, quiet lines"),
]


def check(seed, load_addon):
    # each section on a fresh copy of the addon, so one can't change what the next one sees
    for code, name, what in SECTIONS:
        lua = load_addon()
        lua.execute("math.randomseed(%d)" % (seed % 2147483647))
        run(lua, code, name)
        print("%s section (%s): all checks passed" % (name, what))
