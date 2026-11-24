# 1.6.8 Tapping and petting faces: the cat's face climbs through ten tapping faces the longer and faster
# you tap (heat from a long run of taps AND the speed right now, the lower one wins, one step at a time),
# cools down after a pause, and shows ten petting faces as a petting run heads toward Happy Purrs
# (the last one when the purring starts). The setting turns both off. Every face has its art.
import os

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      T.TapFaceTest.reset(); T.PurrTest.reset()
      T.db.ui.mouse = true
      local cat = T.cat
      local function tapFor(sec, tps)
        local n = math.floor(sec * tps + 0.5)
        local maxLv = 0
        for i = 1, n do
          _clock = _clock + 1 / tps
          T:Tap(i % 2 == 0 and "L" or "R")
          local lv = T:TapFaceLevel(_clock)
          if lv > maxLv then maxLv = lv end
        end
        return maxLv
      end
      local function idle(sec) for i = 1, sec * 10 do _clock = _clock + 0.1; T:TapFaceLevel(_clock) end end
      -- a quick burst never reaches the top faces
      local burst = tapFor(3, 12)
      ck(burst <= 3, "3 seconds of fast tapping: at most face 3 (" .. burst .. ")")
      idle(60)
      ck(T:TapFaceLevel(_clock) == 0, "after a minute's pause: the calm face again")
      -- a long run of fast tapping reaches Legendary, and takes a lot of taps
      T.TapFaceTest.reset()
      local reached
      for k = 1, 200 do
        tapFor(1, 10)
        if T:TapFaceLevel(_clock) >= 10 then reached = k * 10; break end
      end
      ck(reached and reached >= 700, "Legendary after a long run of fast taps (" .. tostring(reached) .. " taps)")
      -- the cat on screen shows it
      cat:OnUpdate(0.05)
      ck(cat.faceKind == "tap10", "the cat shows face_tap10: " .. tostring(cat.faceKind))
      -- slowing down brings it down step by step (the speed decides)
      local seen = {}
      for i = 1, 40 do _clock = _clock + 1 / 4; T:Tap("L"); seen[#seen + 1] = T:TapFaceLevel(_clock) end
      ck(seen[#seen] <= 6 and seen[#seen] >= 4, "4 taps a second: face 4 to 6 (" .. seen[#seen] .. ")")
      local jumps = true
      for i = 2, #seen do if math.abs(seen[i] - seen[i - 1]) > 1 then jumps = false end end
      ck(jumps, "one step at a time")
      -- slow tapping for a long time never climbs high (needs speed)
      T.TapFaceTest.reset()
      local slow = tapFor(300, 2.5)
      ck(slow <= 4, "slow steady tapping for 5 minutes: face 4 at most (" .. slow .. ")")
      -- a short pause keeps some heat: getting back up is quicker than from nothing
      T.TapFaceTest.reset()
      tapFor(60, 10)
      idle(3)
      local heat3 = select(2, T:TapFaceLevel(_clock))
      ck(heat3 > 300, "a 3 second pause keeps most of the heat (" .. math.floor(heat3) .. ")")
      idle(120)
      ck(select(2, T:TapFaceLevel(_clock)) == 0, "two minutes later it has cooled")
      -- petting faces: they follow the run toward Happy Purrs
      T.TapFaceTest.reset()
      for i = 1, 34 do _clock = _clock + 0.3; T:PurrPet() end
      local p34 = T:PurrFaceLevel(_clock)
      ck(p34 >= 3 and p34 <= 4, "34 pets: face 3 or 4 (" .. p34 .. ")")
      cat:OnUpdate(0.05)
      ck(cat.faceKind == "pet" .. p34, "petting shows the petting face: " .. tostring(cat.faceKind))
      for i = 1, 65 do _clock = _clock + 0.3; T:PurrPet() end
      ck(T:PurrFaceLevel(_clock) == 9, "99 pets: face 9")
      _clock = _clock + 0.3; T:PurrPet()
      ck(T:PurrActive() and T:PurrFaceLevel(_clock) == 10, "Happy Purrs: Pure love")
      _clock = _clock + 3.5
      ck(T:PurrFaceLevel(_clock) == 0, "a moment later, and no more petting: back to normal")
      -- the setting
      T.db.ui.tapFaces = false
      T.TapFaceTest.reset()
      tapFor(120, 10)
      cat:OnUpdate(0.05)
      ck(not tostring(cat.faceKind):find("tap", 1, true), "faces off: no tapping face (" .. tostring(cat.faceKind) .. ")")
      T.db.ui.tapFaces = true
      -- art for every face
      for i = 1, 10 do
        ck(T.VEC["cat:face_tap" .. i] and T.VEC["cat:face_pet" .. i], "art for face " .. i)
      end
      ck(#T.TAP_FACE_NAMES == 10 and #T.PET_FACE_NAMES == 10, "names")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("faces: " + r)
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    missing = [n for n in ["c_face_tap%d" % i for i in range(1, 11)] + ["c_face_pet%d" % i for i in range(1, 11)]
               if not os.path.exists(os.path.join(root, "Art", "v", n + ".tga"))]
    if missing: raise AssertionError("faces: missing art %r" % missing)
    print("tapping and petting faces section (a quick burst stays low, Legendary takes hundreds of fast taps, the speed caps it, one step at a time, "
          "slow tapping stays low, a pause cools it, petting faces follow the run to Happy Purrs, the setting, 20 faces drawn): all checks passed")
