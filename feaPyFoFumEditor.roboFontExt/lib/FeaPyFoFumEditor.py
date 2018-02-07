import AppKit

from mojo.events import addObserver, removeObserver

from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController

from feaPyFoFum import compileFeatures

from lib.features.featureEditor import DoodleFeatureTextEditor

from feaPyFoFumLexer import FeaPyFoFumLexer, languagesIDEBehavior
from compositorUFOFont import CompositorUFOFont

import feaPyFoFumUI
try:
    import importlib
    importlib.reload(feaPyFoFumUI)
except:
    pass

from feaPyFoFumUI import FeaturePreviewer, SettingsToolbarButton


import mojo.roboFont

if mojo.roboFont.version < "3.0":
    SplitView = SplitView2


class FeaPyFoFumEditor(BaseWindowController):

    def __init__(self, fea=""):
        if fea is None:
            fea = "hello"
        self._font = None
        self._compositorFont = None

        self._liveFeaPyFoFumWriting = True

        self.feaPyEditor = DoodleFeatureTextEditor((0, 0, -0, -0), callback=self.feaPyEditorCallback)
        self.feaPyEditor.setLexer(FeaPyFoFumLexer())
        self.feaPyEditor.setLanguagesIDEBehavior(languagesIDEBehavior)
        self.feaPyEditor.set(fea)

        self.feaText = DoodleFeatureTextEditor((0, 0, -0, -0), readOnly=True)
        self.feaText.setLexer(FeaPyFoFumLexer())

        self.previewer = FeaturePreviewer((0, 0, -0, 1000))
        self.previewer.glyphLineUpdateButton = Button((-75, 11, 65, 20), "Update", callback=self.glyphLineUpdateButtonCallback)

        self.w = Window((700, 600), minSize=(400, 400))

        toolbarItems = [
            dict(
                itemIdentifier="compile",
                label="Compile FeaPy",
                imageNamed="toolbarRun",
                callback=self.toolbarCompile,
            ),
            dict(
                itemIdentifier="comment",
                label="Comment",
                imageNamed="toolbarComment",
                callback=self.toolbarComment,
            ),
            dict(
                itemIdentifier="uncomment",
                label="Uncomment",
                imageNamed="toolbarUncomment",
                callback=self.toolbarUncomment,
            ),
            dict(
                itemIdentifier="indent",
                label="Indent",
                imageNamed="toolbarIndent",
                callback=self.toolbarIndent,
            ),
            dict(
                itemIdentifier="dedent",
                label="Dedent",
                imageNamed="toolbarDedent",
                callback=self.toolbarDedent,
            ),
            dict(itemIdentifier=AppKit.NSToolbarSpaceItemIdentifier),
            dict(
                itemIdentifier="FeaPytify",
                label="FeaPytify",
                imageNamed="toolbarComment",
                callback=self.toolbarFeaPytify,
            ),
            dict(itemIdentifier=AppKit.NSToolbarSpaceItemIdentifier),
            dict(
                itemIdentifier="save",
                label="Save In Font",
                imageNamed="toolbarScriptSave",
                callback=self.toolbarSaveInFont,
            ),
            dict(itemIdentifier=AppKit.NSToolbarFlexibleSpaceItemIdentifier),
            dict(
                itemIdentifier="settings",
                label="Settings...",
                view=SettingsToolbarButton([
                    ("Live", True, self.toolbarSettingsLive),
                ]),
            ),
        ]

        self.w.addToolbar(toolbarIdentifier="FeaPyTesterToolBar", toolbarItems=toolbarItems, addStandardItems=False)

        paneDescriptors = [
            dict(view=self.feaPyEditor, identifier="feaPyEditor", minSize=100, canCollapse=False),
            dict(view=self.feaText, identifier="feaText", minSize=100, canCollapse=False),
        ]
        self.editorSplit = SplitView((0, 0, -0, -0), paneDescriptors, dividerStyle="thin")

        paneDescriptors = [
            dict(view=self.editorSplit, identifier="editor", minSize=100, canCollapse=False),
            dict(view=self.previewer, identifier="previewer", minSize=100, canCollapse=False),
        ]
        self.w.splitView = SplitView((0, 0, -0, -0), paneDescriptors, dividerStyle="thin", isVertical=False)

        # observer current document changed
        addObserver(self, "fontBecameCurrent", "fontBecameCurrent")
        addObserver(self, "fontResignCurrent", "fontResignCurrent")

        self.w.setDefaultButton(self.previewer.glyphLineUpdateButton)
        self._subscribeFont(CurrentFont())
        self.compile()
        self.setUpBaseWindowBehavior()
        self.w.open()

    def compile(self):
        if self._font is None:
            self.feaText.set("")
            return
        try:
            fea = compileFeatures(self.feaPyEditor.get(), self._font, compileReferencedFiles=True)
        except Exception:
            import traceback
            print(traceback.format_exc(5))
            fea = ""
        self.feaText.set(fea)

    def compileFont(self):
        self.compile()
        compositorFont = self.getCompositorFont(self.feaText.get())
        if compositorFont:
            self.previewer.setCompiledFont(compositorFont)

    def getCompositorFont(self, fea=None):
        if self._compositorFont is None and self._font:
            self._compositorFont = CompositorUFOFont(self._font)

        if fea and self._compositorFont:
            self._compositorFont.addFeatures(fea)
        return self._compositorFont

    def _unsubscribeFont(self):
        if self._font:
            self._font.removeObserver(self, "Font.Changed")
        self._font = None
        self.w.setTitle("")

    def _subscribeFont(self, font):
        self._unsubscribeFont()
        self._font = font
        self._compositorFont = None
        if self._font:
            self._font.addObserver(self, "fontChanged", "Font.Changed")
            self.previewer.setFont(self._font.naked())
            self.compileFont()
            self.w.setTitle("%s - %s" % (self._font.info.familyName, self._font.info.styleName))
        else:
            self.previewer.setFont(None)
            self.w.setTitle("")

    def saveInFont(self):
        if self._font:
            self._font.features.text = self.feaPyEditor.get()
            self._font.lib["com.typesupply.feaPyFoFum.compileFeatures"] = True

    # toolbar

    def toolbarCompile(self, sender):
        self.compile()

    def toolbarComment(self, sender):
        self.feaPyEditor.comment()

    def toolbarUncomment(self, sender):
        self.feaPyEditor.uncomment()

    def toolbarIndent(self, sender):
        self.feaPyEditor.indent()

    def toolbarDedent(self, sender):
        self.feaPyEditor.dedent()

    def toolbarFeaPytify(self, sender):
        self.feaPyEditor.comment()

        def feaPyTiFyFilter(lines):
            indent = 0
            if lines:
                line = lines[0]
                white = line.split("#")[0]
                indent = len(white)

                lastLine = lines[-1]
                if lastLine[-1] != "\n":
                    lines[-1] = lastLine + "\n"

            return ["%s# >>>\n" % (" " * indent)] + lines + ["%s# <<<\n" % (" " * indent)]

        self.feaPyEditor.getNSTextView()._filterLines(feaPyTiFyFilter)

    def toolbarSaveInFont(self, sender):
        self.saveInFont()

    def toolbarSettingsLive(self, sender):
        self._liveFeaPyFoFumWriting = sender.state()

    # notifications

    def fontChanged(self, notification):
        self._ttFont = None
        self.previewer.glyphLineUpdateButton.enable(True)

    def fontBecameCurrent(self, notification):
        self._subscribeFont(notification["font"])

    def fontResignCurrent(self, notification):
        self._unsubscribeFont()

    # ui notifications

    def glyphLineUpdateButtonCallback(self, sender):
        self.compileFont()
        self.previewer.glyphLineUpdateButton.enable(False)

    def feaPyEditorCallback(self, sender):
        if self._liveFeaPyFoFumWriting:
            self.compile()
            if not self.previewer.glyphLineUpdateButton.getNSButton().isEnabled():
                self.previewer.glyphLineUpdateButton.enable(True)

    def windowCloseCallback(self, sender):
        removeObserver(self, "fontBecameCurrent")
        removeObserver(self, "fontResignCurrent")
        self._unsubscribeFont()
        super(self.__class__, self).windowCloseCallback(sender)


if __name__ == "__main__":
    fea = """languagesystem DFLT dflt;
languagesystem latn dflt;

# >>>
# caseWriter = writer.feature("case")
# for name in font.glyphOrder:
#     if name.endswith(".cap"):
#         caseWriter.substitution(name.split(".")[0], name)
# print writer.write()
# <<<

feature liga {
    # >>>
    # for name in font.glyphOrder:
    #     if "_" in name:
    #         writer.substitution(name.replace("_", " "), name)
    # print writer.write()
    # <<<
} liga;


#include(Blah-kern.fea);"""

    FeaPyFoFumEditor()
