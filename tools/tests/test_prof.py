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
local T = TapCatForever
T:SetClass("MAGE")
local ps = T:ProfState()
local fam = T:MainProf()
check(T:SpeedLevel(fam) == 0 and math.abs(T:ToolCooldown(fam, 0) - 1.5) < 1e-9, "no hand speed at first: 1.5s")
check(math.abs(T:ToolCooldown(fam, 60, 0) - 0.75) < 1e-9, "tool alone stops at 0.75s")
check(math.abs(T:ToolCooldown(fam, 60, T.SPEED_MAX) - 0.25) < 1e-6, "hand speed max with a good tool: 0.25s")
check(math.abs(T:ClicksPerSecond(fam, 60, T.SPEED_MAX) - 4) < 1e-6, "4 clicks a second at most")
local prev, prevRatio = 0, 0
for l = 0, T.SPEED_MAX - 1 do
  local c = T:SpeedCost(fam, l)
  check(c and c > prev, "hand speed costs rise: " .. l)
  if l >= 2 then check(c / prev >= prevRatio * 0.97, "and rise faster and faster: " .. l) end
  if l >= 1 then prevRatio = c / prev end
  prev = c
  local a, b = T:ToolCooldown(fam, 0, l), T:ToolCooldown(fam, 0, l + 1)
  check(b < a, "every level is faster")
end
check(T:SpeedCost(fam, 0) <= 1e5 and T:SpeedCost(fam, T.SPEED_MAX - 1) >= 1e16, "first level cheap, last one a long-term goal")
check(T:SpeedCost(fam, T.SPEED_MAX) == nil, "nothing past the top")
-- buying: spends Trade Gold, one level per buy, per family
ps.gold = 0
check(not T:UpgradeSpeed(fam), "no gold, no hand speed")
ps.gold = T:SpeedCost(fam) + 5
check(T:UpgradeSpeed(fam) and T:SpeedLevel(fam) == 1 and math.abs(ps.gold - 5) < 1e-6, "bought level 1")
check(T:SpeedLevel("mining") == 0, "other families keep their own")
-- clicks by hand follow the shorter cooldown
ps.tools[fam] = 60
ps.speed[fam] = T.SPEED_MAX
T.toolNext = {}
local clicks = 0
for k = 1, 2000 do _clock = _clock + 0.01; if T:GatherClick(fam, 1) then clicks = clicks + 1 end end
check(clicks >= 74 and clicks <= 81, "20 seconds at 0.25s: about 80 clicks, got " .. clicks)
-- selling the business keeps it (the tool resets)
ps.lifetime = math.max(ps.lifetime, 1e12)
check(T:PrestigeTrade(), "sell the business")
check(T:SpeedLevel(fam) == T.SPEED_MAX and T:ToolLevel(fam) == 0, "hand speed kept, tool reset")
check(math.abs(T:ToolCooldown(fam) - 0.5) < 1e-6, "fresh tool with max hand speed: 0.5s")
-- the page: Hand speed button and the clicks-a-second line
ps.speed[fam] = 3
ps.ops[fam][1].n = 1
T:CreateWindow(); T.window:Show(); T.window:SelectTab(5)
T.window.profView = "main"; T.window:Refresh()
local btn, line = false, false
for _, f in ipairs(_frames) do
  local t = f.GetText and f:GetText()
  if type(t) == "string" and t:find("Hand speed 4", 1, true) then btn = true end
  if type(t) == "string" and t:find("clicks a second", 1, true) and t:find("kept when you sell", 1, true) then line = true end
end
check(btn and line, "spots page shows the Hand speed button and clicks a second")
ps.speed[fam] = nil
'''


def run(lua, code, name):
    lua.execute(PRE)
    lua.execute(code)
    fails = list(lua.eval("_fails").values())
    if fails:
        raise AssertionError(name + ": " + "; ".join(fails[:12]))


def check(seed, load_addon):
    lua = load_addon()
    run(lua, CURVE, "professions skill-up curve")
    print("professions skill-up curve section (orange 100%, yellow 50%, green 20%/5%, grey 0, every list reaches 300, colours): all checks passed")
    run(lua, STARTER, "professions starter sets")
    run(lua, SPEED, "professions hand speed")
    print("professions hand speed section (separate upgrade per family, steep costs, 1.5s to 0.25s, kept when selling, page): all checks passed")
    print("professions starter sets section (a white piece for every armour slot per craft, cheap, wearable, progress, shown first): all checks passed")
