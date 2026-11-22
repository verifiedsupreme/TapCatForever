-- TapCatForever: a way for players to send feedback. Addons can't reach the internet, so this
-- shows a copy-ready link (GitHub issues with bug/suggestion forms) and a
-- short "about my game" block to paste into the report.
local ADDON, TCF = ...

TCF.FEEDBACK_LINKS = {
  { "Report a bug or suggest an idea (GitHub)", "https://github.com/verifiedsupreme/TapCatForever/issues/new/choose" },
}

-- facts that help track a bug down
function TCF:FeedbackInfo()
  local db = self.db
  local version = (C_AddOns and C_AddOns.GetAddOnMetadata and C_AddOns.GetAddOnMetadata(ADDON, "Version")) or "?"
  local build, _, _, iface = "?", nil, nil, "?"
  if GetBuildInfo then build, _, _, iface = GetBuildInfo() end
  local cd = db and self:CD()
  local adv = cd and cd.adv
  local parts = {
    "TapCatForever " .. tostring(version),
    "WoW " .. tostring(build) .. " (" .. tostring(iface) .. ")",
    (GetLocale and GetLocale() or "?"),
  }
  if db then
    parts[#parts + 1] = string.format("%s cat level %d", tostring(db.class), cd and cd.level or 0)
    if adv then parts[#parts + 1] = string.format("Adventure zone %d stage %d", adv.tier or 0, adv.stage or 0) end
    parts[#parts + 1] = string.format("scale %.2f, text %s", db.ui.scale or 1, db.ui.textAbove and "above" or "below")
  end
  return table.concat(parts, " | ")
end

local function copyBox(parent, w)
  local e = CreateFrame("EditBox", nil, parent, "InputBoxTemplate")
  e:SetSize(w, 22); e:SetAutoFocus(false)
  e:SetScript("OnEscapePressed", function(s) s:ClearFocus() end)
  -- keep the text as written (players only copy it)
  e:SetScript("OnTextChanged", function(s, user) if user and s.fixed then s:SetText(s.fixed); s:HighlightText() end end)
  e:SetScript("OnEditFocusGained", function(s) s:HighlightText() end)
  e:SetScript("OnMouseUp", function(s) s:SetFocus(); s:HighlightText() end)
  return e
end

function TCF:ShowFeedback()
  local f = self.feedback
  if not f then
    local U = TCF.UI
    f = CreateFrame("Frame", "TapCatForeverFeedback", UIParent, U.BT)
    f:SetSize(520, 250); f:SetPoint("CENTER")
    f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
    f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
    if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
    tinsert(UISpecialFrames, "TapCatForeverFeedback")
    local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
    local title = U.Text(f, "GameFontNormalLarge", "Send feedback"); title:SetPoint("TOP", 0, -18)
    local intro = U.Text(f, "GameFontHighlight", "Found a bug or have an idea? I read everything. Click the link box, press Ctrl+C to copy it, then paste it into your browser.")
    intro:SetPoint("TOP", 0, -44); intro:SetWidth(470)
    local y = -92
    f.boxes = {}
    for _, l in ipairs(TCF.FEEDBACK_LINKS) do
      local label = U.Text(f, "GameFontNormal", l[1], "LEFT"); label:SetPoint("TOPLEFT", 26, y)
      local box = copyBox(f, 460); box:SetPoint("TOPLEFT", 30, y - 16)
      box.fixed = l[2]; box:SetText(l[2]); box:SetCursorPosition(0)
      y = y - 50
    end
    local infoLabel = U.Text(f, "GameFontNormal", "About your game (paste this into bug reports)", "LEFT"); infoLabel:SetPoint("TOPLEFT", 26, y)
    f.info = copyBox(f, 460); f.info:SetPoint("TOPLEFT", 30, y - 16)
    local tip = U.Text(f, "GameFontDisableSmall", "Seeing an error? Type /console scriptErrors 1 and include the error text.")
    tip:SetPoint("BOTTOM", 0, 16)
    self.feedback = f
  end
  local info = self:FeedbackInfo()
  f.info.fixed = info; f.info:SetText(info); f.info:SetCursorPosition(0)
  f:Show()
end

-- /tcf feedback (wraps the slash handler when this file loads, like Compendium.lua)
do
  local orig = SlashCmdList and SlashCmdList.TAPCATFOREVER
  if orig and not TCF.feedbackSlash then
    TCF.feedbackSlash = true
    SlashCmdList.TAPCATFOREVER = function(msg, ...)
      if (msg or ""):lower():match("^%s*feedback") then return TCF:ShowFeedback() end
      return orig(msg, ...)
    end
  end
end
