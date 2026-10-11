"""About page and shared program credits."""

import wx
import webbrowser


ABOUT_DIALOG_TEXT = """PyOBD is an automotive OBD-II diagnostic application maintained by FareBrothers, LLC.

Operating since 2023, FareBrothers, LLC develops iOS and Android applications and maintains automotive software projects including pyOBD, DodgeOBD, and NissanOBD. Through Great Lakes IT Services, the company also provides website hosting and game server hosting.

(C) 2025 FareBrothers, LLC
(C) 2021 Jure Poljsak
(C) 2008-2009 SeCons Ltd.
(C) 2004 Charles Donour Sizemore

https://farebros.com
https://farebros.com/divisions.php
https://github.com/alexfare/pyobd

PyOBD is free software distributed under version 2 of the GNU General Public License.
It comes without any warranty. See COPYING for the full license text.
"""


def build_about_page(notebook):
    panel = wx.ScrolledWindow(notebook, style=wx.VSCROLL)
    panel.SetScrollRate(10, 10)
    panel.SetMinSize((640, 420))
    root = wx.BoxSizer(wx.VERTICAL)

    def add_link(label, url, bottom=8):
        link = wx.StaticText(panel, label=label)
        link.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HOTLIGHT))
        link_font = link.GetFont()
        link_font.SetUnderlined(True)
        link.SetFont(link_font)
        link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link.Bind(wx.EVT_LEFT_UP, lambda _event, target=url: webbrowser.open(target))
        root.Add(link, 0, wx.BOTTOM, bottom)

    title = wx.StaticText(panel, label="FareBrothers, LLC")
    title.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

    intro = wx.StaticText(
        panel,
        label=(
            "Operating since 2023, FareBrothers, LLC develops iOS and Android applications "
            "and maintains automotive software projects including pyOBD, DodgeOBD, and NissanOBD."
        ),
    )
    intro.Wrap(760)

    company_title = wx.StaticText(panel, label="Great Lakes IT Services")
    company_title.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    company = wx.StaticText(
        panel,
        label=(
            "Through Great Lakes IT Services, FareBrothers, LLC also provides website hosting "
            "and game server hosting."
        ),
    )
    company.Wrap(760)

    credits = wx.StaticText(
        panel,
        label=(
            "Credits\n"
            "© 2025 FareBrothers, LLC\n"
            "© 2021 Jure Poljsak\n"
            "© 2008–2009 SeCons Ltd.\n"
            "© 2004 Charles Donour Sizemore\n\n"
            "Licensed under GPL-2.0."
        ),
    )

    root.Add(title, 0, wx.BOTTOM, 14)
    root.Add(intro, 0, wx.BOTTOM, 20)
    root.Add(company_title, 0, wx.BOTTOM, 8)
    root.Add(company, 0, wx.BOTTOM, 12)
    more_title = wx.StaticText(panel, label="More from us")
    more_title.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    root.Add(more_title, 0, wx.TOP | wx.BOTTOM, 8)
    add_link("Farebros.com", "https://farebros.com")
    add_link("FareBrothers Divisions", "https://farebros.com/divisions.php")
    add_link(
        "Fare Brothers on the Apple App Store",
        "https://apps.apple.com/us/developer/fare-brothers/id1869971574",
    )
    add_link(
        "FareBrothers apps on Google Play",
        "https://play.google.com/store/apps/developer?id=FareBrothers",
        bottom=20,
    )
    root.Add(credits)
    panel.SetSizer(root)
    root.SetMinSize((800, 560))
    panel.SetVirtualSize(root.GetMinSize())
    notebook.AddPage(panel, "About")
    return panel
