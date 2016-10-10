from lib.features.featureEditor import languagesIDEBehavior, FeatureLexer

from pygments.token import *
from pygments.lexers.python import PythonLexer


languagesIDEBehavior["FeaturePyFoFum"] = dict(languagesIDEBehavior["Feature"])


# lexer

class FeaPyFoFumLexer(FeatureLexer):

    name = "FeaturePyFoFum"
    aliases = ['featurePython', 'feaPy']
    filenames = ['*.feaPy']

    # make sure to make a copy
    tokens = dict(FeatureLexer.tokens)

    # make sure to make a copy
    tokens["root"] = list(FeatureLexer.tokens["root"])
    tokens["root"].insert(1, (r'# >>>', Name.Tag))
    tokens["root"].insert(2, (r'# <<<', Name.Tag))
    tokens["root"].insert(3, (r"# Traceback.*:\n", Error, "endtraceback"))

    tokens["endtraceback"] = [
            (r'# .*\n', Error),
        ]

    def get_tokens_unprocessed(self, text, stack=('root',)):
        pythonLexer = PythonLexer()

        pythonCode = {}
        feaCode = {}

        pythonBlock = None
        feaBlock = []

        location = 0
        pythonStartLocation = None
        feaStartLocation = 0

        for line in text.splitlines():
            l = line.strip()
            location += len(line) + 1
            if l == "# >>>":
                feaBlock.append(line)
                pythonStartLocation = location
                pythonBlock = []
            elif l == "# <<<" and pythonStartLocation:
                indent = len(line.split("#")[0])
                pythonCode[(pythonStartLocation, indent)] = "\n".join(pythonBlock)
                pythonStartLocation = None
                pythonBlock = None
                feaCode[feaStartLocation] = "\n".join(feaBlock)

                feaBlock = []
                feaBlock.append(line)
                feaStartLocation = location - len(line) - 1

            elif pythonBlock is not None:
                if "# " in line:
                    pythonBlock.append(line.split("# ")[1])
            else:
                feaBlock.append(line)

        feaCode[feaStartLocation] = "\n".join(feaBlock)

        for (location, indent), pythonText in pythonCode.items():
            pos = 0
            for line in pythonText.splitlines():
                yield location + pos + indent, Name.Tag, "#"
                pos += len(line) + 1
                pos += 2 + indent
            for pos, token, value in pythonLexer.get_tokens_unprocessed(pythonText):
                if value == "\n":
                    location += 2 + indent
                yield location + pos + indent + 2, token, value

        for location, feaText in feaCode.items():
            for pos, token, value in super(FeaPyFoFumLexer, self).get_tokens_unprocessed(feaText):
                yield location+pos, token, value
