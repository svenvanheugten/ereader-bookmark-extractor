import wx
import sys
from common import extract


config = wx.Config('ereader-bookmark-extractor')


class EbookBookmarkExtractorFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title='Ebook Bookmark Extractor', size=(800, 600),
                         style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.ereader_dir = wx.DirPickerCtrl(self, path=config.Read('ereader_dir'))
        self.output_dir = wx.DirPickerCtrl(self, path=config.Read('output_dir'))
        self.log = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.button = wx.Button(self, label='Run')
        self.button.Bind(wx.EVT_BUTTON, self.OnClickRun)
        sizer.Add(wx.StaticText(self, label='E-reader directory'), flag=wx.EXPAND)
        sizer.Add(self.ereader_dir, flag=wx.EXPAND)
        sizer.Add(wx.StaticText(self, label='Output directory'), flag=wx.EXPAND)
        sizer.Add(self.output_dir, flag=wx.EXPAND)
        sizer.Add(self.button, flag=wx.EXPAND)
        sizer.Add(self.log, flag=wx.EXPAND, proportion=1)
        sys.stdout = self.log
        sys.stderr = self.log
        self.SetSizer(sizer)

    def OnClickRun(self, event):
        ereader_dir = self.ereader_dir.GetPath()
        output_dir = self.output_dir.GetPath()
        config.Write('ereader_dir', ereader_dir)
        config.Write('output_dir', output_dir)
        extract(ereader_dir, output_dir)


if __name__ == '__main__':
    app = wx.App()
    frame = EbookBookmarkExtractorFrame()
    frame.Show()
    frame.Centre()
    app.MainLoop()
