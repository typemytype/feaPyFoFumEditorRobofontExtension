import AppKit
from defconAppKit.controls.glyphSequenceEditText import GlyphSequenceEditText
from defconAppKit.controls.openTypeControlsView import OpenTypeControlsView
from defconAppKit.controls.glyphLineView import GlyphLineView

from vanilla import *


class FeaturePreviewerGlyphSequenceEditText(GlyphSequenceEditText):

    def __init__(self, posSize, callback=None, sizeStyle="regular"):
        super(self.__class__, self).__init__(posSize, None, callback, sizeStyle)

    def setFont(self, font):
        self._font = font

    def get(self):
        if self._font is None:
            return []
        return super(self.__class__, self).get()


class FeaturePreviewer(Group):

    def __init__(self, posSize):
        super(self.__class__, self).__init__(posSize)

        self._font = None
        self._compiledFont = None

        topHeight = 40
        left = 160
        self.glyphLineInputPosSize = (10, 10, -10, 22)
        self.glyphLineInputPosSizeWithUpdate = (10, 10, -85, 22)
        # input
        self.glyphLineInput = FeaturePreviewerGlyphSequenceEditText(self.glyphLineInputPosSizeWithUpdate, callback=self.glyphLineViewInputCallback)
        # tab container
        self.previewTabs = Tabs((left, topHeight, -0, -0), ["Preview", "Records"], showTabs=False)
        # line view
        self.previewTabs[0].lineView = GlyphLineView((0, 0, -0, -0), showPointSizePlacard=True)
        # records
        columnDescriptions = [
            dict(title="Name", width=100),
            dict(title="XP", width=50),
            dict(title="YP", width=50),
            dict(title="XA", width=50),
            dict(title="YA", width=50),
            dict(title="Alternates", width=100)
        ]
        self.previewTabs[1].recordsList = List((0, 0, -0, -0),
                                [],
                                columnDescriptions=columnDescriptions,
                                showColumnTitles=True,
                                drawVerticalLines=True,
                                drawFocusRing=False)
        # controls
        self.glyphLineControls = OpenTypeControlsView((0, topHeight, left+1, 0),
                                self.glyphLineViewControlsCallback)

    def setFont(self, font):
        self._font = font
        self.glyphLineInput.setFont(font)
        self.updateGlyphLineView()

    def setCompiledFont(self, compiledFont):
        self._compiledFont = compiledFont
        self.updateGlyphLineViewViewControls()
        self.updateGlyphLineView()

    def glyphLineViewInputCallback(self, sender):
        self.updateGlyphLineView()

    def glyphLineViewControlsCallback(self, sender):
        self.updateGlyphLineView()

    def updateGlyphLineViewViewControls(self):
        if self._compiledFont is not None:
            existingStates = self.glyphLineControls.get()
            # GSUB
            if self._compiledFont.gsub is not None:
                for tag in self._compiledFont.gsub.getFeatureList():
                    state = existingStates["gsub"].get(tag, False)
                    self._compiledFont.gsub.setFeatureState(tag, state)
            # GPOS
            if self._compiledFont.gpos is not None:
                for tag in self._compiledFont.gpos.getFeatureList():
                    state = existingStates["gpos"].get(tag, False)
                    self._compiledFont.gpos.setFeatureState(tag, state)
        self.glyphLineControls.setFont(self._compiledFont)

    def updateGlyphLineView(self):
        glyphLineView = self.previewTabs[0].lineView
        glyphRecordsList = self.previewTabs[1].recordsList
        # get the settings
        settings = self.glyphLineControls.get()
        # set the display mode
        mode = settings["mode"]
        if mode == "preview":
            self.previewTabs.set(0)
        else:
            self.previewTabs.set(1)
        # set the direction
        glyphLineView.setRightToLeft(settings["rightToLeft"])
        # get the typed glyphs
        glyphs = self.glyphLineInput.get()
        # set into the view
        case = settings["case"]
        if self._compiledFont is None:
            # convert case
            if case != "unchanged":
                # the case converter expects a slightly
                # more strict set of mappings than the
                # ones provided in font.unicodeData.
                # so, make them.
                cmap = {}
                reversedCMAP = {}
                for uniValue, glyphName in self._font.unicodeData.items():
                    cmap[uniValue] = glyphName[0]
                    reversedCMAP[glyphName[0]] = [uniValue]
                # transform to glyph names
                glyphNames = [glyph.name for glyph in glyphs]
                # convert
                glyphNames = convertCase(case, glyphNames, cmap, reversedCMAP, None, ".notdef")
                # back to glyphs
                glyphs = [self._font[glyphName] for glyphName in glyphNames if glyphName in self._font]
            # set the glyphs
            glyphLineView.set(glyphs)
            records = [dict(Name=glyph.name, XP=0, YP=0, XA=0, YA=0, Alternates="") for glyph in glyphs]
            glyphRecordsList.set(records)
        else:
            # get the settings
            script = settings["script"]
            language = settings["language"]
            rightToLeft = settings["rightToLeft"]
            case = settings["case"]
            for tag, state in settings["gsub"].items():
                self._compiledFont.gsub.setFeatureState(tag, state)
            for tag, state in settings["gpos"].items():
                self._compiledFont.gpos.setFeatureState(tag, state)
            # convert to glyph names
            glyphNames = [glyph.name for glyph in glyphs if not glyph.template]
            # process
            glyphRecords = self._compiledFont.process(glyphNames, script=script, langSys=language, rightToLeft=rightToLeft, case=case)
            # set the UFO's glyphs into the records
            finalRecords = []
            for glyphRecord in glyphRecords:
                if glyphRecord.glyphName not in self._font:
                    continue
                glyphRecord.glyph = self._font[glyphRecord.glyphName]
                finalRecords.append(glyphRecord)
            # set the records
            glyphLineView.set(finalRecords)
            records = [dict(Name=record.glyph.name, XP=record.xPlacement, YP=record.yPlacement, XA=record.xAdvance, YA=record.yAdvance, Alternates=", ".join(record.alternates)) for record in finalRecords]
            glyphRecordsList.set(records)


class SettingsToolbarButton(AppKit.NSButton):

    def __new__(cls, *arg, **kwargs):
        self = cls.alloc().initWithFrame_(((0, 0), (32, 32)))
        return self

    def __init__(self, items):
        self._callbackMap = {}
        self.setBordered_(False)
        self.setTitle_("")
        self._makeMenu(items)
        self.setImage_(AppKit.NSImage.imageNamed_("prefToolbarMisc"))

    def _makeMenu(self, items):
        self.popUpCell = AppKit.NSPopUpButtonCell.alloc().initTextCell_pullsDown_("", True)
        self.popUpCell.setUsesItemFromMenu_(False)
        self.popUpCell.addItemWithTitle_("Settings...")

        menu = self.popUpCell.menu()

        for title, state, callback in items:
            menuItem = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, "action:", "")
            menuItem.setTarget_(self)
            menuItem.setState_(state)
            menu.addItem_(menuItem)
            self._callbackMap[title] = callback

    def action_(self, sender):
        sender.setState_(not sender.state())
        self._callbackMap[sender.title()](sender)

    def mouseDown_(self, event):
        self.popUpCell.performClickWithFrame_inView_(self.bounds(), self)
