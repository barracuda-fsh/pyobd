import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class CustomListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(
            self, parent, id, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0
    ):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        ListCtrlAutoWidthMixin.__init__(self)

# class MyPanel(wx.Panel):
#     def __init__(self, parent):
#         super(MyPanel, self).__init__(parent)
#
#         self.label = wx.StaticText(self, label="What Programming Language You Like?", pos=(50, 30))
#
#         languages = ['Java', 'C++', 'C#', 'Python', 'Erlang', 'PHP', 'Ruby']
#         self.combobox = wx.ComboBox(self, choices=languages, pos=(50, 50))
#
#         self.label2 = wx.StaticText(self, label="", pos=(50, 80))
#
#         self.Bind(wx.EVT_COMBOBOX, self.OnCombo)
#
#     def OnCombo(self, event):
#         self.label2.SetLabel("You Like " + self.combobox.GetValue())
