# 1.7.0: test mode is only ever on for the developer's one character, Ziggu Trip. No password, no other
# character (not even "Ziggu"); a save that had it on elsewhere has it turned off.

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local realName, realFull = _charName, UnitFullName
      local on = function() return T.RealTestModeOn(T) end
      local function as(name) _charName = name; T.db.ui.testMode = nil end
      -- other characters: the old password and the other old name do nothing
      for _, n in ipairs({ "Ziggu", "Zigguu", "Someone", "Trip" }) do
        as(n)
        SlashCmdList.TAPCATFOREVER("testmode ziggu")
        SlashCmdList.TAPCATFOREVER("testmode")
        ck(not T.db.ui.testMode and not on(), n .. ": no test mode")
      end
      -- a save with it on, played on another character: off, and its shortcuts do nothing
      as("Someone"); T.db.ui.testMode = true
      local coins = T.db.coins
      T.TestModeOn = T.RealTestModeOn
      T:TestCheat("coins")
      ck(T.db.coins == coins and not T.db.ui.testMode, "shortcuts locked elsewhere")
      ck(not T:IsDeveloper(), "not the developer")
      -- the developer's character, with its name whole or in two parts
      as("Ziggu Trip")
      SlashCmdList.TAPCATFOREVER("testmode")
      ck(T.db.ui.testMode and on(), "Ziggu Trip turns it on")
      T:TestCheat("coins")
      ck(T.db.coins == coins + 5000, "shortcuts work there")
      SlashCmdList.TAPCATFOREVER("testmode")
      ck(not T.db.ui.testMode, "and off again")
      as("Ziggu"); UnitFullName = function() return "Ziggu", "Trip" end
      SlashCmdList.TAPCATFOREVER("testmode")
      ck(T.db.ui.testMode and on(), "Ziggu + Trip (two parts) is the same character")
      UnitFullName = function() return "Ziggu", "" end
      ck(not on() and not T.db.ui.testMode, "plain Ziggu is not")
      _charName, UnitFullName = realName, realFull
      return table.concat(fails, "; ")
    ''')
    assert r == "", r
    print("test mode: only Ziggu Trip, no password")
