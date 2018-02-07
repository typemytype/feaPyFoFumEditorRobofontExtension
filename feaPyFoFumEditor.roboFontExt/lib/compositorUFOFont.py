import tempfile
import os

import compositor
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeatures


class CompositorUFOFont(compositor.Font):

    def __init__(self, ufo):
        self.ufo = ufo
        otf = TTFont()
        otf.setGlyphOrder(ufo.glyphOrder)
        super(CompositorUFOFont, self).__init__(otf)

    def addFeatures(self, fea, clear=True):
        feaPath = tempfile.mktemp()
        f = open(feaPath, "w")
        f.write(fea)
        f.close()

        if clear:
            if "GSUB" in self.source:
                del self.source["GSUB"]
            if "GPOS" in self.source:
                del self.source["GPOS"]
        try:
            addOpenTypeFeatures(self.source, feaPath)
        except Exception:
            import traceback
            print(traceback.format_exc(5))
        finally:
            os.remove(feaPath)
            # XXX hacking into fontTools
            for tableName in ("GDEF", "GSUB", "GPOS"):
                if tableName in self.source:
                    table = self.source[tableName]
                    compiled = table.compile(self.source)
                    table.decompile(compiled, self.source)
            self.loadFeatures()

    def loadCMAP(self):
        self.cmap = {}
        self.reversedCMAP = {}
        for glyph in self.ufo:
            name = glyph.name
            uni = glyph.unicode
            if uni is None:
                continue
            self.cmap[uni] = name
            self.reversedCMAP[name] = uni

    def loadGlyphSet(self):
        self.glyphSet = self.ufo
        self._glyphOrder = {}
        for index, glyphName in enumerate(self.ufo.keys()):
            self._glyphOrder[glyphName] = index

    def loadInfo(self):
        self.info = info = compositor.Info()
        info.unitsPerEm = self.ufo.info.unitsPerEm
        info.ascender = self.ufo.info.ascender
        info.descender = self.ufo.info.descender
        info.xHeight = self.ufo.info.xHeight
        info.capHeight = self.ufo.info.capHeight
        info.familyName = self.ufo.info.familyName
        info.styleName = self.ufo.info.styleName
        self.stylisticSetNames = {}
