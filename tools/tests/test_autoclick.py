# 1.7.0 auto-clicker guard: one key pressed at a machine-steady rhythm for 150 presses in a row stops
# counting for 10 seconds (1.7.1: a pause, never until a reload); fast human mashing (uneven gaps, several keys) is never touched.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      T.AutoclickTest.reset()
      -- a bot: the same key every 0.100 s (with the client's frame rounding of up to 16 ms)
      local t0 = T.db.taps
      for i = 1, 240 do _clock = _clock + 0.1 + (i % 2) * 0.0167 - 0.008; T:OnKey("F") end
      local botTaps = T.db.taps - t0
      ck(botTaps <= 160, "a steady auto-clicker stops counting after about 150 presses: " .. botTaps)
      -- (1.7.1) only a pause: 10 seconds later the same steady key counts again (never stuck until a reload)
      local tp = T.db.taps
      for i = 1, 60 do _clock = _clock + 0.1 + (i % 2) * 0.0167 - 0.008; T:OnKey("F") end
      ck(T.db.taps - tp >= 40, "after the 10 second pause it counts again: " .. (T.db.taps - tp))
      -- the rhythm breaks: counting again
      _clock = _clock + 2
      local t1 = T.db.taps
      for i = 1, 20 do _clock = _clock + 0.1; T:OnKey("F") end
      ck(T.db.taps - t1 >= 19, "after a pause the key counts again")
      -- a fast human: one key, 9 presses a second for two minutes, gaps a little uneven
      T.AutoclickTest.reset()
      local t2 = T.db.taps
      for i = 1, 1080 do _clock = _clock + 0.111 + (math.random() - 0.5) * 0.08; T:OnKey("1") end
      ck(T.db.taps - t2 >= 1050, "fast human mashing is never blocked: " .. (T.db.taps - t2))
      -- a fast human on several keys
      T.AutoclickTest.reset()
      local keys = { "1", "2", "3", "Q", "E" }
      local t3 = T.db.taps
      for i = 1, 1000 do _clock = _clock + 0.1; T:OnKey(keys[i % 5 + 1]) end
      ck(T.db.taps - t3 == 1000, "several keys at a steady pace count every time")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("autoclick: " + r)
    print("auto-clicker guard section (a machine-steady key stops counting, a pause brings it back, fast human mashing and many keys always count): all checks passed")
