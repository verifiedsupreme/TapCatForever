# 1.6.7: Settings > Show party cats. Off: the row of party members' cats beside yours is hidden; the tap
# bonus, the party list and everything else keep working. On by default, and back on shows the row again.

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      ck(T.db.ui.partyCats == true, "on by default")
      T.db.ui.testMode = true; T:PartyTestInject(2); T.db.ui.testMode = false   -- two stand-in party cats
      T.PartyRefresh()
      local mult = T:PartyTapMult()
      ck(T:PartyCount() == 2 and mult > 1, "two party cats, a bonus: " .. mult)
      T:ToggleWindow()
      local win = T.window
      win:SelectTab(win.TAB_SETTINGS)
      local cb = win.partyCatsCheck
      ck(cb and cb:IsShown() and cb:GetChecked(), "the Show party cats box, ticked")
      cb:SetChecked(false); cb.scripts.OnClick(cb)
      ck(T.db.ui.partyCats == false, "turned off and saved")
      ck(T:PartyTapMult() == mult and T:PartyCount() == 2, "the bonus stays")
      local rowFrame = T.PartyRowFrame and T.PartyRowFrame()
      ck(rowFrame == nil or not rowFrame:IsShown(), "the row is hidden")
      cb:SetChecked(true); cb.scripts.OnClick(cb)
      rowFrame = T.PartyRowFrame and T.PartyRowFrame()
      ck(T.db.ui.partyCats == true and rowFrame and rowFrame:IsShown(), "back on: the row shows again")
      local help = win.settingsInfo.help:GetText()
      ck(not help:find("per character", 1, true), "the outdated per-character line is gone: " .. help)
      -- test mode (1.6.7): +1,000 taps, and no fake party cat buttons any more
      local t0 = T.db.taps
      T.db.ui.testMode = true
      T:TestCheat("taps")
      ck(T.db.taps == t0 + 1000, "test mode: +1,000 taps")
      ck(T:SharedTaps() == t0 and T:LeaderboardOwnEntry().t == t0, "test taps stay yours: other players (leaderboard, party) don't get them")
      T.db.ui.testMode = false
      T:TestCheat("taps")
      ck(T.db.taps == t0 + 1000, "only in test mode")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("party cats setting: " + r)
    print("party cats setting section (Show party cats off hides the row only, the bonus stays, back on shows it): all checks passed")
