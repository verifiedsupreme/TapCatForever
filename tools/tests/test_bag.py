# 1.7.0 Profession Bag: every material by tab, what it's for, selling a stack, and bags bought with
# TapCoins. Every kind fits; goods past the stack size are sold for Trade Gold; a pile a cat already had
# above the size is kept until it shrinks. The TapCoin icon is orange now.
import os

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      T:SetClass("MAGE")
      local s = T:ProfState()
      s.gold = 0
      s.mats.linen, s.mats.wool, s.mats.essundeath, s.mats.peacebloom, s.mats.b_linen, s.mats.primalmooncloth = 701620, 15000, 2, 30, 4, 1
      s.bagKeep = nil
      T:MatBagTrim()
      ck(T:MatStackCap() == 20000 and T:MatBag().name == "Linen Bag", "a Linen Bag to start")
      ck(s.mats.linen == 701620, "a big pile from before is kept")
      s.mats.linen = s.mats.linen + 100
      T:MatBagTrim()
      ck(s.mats.linen == 701620 and s.gold > 0, "more than the kept pile is sold for Trade Gold")
      s.mats.linen = 30000
      T:MatBagTrim()
      ck(s.bagKeep.linen == 30000, "the kept pile shrinks with use")
      s.mats.linen = 10000
      T:MatBagTrim()
      ck(s.bagKeep.linen == nil, "and is forgotten once it fits")
      s.mats.wool = 25000
      T:MatBagTrim()
      ck(s.mats.wool == 20000, "a stack can't grow past the bag")
      -- tabs
      local function has(tab, key) for _, k in ipairs(T:BagList(tab)) do if k == key then return true end end end
      ck(has("gathered", "linen") and has("rare", "essundeath") and has("daily", "primalmooncloth") and has("herbs", "peacebloom") and has("bandages", "b_linen"), "materials by tab")
      ck(#T:MatUses("runecloth") > 0 and #T:MatUses("boot") == 0, "what a material is for")
      -- buying a bigger bag
      T.db.coins = 400
      ck(not T:BuyMatBag(), "the Wool Bag costs 500")
      T.db.coins = 600
      ck(T:BuyMatBag() and T:MatStackCap() == 50000 and T.db.coins == 100, "Wool Bag: stacks of 50,000")
      s.mats.wool = 45000; T:MatBagTrim()
      ck(s.mats.wool == 45000, "a bigger bag holds more")
      T.db.matBag = #T.MAT_BAGS
      s.mats.wool = 1e12; T:MatBagTrim()
      ck(s.mats.wool == 1e12, "the Bottomless Bag holds any amount")
      -- selling a stack
      local g = s.gold
      ck(T:SellMatStack("peacebloom") > 0 and (s.mats.peacebloom or 0) == 0 and s.gold > g, "a stack sold")
      -- the window: the Bag button opens it
      T:ToggleWindow(); local win = T.window
      win:SelectTab(win.TAB_PROFESSIONS)
      win.profBag:Show(); win:Refresh()
      ck(win.profBag:IsShown(), "the bag panel shows")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("bag: " + r)
    from PIL import Image
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    im = Image.open(os.path.join(root, "Art", "ui_coin.tga")).convert("RGB")
    cr, cg, cb = im.getpixel((im.width // 2, im.height // 4))
    if not (cr > 200 and cg < 175 and cb < 90):
        raise AssertionError("bag: the TapCoin is orange: %r" % ((cr, cg, cb),))
    print("profession bag section (every material by tab, what it's for, old piles kept, extra sold for Trade Gold, bags with TapCoins up to Bottomless, selling a stack, orange TapCoin): all checks passed")
